import numpy as np
from lightparam.param_qt import ParametrizedQt
from lightparam import Param
from lightsheet.scanning import (
    PlanarScanning,
    ZScanning,
    XYScanning,
    ScanParameters,
    ScanningState,
)


class PlanarScanningSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "planar"
        self.lateral_range = Param((0, 0.5), (-2, 2))
        self.lateral_frequency = Param(500.0, (10, 1000))
        self.frontal_range = Param((0, 0.5), (-2, 2))
        self.frontal_frequency = Param(500.0, (10, 1000))


class ZSettings(ParametrizedQt):
    def __init__(self):
        super().__init__()
        self.name = "z_control"
        self.piezo = Param(0.0, (0.0, 400.0), unit="um")
        self.lateral = Param(0.0, (-2.0, 2.0))
        self.frontal = Param(0.0, (-2.0, 2.0))


class ZRecordingSettings(ParametrizedQt):
    def __init__(self):
        super().__init__(self)
        self.scan_range = Param(0.0, (0.0, 400.0), unit="um")
        self.n_planes_total = Param(10, (1, 100))
        self.n_skip_ventral = Param(0, (0, 20))
        self.n_skip_dorsal = Param(0, (0, 20))


def convert_calibration_params(planar: PlanarScanningSettings, zsettings: ZSettings):
    return ScanParameters(
        state=ScanningState.PLANAR,
        xy=PlanarScanning(
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
        ),
        z=ZScanning(**zsettings.params.values),
    )


class State:
    def __init__(self):
        self.planar_setting = PlanarScanningSettings()


class CalibrationState(State):
    def __init__(self):
        super().__init__()
        self.z_settings = ZSettings()
        self.calibrations_points = []
        self.calibration = None

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
            piezo_cor @ piezo_val.T @ galvo for galvo in [lateral_val, frontal_val]
        ]

        return True
