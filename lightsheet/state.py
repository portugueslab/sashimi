import numpy as np
from queue import Empty
from typing import Optional
from lightparam.param_qt import ParametrizedQt
from lightparam import Param, ParameterTree
from lightsheet.hardware.laser import CoboltLaser, LaserSettings
from lightsheet.scanning import (
    Scanner,
    PlanarScanning,
    ZScanning,
    ZSynced,
    ZManual,
    XYScanning,
    ScanParameters,
    TriggeringParameters,
    ScanningState,
    ExperimentPrepareState,
)
from lightsheet.stytra_comm import StytraCom
from multiprocessing import Event
import json
from lightsheet.camera import CameraProcess, CamParameters, CameraMode, TriggerMode
from lightsheet.streaming_save import StackSaver, SavingParameters, SavingStatus
from pathlib import Path
from enum import Enum


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
        self.n_frames = Param(10_000, (1, 10_000_000), gui=False, loadable=False)
        self.chunk_size = Param(320, (1, 10_000))
        self.save_dir = Param(r"F:/Vilim", gui=False)
        self.experiment_duration = Param(0, (0, 100_000), gui=False)
        self.notification_email = Param("None")


class ScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/scanning_state"
        self.scanning_state = Param(
            "Paused", ["Paused", "Calibration", "Planar", "Volume"],
        )

scanning_to_global_state = dict(
    Paused=GlobalState.PAUSED,
    Calibration=GlobalState.PREVIEW,
    Planar=GlobalState.PLANAR_PREVIEW,
    Volume=GlobalState.VOLUME_PREVIEW
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
        self.n_planes = Param(10, (1, 100))
        self.i_freeze = Param(-1, (-1, 1000))
        self.n_skip_start = Param(0, (0, 20))
        self.n_skip_end = Param(0, (0, 20))


class CameraSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "camera/parameters"
        self.exposure = Param(60, (2, 1000), unit="ms")
        self.binning = Param("2x2", ["1x1", "2x2", "4x4"])
        self.subarray = Param([0, 0, 2048, 2048], gui=False)  # order of params here is [hpos, vpos, hsize, vsize,]


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
            (self.z_settings.piezo, self.z_settings.lateral, self.z_settings.frontal)
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


def convert_save_params(save_settings: SaveSettings, scanning_settings:ZRecordingSettings):
    n_planes = scanning_settings.n_planes - (scanning_settings.n_skip_start + scanning_settings.n_skip_end)
    framerate = scanning_settings.frequency * (n_planes)
    return SavingParameters(
        output_dir=Path(save_settings.save_dir),
        n_t=int(save_settings.n_frames),
        n_planes=n_planes,
        chunk_size=int(save_settings.chunk_size),
        notification_email=str(save_settings.notification_email),
        framerate=framerate
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
            i_freeze=z_setting.i_freeze,
            frequency=None,
        ),
    )


class State:
    def __init__(self):
        self.stop_event = Event()
        self.experiment_start_event = Event()
        self.experiment_state = ExperimentPrepareState.PREVIEW
        self.scanner = Scanner(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
        )
        self.status = ScanningSettings()

        self.laser = CoboltLaser()
        self.camera = CameraProcess(
            experiment_start_event=self.experiment_start_event,
            stop_event=self.stop_event,
        )

        self.camera_settings = CameraSettings()
        self.save_settings = SaveSettings()

        self.settings_tree = ParameterTree()

        self.global_state = GlobalState.PAUSED

        self.planar_setting = PlanarScanningSettings()
        self.laser_settings = LaserSettings()
        self.stytra_comm = StytraCom(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
        )

        self.save_status: Optional[SavingStatus] = None

        self.saver = StackSaver(self.stop_event, duration_queue=self.stytra_comm.duration_queue)

        self.single_plane_settings = SinglePlaneSettings()
        self.volume_setting = ZRecordingSettings()
        self.calibration = Calibration()

        for setting in [
            self.planar_setting,
            self.laser_settings,
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

        self.camera_settings.sig_param_changed.connect(self.send_camera_settings)
        self.save_settings.sig_param_changed.connect(self.send_scan_settings)

        self.camera.start()
        self.scanner.start()
        self.stytra_comm.start()
        self.saver.start()

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
        camera_params.trigger_mode = TriggerMode.FREE if self.global_state == GlobalState.PREVIEW else TriggerMode.EXTERNAL_TRIGGER
        if self.global_state == GlobalState.PAUSED:
            camera_params.camera_mode = CameraMode.PAUSED
        else:
            camera_params.camera_mode = CameraMode.PREVIEW

        self.camera.parameter_queue.put(camera_params)
        self.all_settings["camera"] = camera_params

    def send_scan_settings(self):
        if self.global_state == GlobalState.PAUSED:
            params = ScanParameters(state=ScanningState.PAUSED)

        elif self.global_state == GlobalState.PREVIEW:
            params = convert_calibration_params(
                self.planar_setting, self.calibration.z_settings
            )

        elif self.global_state == GlobalState.PLANAR_PREVIEW:
            params = convert_single_plane_params(
                self.planar_setting, self.single_plane_settings, self.calibration
            )

        elif self.global_state == GlobalState.VOLUME_PREVIEW:
            params = convert_volume_params(
                self.planar_setting, self.volume_setting, self.calibration
            )

        params.experiment_state = self.experiment_state

        self.all_settings["scanning"] = params

        self.scanner.parameter_queue.put(params)
        self.stytra_comm.current_settings_queue.put(self.all_settings)

        save_params = convert_save_params(
                self.save_settings, self.volume_setting)
        self.saver.saving_parameter_queue.put(save_params)

    def get_camera_status(self):
        try:
            current_camera_status = self.camera.camera_status_queue.get(timeout=0.001)
            return current_camera_status
        except Empty:
            return None

    def toggle_experiment_state(self):
        if self.experiment_state == ExperimentPrepareState.PREVIEW:
            self.experiment_state = ExperimentPrepareState.NO_TRIGGER
            self.prepare_experiment()

        elif self.experiment_state == ExperimentPrepareState.NO_TRIGGER:
            self.experiment_state = ExperimentPrepareState.EXPERIMENT_STARTED
            self.send_scan_settings()

        elif self.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
            self.experiment_state = ExperimentPrepareState.ABORT
            self.abort_experiment()
            self.experiment_state = ExperimentPrepareState.PREVIEW
            self.send_scan_settings()

    def prepare_experiment(self):
        # TODO disable the GUI
        self.send_scan_settings()
        self.saver.saving_signal.set()

    def abort_experiment(self):
        self.saver.saving_signal.clear()
        self.experiment_start_event.clear()
        self.send_scan_settings()

    def get_image(self):
        try:
            image = self.camera.image_queue.get(timeout=0.001)
            if self.saver.saving_signal.is_set():
                if (
                    self.save_status is not None
                    and self.save_status.i_in_chunk + 1 == self.save_status.target_params.n_t
                ):
                    self.wrap_up()
                if self.experiment_state == ExperimentPrepareState.EXPERIMENT_STARTED:
                    self.saver.save_queue.put(image)
            return image
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
        self.laser.close()
        self.scanner.join(timeout=10)
        self.saver.join(timeout=10)
        self.camera.join(timeout=10)
        self.stytra_comm.join(timeout=10)

