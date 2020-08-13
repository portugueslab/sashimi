import numpy as np
from queue import Empty
from typing import Optional
from lightparam.param_qt import ParametrizedQt
from lightparam import Param, ParameterTree
from shirashi.scanning import (
    Scanner,
    ScanParameters,
    TriggeringParameters,
    ScanningState,
    ExperimentPrepareState,
)
from shirashi.stytra_comm import StytraCom
from shirashi.dispatcher import VolumeDispatcher
from multiprocessing import Event
import json
from shirashi.camera import (
    CameraProcess,
    CamParameters,
    CameraMode,
    TriggerMode,
    MockCameraProcess,
)
from shirashi.streaming_save import StackSaver, SavingParameters, SavingStatus
from pathlib import Path
from enum import Enum
import time
from shirashi.config import read_config

conf = read_config()


class GlobalState(Enum):
    PAUSED = 0
    PREVIEW = 1
    TBD_PREVIEW = 2
    EXP_PREVIEW = 3
    EXPERIMENT_RUNNING = 4


class ScopeAlignmentInfo(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "scope_alignment_info"
        self.waist_width = Param(6.5, (0.1, 100), unit="um")
        self.pixel_size_x = Param(0.3, (0.1, 10), unit="um (at binning 1x1)")
        self.pixel_size_y = Param(0.3, (0.1, 10), unit="um (at binning 1x1)")


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
            "Paused", ["Paused", "Preview", "TBD", "Experiment"],
        )


scanning_to_global_state = dict(
    Paused=GlobalState.PAUSED,
    Preview=GlobalState.PREVIEW,
    TBD=GlobalState.TBD_PREVIEW,
    Experiment=GlobalState.EXP_PREVIEW,
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


class CameraSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "camera/parameters"
        self.exposure = Param(60, (2, 1000), unit="ms")
        self.binning = Param("1x1", ["1x1", "2x2", "4x4"])
        self.subarray = Param(
            [0, 0, 2048, 2048], gui=False
        )  # order of params here is [hpos, vpos, hsize, vsize,]



class Preview(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/preview"
        self.z_settings = CalibrationZSettings()
        self.calibrations_points = []
        self.calibration = Param([(0, 0.01), (0, 0.01)], gui=False)

    def add_calibration_point(self):
        self.calibrations_points.append(
            (self.z_settings.piezo, self.z_settings.lateral, self.z_settings.frontal,)
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
        subarray=tuple(camera_settings.subarray),
    )


def get_voxel_size(
    camera_settings: CameraSettings,
    scope_alignment: ScopeAlignmentInfo,
):
    if camera_settings.binning == "1x1":
        binning = 1
    elif camera_settings.binning == "2x2":
        binning = 2
    elif camera_settings.binning == "4x4":
        binning = 4
        # set binning 2x2 by default
    else:
        binning = 2


    return (
        scope_alignment.pixel_size_y * binning,
        scope_alignment.pixel_size_x * binning,
    )


def convert_save_params(
    save_settings: SaveSettings,
    camera_settings: CameraSettings,
    scope_alignment: ScopeAlignmentInfo,
):
    return SavingParameters(
        output_dir=Path(save_settings.save_dir),
        n_planes= 10, #todo change
        notification_email=str(save_settings.notification_email),
        voxel_size=get_voxel_size(camera_settings, scope_alignment),
    )




class State:
    def __init__(self, sample_rate):
        self.conf = read_config()
        self.sample_rate = sample_rate
        self.calibration_ref = None
        self.waveform = None
        self.stop_event = Event()
        self.experiment_start_event = Event()
        self.experiment_state = ExperimentPrepareState.PREVIEW
        self.status = ScanningSettings()
        self.scope_alignment_info = ScopeAlignmentInfo()
        if self.conf["scopeless"]:
            self.laser = MockCoboltLaser()
            self.camera = MockCameraProcess(
                experiment_start_event=self.experiment_start_event,
                stop_event=self.stop_event,
            )
        else:
            self.camera = CameraProcess(
                experiment_start_event=self.experiment_start_event,
                stop_event=self.stop_event,
            )

        self.scanner = Scanner(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
            sample_rate=self.sample_rate,
        )
        self.camera_settings = CameraSettings()
        self.save_settings = SaveSettings()

        self.settings_tree = ParameterTree()

        self.global_state = GlobalState.PAUSED
        self.pause_after = False

        self.planar_setting = PlanarScanningSettings()
        self.stytra_comm = StytraCom(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
        )

        self.save_status: Optional[SavingStatus] = None

        self.saver = StackSaver(
            stop_event=self.stop_event, duration_queue=self.stytra_comm.duration_queue,
        )

        self.dispatcher = VolumeDispatcher(
            stop_event=self.stop_event,
            saving_signal=self.saver.saving_signal,
            wait_signal=self.scanner.wait_signal,
            camera_queue=self.camera.image_queue,
            saver_queue=self.saver.save_queue,
        )

        self.preview = Preview()

        for setting in [
            self.planar_setting,
            self.preview,
            self.preview.z_settings,
            self.camera_settings,
            self.save_settings,
            self.scope_alignment_info,
        ]:
            self.settings_tree.add(setting)

        self.status.sig_param_changed.connect(self.change_global_state)

        self.planar_setting.sig_param_changed.connect(self.send_scan_settings)
        self.preview.z_settings.sig_param_changed.connect(self.send_scan_settings)

        self.camera_settings.sig_param_changed.connect(self.send_camera_settings)
        self.save_settings.sig_param_changed.connect(self.send_scan_settings)
        #
        # self.volume_setting.sig_param_changed.connect(self.send_dispatcher_settings)
        # self.single_plane_settings.sig_param_changed.connect(
        #     self.send_dispatcher_settings
        # )
        self.status.sig_param_changed.connect(self.send_dispatcher_settings)

        self.camera.start()
        self.scanner.start()
        self.stytra_comm.start()
        self.saver.start()
        self.dispatcher.start()

        self.all_settings = dict(camera=dict(), scanning=dict())

        self.current_camera_status = CamParameters()
        self.send_scan_settings()

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
        params = ScanParameters(state=ScanningState.PAUSED)
        if self.global_state == GlobalState.PAUSED:
            params = ScanParameters(state=ScanningState.PAUSED)

        elif self.global_state == GlobalState.PREVIEW:
            pass
            # params = convert_calibration_params(
            #     self.planar_setting, self.preview.z_settings
            # )

        elif self.global_state == GlobalState.TBD_PREVIEW:
            pass
            # params = convert_single_plane_params(
            #     self.planar_setting, self.single_plane_settings, self.preview,
            # )

        elif self.global_state == GlobalState.EXP_PREVIEW:
            pass
        # params = convert_volume_params(
            #     self.planar_setting, self.volume_setting, self.preview
            # )


        params.experiment_state = self.experiment_state
        self.all_settings["scanning"] = params

        self.scanner.parameter_queue.put(params)
        self.stytra_comm.current_settings_queue.put(self.all_settings)

        save_params = convert_save_params(
            self.save_settings,
            self.camera_settings,
            self.scope_alignment_info,
        )
        self.saver.saving_parameter_queue.put(save_params)
        self.dispatcher.n_planes_queue.put(n_planes)

    def send_dispatcher_settings(self):
        pass

    def get_camera_status(self):
        try:
            current_camera_status = self.camera.camera_status_queue.get(timeout=0.001)
            return current_camera_status
        except Empty:
            return None

    def toggle_experiment_state(self):
        if self.experiment_state == ExperimentPrepareState.PREVIEW:
            self.experiment_state = ExperimentPrepareState.NO_TRIGGER
            self.start_experiment()

        elif self.experiment_state == ExperimentPrepareState.NO_TRIGGER:
            self.experiment_state = ExperimentPrepareState.EXPERIMENT_STARTED
            self.send_scan_settings()

        elif self.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
            self.experiment_state = ExperimentPrepareState.PREVIEW
            self.end_experiment()

    def start_experiment(self):
        # TODO disable the GUI except the abort button
        self.send_scan_settings()
        self.saver.save_queue.empty()
        self.camera.image_queue.empty()
        self.saver.saving_signal.set()
        time.sleep(0.5)
        self.toggle_experiment_state()

    def end_experiment(self):
        self.saver.saving_signal.clear()
        self.experiment_start_event.clear()
        self.saver.save_queue.clear()
        self.send_scan_settings()

    def obtain_noise_average(self, n_images=50, dtype=np.uint16):
        """
        Obtains average noise of n_images to subtract to acquired, both for display and saving
        """
        self.dispatcher.noise_subtraction_active.clear()

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
        self.dispatcher.noise_subtraction_active.set()
        self.calibration_ref = np.mean(calibration_set, axis=0).astype(dtype=dtype)
        self.laser.set_current(current_laser)

        self.dispatcher.calibration_ref_queue.put(self.calibration_ref)

    def reset_noise_subtraction(self):
        self.calibration_ref = None
        self.dispatcher.noise_subtraction_active.clear()

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

    def wrap_up(self):
        self.stop_event.set()
        self.scanner.join(timeout=10)
        self.saver.join(timeout=10)
        self.camera.join(timeout=10)
        self.stytra_comm.join(timeout=10)
        self.dispatcher.join(timeout=10)
