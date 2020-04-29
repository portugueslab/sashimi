import numpy as np
from lightparam.param_qt import ParametrizedQt
from lightparam import Param
from lightsheet.hardware.laser import CoboltLaser, LaserSettings
from lightsheet.scanning import (
    Scanner,
    PlanarScanning,
    ZScanning,
    ZSynced,
    ZManual,
    XYScanning,
    ScanParameters,
    ScanningState,
)
from copy import deepcopy


class ScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.scanning_state = Param(
            "Paused", ["Paused", "Calibration", "Planar scanning", "Volume"],
        )


class PlanarScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "planar"
        self.lateral_range = Param((0, 0.5), (-2, 2))
        self.lateral_frequency = Param(500.0, (10, 1000), unit="Hz")
        self.frontal_range = Param((0, 0.5), (-2, 2))
        self.frontal_frequency = Param(500.0, (10, 1000), unit="Hz")


class CalibrationZSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "z_control"
        self.piezo = Param(0.0, (0.0, 400.0), unit="um")
        self.lateral = Param(0.0, (-2.0, 2.0))
        self.frontal = Param(0.0, (-2.0, 2.0))


class ZSetting(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "z_control"
        self.piezo = Param(0.0, (0.0, 400.0), unit="um")


class ZRecordingSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.scan_range = Param((0.0, 10.0), (0.0, 400.0), unit="um")
        self.frequency = Param(1.0, (0.001, 100), unit="Hz")
        self.n_planes_total = Param(10, (1, 100))
        self.n_skip_ventral = Param(0, (0, 20))
        self.n_skip_dorsal = Param(0, (0, 20))


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


class Calibration:
    def __init__(self):
        super().__init__()
        self.z_settings = CalibrationZSettings()
        self.calibrations_points = []
        self.calibration = [(0, 0.01), (0, 0.01)]

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
            calibration_data[:, 0:1], ((0, 0), (1, 0)), constant_values=1.0
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
    planar: PlanarScanningSettings, z_setting: ZSetting, calibration: Calibration
):
    return ScanParameters(
        state=ScanningState.PLANAR,
        xy=convert_planar_params(planar),
        z=ZSynced(
            piezo=z_setting.piezo,
            lateral_sync=tuple(calibration.calibration[0]),
            frontal_sync=tuple(calibration.calibration[1]),
        ),
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
    )


class State:
    def __init__(self):
        self.scanner = Scanner()
        self.status = ScanningSettings()
        self.planar_setting = PlanarScanningSettings()
        self.laser_settings = LaserSettings()

        self.z_setting = ZSetting()
        self.volume_setting = ZRecordingSettings()
        self.calibration = Calibration()

        self.status.sig_param_changed.connect(self.send_settings)
        self.planar_setting.sig_param_changed.connect(self.send_settings)
        self.calibration.z_settings.sig_param_changed.connect(self.send_settings)
        self.z_setting.sig_param_changed.connect(self.send_settings)
        self.volume_setting.sig_param_changed.connect(self.send_settings)

        self.laser = CoboltLaser()
        self.scanner.start()

    def send_settings(self):
        if self.status.scanning_state == "Paused":
            params = ScanParameters(state=ScanningState.PAUSED)
        elif self.status.scanning_state == "Calibration":
            params = convert_calibration_params(
                self.planar_setting, self.calibration.z_settings
            )
        elif self.status.scanning_state == "Planar":
            params = convert_planar_params(
                self.planar_setting, self.z_setting, self.calibration
            )
        elif self.status.scanning_state == "Volume":
            params = convert_volume_params(
                self.planar_setting, self.volume_setting, self.calibration
            )
        else:
            print("Should have not gotten here")
            return
        self.scanner.parameter_queue.put(deepcopy(params))

    def wrap_up(self):
        self.scanner.stop_event.set()
        self.scanner.join(timeout=10)
        self.laser.close()
