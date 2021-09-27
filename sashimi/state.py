import numpy as np
from multiprocessing import Manager as MultiprocessingManager
from queue import Empty
from typing import Optional, Tuple
from lightparam.param_qt import ParametrizedQt
from lightparam import Param, ParameterTree
from sashimi.hardware.light_source import light_source_class_dict

# from sashimi.hardware import light_source_class_dict
from sashimi.hardware.scanning.scanning_manager import (
    ScanningSettings,
    ScanningUseMode,
    ScanningManager,
)
from sashimi.hardware.scanning.scanloops import ExperimentPrepareState
from sashimi.processes.external_communication import ExternalComm
from sashimi.processes.dispatcher import VolumeDispatcher
from sashimi.processes.logging import ConcurrenceLogger
from multiprocessing import Event
import json
from sashimi.processes.camera import (
    CameraProcess,
    CamParameters,
    CameraMode,
    TriggerMode,
)
from sashimi.processes.streaming_save import StackSaver, SavingParameters, SavingStatus
from sashimi.events import LoggedEvent, SashimiEvents
from pathlib import Path
from sashimi.config import read_config
import time
from sashimi.utilities import clean_json, get_last_parameters

conf = read_config()


class SaveSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "experiment_settings"
        self.save_dir = Param(conf["default_paths"]["data"], gui=False)
        self.notification_email = Param("")
        self.overwrite_save_folder = Param(0, (0, 1), gui=False, loadable=False)


class TriggerSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.name = "trigger_settings"
        self.experiment_duration = Param(5, (1, 50_000), unit="s")
        self.is_triggered = Param(True, [True, False], gui=False)


scanning_to_global_state = dict(
    Paused=ScanningUseMode.PAUSED,
    Calibration=ScanningUseMode.PREVIEW,
    Planar=ScanningUseMode.PLANAR,
    Volume=ScanningUseMode.VOLUME,
)

roi_size = [0, 0] + [
    r // conf["camera"]["default_binning"]
    for r in conf["camera"]["max_sensor_resolution"]
]


class CameraSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "camera/parameters"
        self.exposure_time = Param(
            conf["camera"]["default_exposure"], (1, 1000), unit="ms"
        )
        self.binning = Param(conf["camera"]["default_binning"], [1, 2, 4])
        self.roi = Param(
            roi_size, gui=False
        )  # order of params here is [hpos, vpos, hsize, vsize,]; h: horizontal, v: vertical


class LightSourceSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/light_source"
        self.intensity = Param(0, (0, 40), unit=conf["light_source"]["intensity_units"])


def convert_save_params(
    save_settings: SaveSettings,
    volume_rate: float,
    n_planes: int,
    voxel_size: Tuple[float, float, float],
):

    return SavingParameters(
        output_dir=Path(save_settings.save_dir),
        n_planes=n_planes,
        notification_email=str(save_settings.notification_email),
        volumerate=volume_rate,
        voxel_size=voxel_size,
    )


class State:
    def __init__(self):
        self.conf = read_config()

        self.logger = ConcurrenceLogger("main")

        self.noise_image = None
        self.waveform = None
        self.stop_event = LoggedEvent(self.logger, SashimiEvents.CLOSE_ALL)
        self.experiment_start_event = LoggedEvent(
            self.logger, SashimiEvents.SEND_EXT_TRIGGER
        )
        self.noise_subtraction_active = LoggedEvent(
            self.logger, SashimiEvents.NOISE_SUBTRACTION_ACTIVE, Event()
        )
        self.is_saving_event = LoggedEvent(self.logger, SashimiEvents.IS_SAVING)

        self.experiment_state = ExperimentPrepareState.PREVIEW
        self.status = ScanningSettings()

        self.camera_settings = CameraSettings()
        self.trigger_settings = TriggerSettings()

        self.settings_tree = ParameterTree()

        self.pause_after = False
        if self.conf["scopeless"]:
            self.light_source = light_source_class_dict["mock"]()
        else:
            self.light_source = light_source_class_dict[conf["light_source"]["name"]](
                port=conf["light_source"]["port"]
            )

        self.scanning_manager = ScanningManager(
            self.conf["sample_rate"], self.stop_event, self.logger
        )

        self.camera = CameraProcess(
            stop_event=self.stop_event,
            wait_event=self.scanning_manager.is_waiting_event,
            exp_trigger_event=self.experiment_start_event,
        )

        self.multiprocessing_manager = MultiprocessingManager()

        self.experiment_duration_queue = self.multiprocessing_manager.Queue()

        self.external_comm = ExternalComm(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
            is_saving_event=self.is_saving_event,
            is_waiting_event=self.scanning_manager.is_waiting_event,
            duration_queue=self.experiment_duration_queue,
        )

        self.saver = StackSaver(
            stop_event=self.stop_event,
            is_saving_event=self.is_saving_event,
            duration_queue=self.experiment_duration_queue,
        )

        self.dispatcher = VolumeDispatcher(
            stop_event=self.stop_event,
            saving_signal=self.saver.saving_signal,
            wait_signal=self.scanning_manager.is_waiting_event,
            noise_subtraction_on=self.noise_subtraction_active,
            camera_queue=self.camera.image_queue,
            saver_queue=self.saver.save_queue,
        )

        self.camera_settings = CameraSettings()
        self.save_settings = SaveSettings()

        self.settings_tree = ParameterTree()

        self.global_state = ScanningUseMode.PAUSED

        self.light_source_settings = LightSourceSettings()
        self.light_source_settings.params.intensity.unit = (
            self.light_source.intensity_units
        )

        self.save_status: Optional[SavingStatus] = None

        for setting in [
            self.light_source_settings,
            self.camera_settings,
            self.save_settings,
        ] + self.scanning_manager.all_settings:
            self.settings_tree.add(setting)

        self.scanning_manager.scanning_changed.connect(self.send_imaging_settings)
        self.status.sig_param_changed.connect(self.change_global_state)
        self.save_settings.sig_param_changed.connect(self.send_imaging_settings)

        self.camera.start()
        self.external_comm.start()
        self.saver.start()
        self.dispatcher.start()
        self.scanning_manager.start()

        self.send_imaging_settings()
        self.logger.log_message("initialized")

    def restore_tree(self, restore_file):
        with open(restore_file, "r") as f:
            self.settings_tree.deserialize(json.load(f))

    def save_tree(self, save_file):
        with open(save_file, "w") as f:
            json.dump(clean_json(self.settings_tree.serialize()), f)

    def change_global_state(self):
        self.global_state = scanning_to_global_state[self.status.scanning_state]
        self.send_camera_settings()
        self.send_imaging_settings()

    def send_camera_settings(self):
        camera_params = CamParameters(
            exposure_time=self.camera_settings.exposure_time,
            binning=int(self.camera_settings.binning),
            roi=tuple(self.camera_settings.roi),
        )

        camera_params.trigger_mode = (
            TriggerMode.FREE
            if self.global_state == ScanningUseMode.PREVIEW
            or self.global_state == ScanningUseMode.PLANAR
            else TriggerMode.EXTERNAL_TRIGGER
        )
        if self.global_state == ScanningUseMode.PAUSED:
            camera_params.camera_mode = CameraMode.PAUSED
        else:
            camera_params.camera_mode = CameraMode.PREVIEW

        self.camera.image_queue.clear()
        self.camera.parameter_queue.put(self.camera_params)

    def send_scan_settings(self, param_changed=None):
        # Restart scanning loop if scanning params have changed:
        self.send_imaging_settings()

    @property
    def voxel_size(self):
        binning = int(self.camera_settings.binning)

        return (
            self.scanning_manager.interplane_distance,
            conf["voxel_size"]["y"] * binning,
            conf["voxel_size"]["x"] * binning,
        )

    @property
    def is_volumetric(self):
        return self.scanning_manager.scanning_mode == ScanningUseMode.VOLUME

    @property
    def n_planes(self):
        return self.scanning_manager.n_planes

    @property
    def volume_rate(self):
        # TODO calculate this from the camera for
        # free running or no-scanner mode
        return self.scanning_manager.volume_rate

    @property
    def save_params(self):
        return convert_save_params(
            self.save_settings, self.volume_rate, self.n_planes, self.voxel_size,
        )

    @property
    def camera_params(self):
        camera_params = CamParameters(
            exposure_time=self.camera_settings.exposure_time,
            binning=int(self.camera_settings.binning),
            roi=tuple(self.camera_settings.roi),
        )

        camera_params.trigger_mode = (
            TriggerMode.FREE
            if self.global_state == ScanningUseMode.PREVIEW
            or self.global_state == ScanningUseMode.PLANAR
            else TriggerMode.EXTERNAL_TRIGGER
        )
        if self.global_state == ScanningUseMode.PAUSED:
            camera_params.camera_mode = CameraMode.PAUSED
        else:
            camera_params.camera_mode = CameraMode.PREVIEW

        return camera_params

    @property
    def all_settings(self):
        all_settings = dict(
            scanning=self.scanning_manager.last_params, camera=self.camera_params
        )

        if self.scanning_manager.waveform is not None:
            all_settings[
                "scanning"
            ] = self.scanning_manager.piezo_values_at_trigger_times()

        return all_settings

    @property
    def pulse_times(self):
        return self.scanning_manager.calculate_pulse_times()

    def send_imaging_settings(self):
        self.external_comm.current_settings_queue.put(self.all_settings)
        self.saver.saving_parameter_queue.put(self.save_params)
        self.dispatcher.n_planes_queue.put(self.n_planes)

    def start_experiment(self):
        # TODO disable the GUI except the abort button
        self.logger.log_message("started experiment")
        self.scanning_manager.prepare_experiment()
        self.send_imaging_settings()
        self.scanning_manager.restart_event.set()
        self.saver.save_queue.empty()
        self.camera.image_queue.empty()
        time.sleep(0.01)
        self.is_saving_event.set()

    def end_experiment(self):
        self.logger.log_message("experiment ended")
        self.is_saving_event.clear()
        self.experiment_start_event.clear()
        self.saver.save_queue.clear()
        self.send_imaging_settings()

    def obtain_noise_average(self, n_images=50):
        """Obtains average noise of n_images to subtract to acquired,
        both for display and saving.

        Parameters
        ----------
        n_images : int
            Number of frames to average.

        """
        self.noise_subtraction_active.clear()

        light_intensity = self.light_source_settings.intensity
        self.light_source.intensity = 0
        n_image = 0
        while n_image < n_images:
            current_volume = self.get_volume()
            if current_volume is not None:
                current_image = current_volume[0, :, :]
                if n_image == 0:
                    calibration_set = np.empty(
                        shape=(n_images, *current_image.shape),
                        dtype=current_volume.dtype,
                    )
                calibration_set[n_image, :, :] = current_image
                n_image += 1

        self.noise_subtraction_active.set()
        self.noise_image = np.mean(calibration_set, axis=0).astype(
            dtype=current_volume.dtype
        )
        self.light_source.intensity = light_intensity

        self.dispatcher.noise_image_queue.put(self.noise_image)

    def reset_noise_subtraction(self):
        self.noise_image = None
        self.noise_subtraction_active.clear()

    def get_volume(self):
        # TODO consider get_last_parameters method
        try:
            return self.dispatcher.viewer_queue.get(timeout=0.001)
        except Empty:
            return None

    def get_save_status(self) -> Optional[SavingStatus]:
        return get_last_parameters(self.saver.saved_status_queue)

    def get_triggered_frame_rate(self):
        return get_last_parameters(self.camera.triggered_frame_rate_queue)

    def get_waveform(self):
        return self.scanning_manager.get_waveform()

    def set_trigger_mode(self, mode: bool):
        if mode:
            self.external_comm.is_triggered_event.set()
        else:
            self.external_comm.is_triggered_event.clear()

    def send_manual_duration(self):
        self.experiment_duration_queue.put(self.trigger_settings.experiment_duration)

    def wrap_up(self):
        self.stop_event.set()
        self.light_source.close()

        self.scanning_manager.wrap_up()
        self.saver.join(timeout=10)
        self.camera.join(timeout=10)
        self.external_comm.join(timeout=10)
        self.dispatcher.join(timeout=10)
        self.logger.close()
