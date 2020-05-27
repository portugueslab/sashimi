import numpy as np
from arrayqueues.shared_arrays import ArrayQueue
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
from lightsheet.camera import CameraProcess, CamParameters
from lightsheet.streaming_save import StackSaver, SavingParameters, SavingStatus


class ScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "general/scanning_state"
        self.scanning_state = Param(
            "Paused", ["Paused", "Calibration", "Planar", "Volume"],
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
        self.piezo = Param(0.0, (0.0, 400.0), unit="um", gui="slider")
        self.lateral = Param(0.0, (-2.0, 2.0), gui="slider")
        self.frontal = Param(0.0, (-2.0, 2.0), gui="slider")


class SinglePlaneSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "scanning/z_single_plane"
        self.piezo = Param(0.0, (0.0, 400.0), unit="um", gui="slider")
        self.frequency = Param(1.0, (0.1, 100), unit="Hz")


class ZRecordingSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.name = "scanning/volumetric_recording"
        self.scan_range = Param((0.0, 100.0), (0.0, 400.0), unit="um")
        self.frequency = Param(1.0, (0.1, 100), unit="Hz")
        self.n_planes = Param(10, (1, 100))
        self.i_freeze = Param(-1, (-1, 1000))
        self.n_skip_start = Param(0, (0, 20))
        self.n_skip_end = Param(0, (0, 20))


class CameraSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "camera/parameters"
        self.exposure = Param(60, (2, 1000), unit="ms")
        self.binning = Param("1x1", ["1x1", "2x2", "4x4"])


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
            calibration_data[:, 0:1], ((0, 0), (1, 0)), constant_values=1.0, mode="constant"
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


def convert_single_plane_params(
        planar: PlanarScanningSettings, single_plane_setting: SinglePlaneSettings, calibration: Calibration
):
    return ScanParameters(
        state=ScanningState.PLANAR,
        xy=convert_planar_params(planar),
        z=ZSynced(
            piezo=single_plane_setting.piezo,
            lateral_sync=tuple(calibration.calibration[0]),
            frontal_sync=tuple(calibration.calibration[1]),
        ),
        triggering=TriggeringParameters(frequency=single_plane_setting.frequency)
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
        self.experiment_state = ExperimentPrepareState.NORMAL
        self.scanner = Scanner(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
        )
        self.status = ScanningSettings()

        self.laser = CoboltLaser()
        self.camera = CameraProcess()

        self.camera_properties = CameraSettings()

        self.settings_tree = ParameterTree()

        self.planar_setting = PlanarScanningSettings()
        self.laser_settings = LaserSettings()
        self.stytra_comm = StytraCom(
            stop_event=self.stop_event,
            experiment_start_event=self.experiment_start_event,
        )

        self.save_status: Optional[SavingStatus] = None

        #self.save_queue = ArrayQueue(max_mbytes=800)
        self.saver = StackSaver(self.stop_event)

        self.single_plane_settings = SinglePlaneSettings()
        self.volume_setting = ZRecordingSettings()
        self.calibration = Calibration()

        for setting in [self.planar_setting, self.laser_settings, self.single_plane_settings, self.volume_setting,
                        self.calibration, self.calibration.z_settings, self.camera_properties]:
            self.settings_tree.add(setting)

        self.status.sig_param_changed.connect(self.send_settings)
        self.planar_setting.sig_param_changed.connect(self.send_settings)
        self.calibration.z_settings.sig_param_changed.connect(self.send_settings)
        self.single_plane_settings.sig_param_changed.connect(self.send_settings)
        self.volume_setting.sig_param_changed.connect(self.send_settings)
        self.camera_properties.sig_param_changed.connect(self.send_settings)

        self.camera.start()
        self.scanner.start()
        self.stytra_comm.start()
        self.saver.start()

    def restore_tree(self, restore_file):
        with open(restore_file, "r") as f:
            self.settings_tree.deserialize(json.load(f))

    def save_tree(self, save_file):
        with open(save_file, "w") as f:
            json.dump(self.settings_tree.serialize(), f)

    def toggle_experiment_state(self):
        if self.experiment_state == ExperimentPrepareState.NORMAL:
            self.experiment_state = ExperimentPrepareState.NO_CAMERA
        elif self.experiment_state == ExperimentPrepareState.NO_CAMERA:
            self.experiment_state = ExperimentPrepareState.START
        self.send_settings()

    def send_settings(self):
        if self.status.scanning_state == "Paused":
            params = ScanParameters(state=ScanningState.PAUSED)
        elif self.status.scanning_state == "Calibration":
            params = convert_calibration_params(
                self.planar_setting, self.calibration.z_settings
            )
        elif self.status.scanning_state == "Planar":
            params = convert_single_plane_params(
                self.planar_setting, self.single_plane_settings, self.calibration
            )
        elif self.status.scanning_state == "Volume":
            params = convert_volume_params(
                self.planar_setting, self.volume_setting, self.calibration
            )

        params.experiment_state = self.experiment_state
        self.scanner.parameter_queue.put(params)
        self.camera.parameter_queue.put(self.camera_properties)
        self.stytra_comm.current_settings_queue.put(params)
        if params.experiment_state == ExperimentPrepareState.START:
            self.experiment_state = ExperimentPrepareState.NORMAL

    def wrap_up(self):
        self.scanner.stop_event.set()
        self.scanner.join(timeout=10)
        self.laser.close()
        # FIXME: Not sure this will properly terminate the camera process
        self.camera.terminate()
        self.camera.join(timeout=10)

    def get_image(self):
        try:
            image = self.camera.image_queue.get(timeout=0.001)
            if self.saver.saving_signal.is_set():
                if (
                        self.save_status is not None
                        and self.save_status.i_t + 1 == self.save_status.target_params.n_t
                ):
                    self.wrap_up()
                self.saver.save_queue.put(image)
            return image
        except Empty:
            return None
