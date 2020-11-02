import numpy as np
from queue import Empty
from typing import Optional
from lightparam.param_qt import ParametrizedQt
from lightparam import Param, ParameterTree
from sashimi.hardware.light_source import light_source_class_dict
from sashimi.processes.scanning import Scanner
from sashimi.hardware.scanning.scanloops import (
    ScanningState,
    ExperimentPrepareState,
    XYScanning,
    PlanarScanning,
    ZManual,
    ZSynced,
    ZScanning,
    TriggeringParameters,
    ScanParameters,
)
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
from enum import Enum
from sashimi.config import read_config

conf = read_config()


class GlobalState(Enum):
    PAUSED = 0
    PREVIEW = 1
    PLANAR_PREVIEW = 2
    VOLUME_PREVIEW = 3
    EXPERIMENT_RUNNING = 4

class SaveSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "experiment_settings"
        self.save_dir = Param(conf["default_paths"]["data"], gui=False)
        self.experiment_duration = Param(0, (0, 100_000), gui=False)
        self.notification_email = Param("")
        self.overwrite_save_folder = Param(0, (0, 1), gui=False, loadable=False)


class ScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/scanning_state"
        self.scanning_state = Param(
            "Paused",
            ["Paused", "Calibration", "Planar", "Volume"],
        )


scanning_to_global_state = dict(
    Paused=GlobalState.PAUSED,
    Calibration=GlobalState.PREVIEW,
    Planar=GlobalState.PLANAR_PREVIEW,
    Volume=GlobalState.VOLUME_PREVIEW,
)


class PlanarScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "scanning/planar_scanning"
        self.lateral_range = Param((0, 0.5), (-2, 2))
        self.lateral_frequency = Param(500.0, (10, 1000), unit="Hz")
        self.frontal_range = Param((0, 0.5), (-2, 2))
        self.frontal_frequency = Param(500.0, (10, 1000), unit="Hz")


class CalibrationZSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "scanning/z_manual"
        self.piezo = Param(200.0, (0.0, 400.0), unit="um", gui="slider")
        self.lateral = Param(0.0, (-2.0, 2.0), gui="slider")
        self.frontal = Param(0.0, (-2.0, 2.0), gui="slider")


class SinglePlaneSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "scanning/z_single_plane"
        self.piezo = Param(200.0, (0.0, 400.0), unit="um", gui="slider")
        self.frequency = Param(1.0, (0.1, 1000), unit="planes/s (Hz)")


class ZRecordingSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.name = "scanning/volumetric_recording"
        self.scan_range = Param((0.0, 100.0), (0.0, 400.0), unit="um")
        self.frequency = Param(1.0, (0.1, 100), unit="volumes/s (Hz)")
        self.n_planes = Param(10, (2, 100))
        self.n_skip_start = Param(0, (0, 20))
        self.n_skip_end = Param(0, (0, 20))


class CameraSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "camera/parameters"
        self.exposure = Param(60, (2, 1000), unit="ms")
        self.binning = Param("2x2", ["1x1", "2x2", "4x4"])
        self.roi = Param(
            [0, 0, 1024, 1024], gui=False
        )  # order of params here is [hpos, vpos, hsize, vsize,]; h: horizontal, v: vertical



class LightSourceSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/light_source"
        self.intensity = Param(0, (0, 40), unit=conf["light_source"]["intensity_units"])


def convert_planar_params(planar: PlanarScanningSettings):
    return PlanarScanning(
        lateral=XYScanning(
            vmin=planar.lateral_range[0],
            vmax=planar.lateral_range[1],
            frequency=planar.lateral_frequency,
        ),
        frontal=XYScanning(
            vmin=planar.frontal_range[0],
            vmax=planar.frontal_range[1],
            frequency=planar.frontal_frequency,
        ),
    )


def convert_calibration_params(
    planar: PlanarScanningSettings, zsettings: CalibrationZSettings
):
    sp = ScanParameters(
        state=ScanningState.PLANAR,
        xy=convert_planar_params(planar),
        z=ZManual(**zsettings.params.values),
    )
    return sp


class Calibration(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/calibration"
        self.z_settings = CalibrationZSettings()
        self.calibrations_points = []
        self.calibration = Param([(0, 0.01), (0, 0.01)], gui=False)

    def add_calibration_point(self):
        self.calibrations_points.append(
            (
                self.z_settings.piezo,
                self.z_settings.lateral,
                self.z_settings.frontal,
            )
        )
        self.calculate_calibration()

    def remove_calibration_point(self):
        if len(self.calibrations_points) > 0:
            self.calibrations_points.pop()
            self.calculate_calibration()

    def calculate_calibration(self):
        if len(self.calibrations_points) < 2:
            self.calibration = None
            return False

        calibration_data = np.array(self.calibrations_points)
        piezo_val = np.pad(
            calibration_data[:, 0:1],
            ((0, 0), (1, 0)),
            constant_values=1.0,
            mode="constant",
        )
        lateral_val = calibration_data[:, 1]
        frontal_val = calibration_data[:, 2]

        # solve least squares according to standard formula b = (XtX)^-1 * Xt * y
        piezo_cor = np.linalg.pinv(piezo_val.T @ piezo_val)

        self.calibration = [
            tuple(piezo_cor @ piezo_val.T @ galvo)
            for galvo in [lateral_val, frontal_val]
        ]

        return True


def convert_camera_params(camera_settings: CameraSettings):
    if camera_settings.binning == "1x1":
        binning = 1
    elif camera_settings.binning == "2x2":
        binning = 2
    elif camera_settings.binning == "4x4":
        binning = 4
    # set binning 2x2 by default
    else:
        binning = 2

    return CamParameters(
        exposure_time=camera_settings.exposure,
        binning=binning,
        roi=tuple(camera_settings.roi),
    )


def get_voxel_size(
    scanning_settings: ZRecordingSettings,
    camera_settings: CameraSettings,
):
    scan_length = scanning_settings.scan_range[1] - scanning_settings.scan_range[0]

    if camera_settings.binning == "1x1":
        binning = 1
    elif camera_settings.binning == "2x2":
        binning = 2
    elif camera_settings.binning == "4x4":
        binning = 4
        # set binning 2x2 by default
    else:
        binning = 2

    inter_plane = scan_length / scanning_settings.n_planes

    return (
        inter_plane,
        conf["voxel_size"]["y"] * binning,
        conf["voxel_size"]["x"] * binning,
    )


def convert_save_params(
    save_settings: SaveSettings,
    scanning_settings: ZRecordingSettings,
    camera_settings: CameraSettings,
):
    n_planes = scanning_settings.n_planes - (
        scanning_settings.n_skip_start + scanning_settings.n_skip_end
    )

    return SavingParameters(
        output_dir=Path(save_settings.save_dir),
        n_planes=n_planes,
        notification_email=str(save_settings.notification_email),
        volumerate=scanning_settings.frequency,
        voxel_size=get_voxel_size(scanning_settings, camera_settings),
    )


def convert_single_plane_params(
    planar: PlanarScanningSettings,
    single_plane_setting: SinglePlaneSettings,
    calibration: Calibration,
):
    return ScanParameters(
        state=ScanningState.PLANAR,
        xy=convert_planar_params(planar),
        z=ZSynced(
            piezo=single_plane_setting.piezo,
            lateral_sync=tuple(calibration.calibration[0]),
            frontal_sync=tuple(calibration.calibration[1]),
        ),
        triggering=TriggeringParameters(frequency=single_plane_setting.frequency),
    )


def convert_volume_params(
    planar: PlanarScanningSettings,
    z_setting: ZRecordingSettings,
    calibration: Calibration,
):
    return ScanParameters(
        state=ScanningState.VOLUMETRIC,
        xy=convert_planar_params(planar),
        z=ZScanning(
            piezo_min=z_setting.scan_range[0],
            piezo_max=z_setting.scan_range[1],
            frequency=z_setting.frequency,
            lateral_sync=tuple(calibration.calibration[0]),
            frontal_sync=tuple(calibration.calibration[1]),
        ),
        triggering=TriggeringParameters(
            n_planes=z_setting.n_planes,
            n_skip_start=z_setting.n_skip_start,
            n_skip_end=z_setting.n_skip_end,
            frequency=None,
        ),
    )


class State:
    def __init__(self):
        self.conf = read_config()
        self.sample_rate = conf["sample_rate"]

        self.logger = ConcurrenceLogger("main")

        self.calibration_ref = None
        self.waveform = None
        self.stop_event = LoggedEvent(self.logger, SashimiEvents.CLOSE_ALL)
        self.restart_event = LoggedEvent(self.logger, SashimiEvents.RESTART_SCANNING)
        self.experiment_start_event = LoggedEvent(
            self.logger, SashimiEvents.SEND_EXT_TRIGGER
        )
        self.noise_subtraction_active = LoggedEvent(
            self.logger, SashimiEvents.NOISE_SUBTRACTION_ACTIVE, Event()
        )
        self.is_saving_event = LoggedEvent(self.logger, SashimiEvents.IS_SAVING)
        self.is_waiting_event = LoggedEvent(
            self.logger, SashimiEvents.WAITING_FOR_TRIGGER
        )

        self.experiment_state = ExperimentPrepareState.PREVIEW
        self.status = ScanningSettings()

        self.scanner = Scanner(
            stop_event=self.stop_event,
            restart_event=self.restart_event,
            waiting_event=self.is_waiting_event,
            sample_rate=self.sample_rate,
        )
        self.camera_settings = CameraSettings()
        self.save_settings = SaveSettings()

        self.settings_tree = ParameterTree()

        self.global_state = GlobalState.PAUSED
        self.pause_after = False
        if self.conf["scopeless"]:
            self.light_source = light_source_class_dict["mock"]()
        else:
            self.light_source = light_source_class_dict[conf["light_source"]["name"]](
                port=conf["light_source"]["port"]
            )
        self.camera = CameraProcess(
            stop_event=self.stop_event,
            wait_event=self.scanner.wait_signal,
            exp_trigger_event=self.experiment_start_event,
        )
        self.planar_setting = PlanarScanningSettings()
        self.external_comm = ExternalComm(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
            is_saving_event=self.is_saving_event,
            is_waiting_event=self.is_waiting_event,
        )

        self.saver = StackSaver(
            stop_event=self.stop_event,
            is_saving_event=self.is_saving_event,
            duration_queue=self.external_comm.duration_queue,
        )

        self.dispatcher = VolumeDispatcher(
            stop_event=self.stop_event,
            saving_signal=self.saver.saving_signal,
            wait_signal=self.scanner.wait_signal,
            noise_subtraction_on=self.noise_subtraction_active,
            camera_queue=self.camera.image_queue,
            saver_queue=self.saver.save_queue,
        )

        self.camera_settings = CameraSettings()
        self.save_settings = SaveSettings()

        self.settings_tree = ParameterTree()

        self.global_state = GlobalState.PAUSED
        self.pause_after = False

        self.planar_setting = PlanarScanningSettings()
        self.light_source_settings = LightSourceSettings()

        self.save_status: Optional[SavingStatus] = None

        self.single_plane_settings = SinglePlaneSettings()
        self.volume_setting = ZRecordingSettings()
        self.calibration = Calibration()

        for setting in [
            self.planar_setting,
            self.light_source_settings,
            self.single_plane_settings,
            self.volume_setting,
            self.calibration,
            self.calibration.z_settings,
            self.camera_settings,
            self.save_settings,
        ]:
            self.settings_tree.add(setting)

        self.status.sig_param_changed.connect(self.change_global_state)

        self.planar_setting.sig_param_changed.connect(self.send_scan_settings)
        self.calibration.z_settings.sig_param_changed.connect(self.send_scan_settings)
        self.single_plane_settings.sig_param_changed.connect(self.send_scan_settings)
        self.volume_setting.sig_param_changed.connect(self.send_scan_settings)

        # self.camera_settings.sig_param_changed.connect(self.send_camera_settings)
        self.save_settings.sig_param_changed.connect(self.send_scan_settings)

        self.volume_setting.sig_param_changed.connect(self.send_dispatcher_settings)
        self.single_plane_settings.sig_param_changed.connect(
            self.send_dispatcher_settings
        )
        self.status.sig_param_changed.connect(self.send_dispatcher_settings)

        self.camera.start()
        self.scanner.start()
        self.external_comm.start()
        self.saver.start()
        self.dispatcher.start()

        self.all_settings = dict(camera=dict(), scanning=dict())

        self.current_binning = 2  # TODO avoid hardcoding
        self.send_scan_settings()
        self.logger.log_message("initialized")

        self.voxel_size = None

    def restore_tree(self, restore_file):
        with open(restore_file, "r") as f:
            self.settings_tree.deserialize(json.load(f))

    def save_tree(self, save_file):
        with open(save_file, "w") as f:
            json.dump(self.settings_tree.serialize(), f)

    def change_global_state(self):
        self.global_state = scanning_to_global_state[self.status.scanning_state]
        self.send_camera_settings()
        self.send_scan_settings()

    def send_camera_settings(self):
        camera_params = convert_camera_params(self.camera_settings)

        camera_params.trigger_mode = (
            TriggerMode.FREE
            if self.global_state == GlobalState.PREVIEW
            else TriggerMode.EXTERNAL_TRIGGER
        )
        if self.global_state == GlobalState.PAUSED:
            camera_params.camera_mode = CameraMode.PAUSED
        else:
            camera_params.camera_mode = CameraMode.PREVIEW

        self.camera.image_queue.clear()
        self.camera.parameter_queue.put(camera_params)
        self.all_settings["camera"] = camera_params

    def send_scan_settings(self):
        n_planes = 1
        if self.global_state == GlobalState.PAUSED:
            params = ScanParameters(state=ScanningState.PAUSED)

        elif self.global_state == GlobalState.PREVIEW:
            params = convert_calibration_params(
                self.planar_setting, self.calibration.z_settings
            )

        elif self.global_state == GlobalState.PLANAR_PREVIEW:
            params = convert_single_plane_params(
                self.planar_setting,
                self.single_plane_settings,
                self.calibration,
            )

        elif self.global_state == GlobalState.VOLUME_PREVIEW:
            params = convert_volume_params(
                self.planar_setting, self.volume_setting, self.calibration
            )
            n_planes = (
                self.volume_setting.n_planes
                - self.volume_setting.n_skip_start
                - self.volume_setting.n_skip_end
            )
            if self.waveform is not None:
                pulses = self.calculate_pulse_times() * self.sample_rate
                try:
                    pulse_log = self.waveform[pulses.astype(int)]
                    self.all_settings["piezo_log"] = {"trigger": pulse_log.tolist()}
                except IndexError:
                    pass

        params.experiment_state = self.experiment_state
        self.all_settings["scanning"] = params

        self.scanner.parameter_queue.put(params)
        self.external_comm.current_settings_queue.put(self.all_settings)

        save_params = convert_save_params(
            self.save_settings,
            self.volume_setting,
            self.camera_settings,
        )
        self.voxel_size = get_voxel_size(self.volume_setting, self.camera_settings)
        self.saver.saving_parameter_queue.put(save_params)
        self.dispatcher.n_planes_queue.put(n_planes)

    def send_dispatcher_settings(self):
        pass

    def start_experiment(self):
        # TODO disable the GUI except the abort button
        self.logger.log_message("started experiment")
        self.send_scan_settings()
        self.scanner.wait_signal.set()
        self.restart_event.set()
        self.saver.save_queue.empty()
        self.camera.image_queue.empty()
        self.is_saving_event.set()

    def end_experiment(self):
        self.logger.log_message("experiment ended")
        self.is_saving_event.clear()
        self.experiment_start_event.clear()
        self.saver.save_queue.clear()
        self.send_scan_settings()

    def obtain_noise_average(self, n_images=50, dtype=np.uint16):
        """
        Obtains average noise of n_images to subtract to acquired, both for display and saving
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
                        shape=(n_images, *current_image.shape), dtype=dtype
                    )
                calibration_set[n_image, :, :] = current_image
                n_image += 1
        self.noise_subtraction_active.set()
        self.calibration_ref = np.mean(calibration_set, axis=0).astype(dtype=dtype)
        self.light_source.intensity = light_intensity

        self.dispatcher.calibration_ref_queue.put(self.calibration_ref)

    def reset_noise_subtraction(self):
        self.calibration_ref = None
        self.noise_subtraction_active.clear()

    def get_frame_size(self):
        return [
            self.camera_settings.roi[2] - self.camera_settings.roi[0],
            self.camera_settings.roi[3] - self.camera_settings.roi[1]
        ]

    def get_volume(self):
        try:
            return self.dispatcher.viewer_queue.get(timeout=0.001)
        except Empty:
            return None

    def get_save_status(self) -> Optional[SavingStatus]:
        try:
            return self.saver.saved_status_queue.get(timeout=0.001)
        except Empty:
            return None

    def get_triggered_frame_rate(self):
        try:
            return self.camera.triggered_frame_rate_queue.get(timeout=0.001)
        except Empty:
            return None

    def get_waveform(self):
        try:
            self.waveform = self.scanner.waveform_queue.get(timeout=0.001)
            return self.waveform
        except Empty:
            return None

    def calculate_pulse_times(self):
        return (
            np.arange(
                self.volume_setting.n_skip_start,
                self.volume_setting.n_planes - self.volume_setting.n_skip_end,
            )
            / (self.volume_setting.frequency * self.volume_setting.n_planes)
        )

    def wrap_up(self):
        self.stop_event.set()
        self.light_source.close()

        self.scanner.join(timeout=10)
        self.saver.join(timeout=10)
        self.camera.join(timeout=10)
        self.external_comm.join(timeout=10)
        self.dispatcher.join(timeout=10)
        self.logger.close()
