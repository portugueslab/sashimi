from enum import Enum
from queue import Empty

from PyQt5.Qt import QObject, pyqtSignal

from typing import Optional
import numpy as np
from lightparam import Param
from lightparam.param_qt import ParametrizedQt

from sashimi.events import LoggedEvent, SashimiEvents
from sashimi.processes.scanning import ScannerProcess
from sashimi.hardware.scanning.scanloops import (
    PlanarScanning,
    XYScanning,
    ScanParameters,
    ScanningMode,
    ZManual,
    ZSynced,
    TriggeringParameters,
    ZScanning,
)
from sashimi.utilities import get_last_parameters


class ScanningUseMode(Enum):
    PAUSED = 0
    PREVIEW = 1
    PLANAR = 2
    VOLUME = 3


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
        self.piezo_scan_range = Param((180.0, 220.0), (0.0, 400.0), unit="um")
        self.frequency = Param(3.0, (0.1, 100), unit="volumes/s (Hz)")
        self.n_planes = Param(4, (2, 100))
        self.n_skip_start = Param(0, (0, 20))
        self.n_skip_end = Param(0, (0, 20))


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
        mode=ScanningMode.PLANAR,
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


def convert_single_plane_params(
    planar: PlanarScanningSettings,
    single_plane_setting: SinglePlaneSettings,
    calibration: Calibration,
):
    return ScanParameters(
        mode=ScanningMode.PLANAR,
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
        mode=ScanningMode.VOLUMETRIC,
        xy=convert_planar_params(planar),
        z=ZScanning(
            piezo_min=z_setting.piezo_scan_range[0],
            piezo_max=z_setting.piezo_scan_range[1],
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


def significant_scanning_change(new_params: ScanParameters, old_params: Optional[ScanParameters]):
    if old_params is None:
        return True
    if new_params.experiment_state != old_params.experiment_state:
        return True
    if new_params.triggering.n_planes != old_params.triggering.n_planes:
        return True
    return False


def merits_restart(new_params: ScanParameters, old_params: Optional[ScanParameters]):
    # TODO insert the condition that the restart should not happen if all the important
    # conditions are the same, (the exception being camera triggerning)
    if new_params.mode == ScanningMode.VOLUMETRIC:
        return True
    return False


class ScanningManager(QObject):
    """Class that manages everything scanning-related in the main thread

    """

    scanning_changed = pyqtSignal()

    def __init__(self, sample_rate, stop_event, logger):
        super().__init__()
        self.logger = logger
        self.scanning_mode = ScanningUseMode.PAUSED

        self.planar_setting = PlanarScanningSettings()
        self.single_plane_settings = SinglePlaneSettings()
        self.volume_setting = ZRecordingSettings()
        self.calibration = Calibration()
        self.sample_rate = sample_rate

        # The even active during scanning preparation (before first real camera trigger)
        self.is_waiting_event = LoggedEvent(
            self.logger, SashimiEvents.WAITING_FOR_TRIGGER
        )
        self.restart_event = LoggedEvent(self.logger, SashimiEvents.RESTART_SCANNING)

        self.planar_setting.sig_param_changed.connect(self.settings_changed)
        self.calibration.z_settings.sig_param_changed.connect(self.settings_changed)
        self.single_plane_settings.sig_param_changed.connect(self.settings_changed)
        self.volume_setting.sig_param_changed.connect(self.settings_changed)

        self.scanner = ScannerProcess(
            stop_event=stop_event,
            restart_event=self.restart_event,
            waiting_event=self.is_waiting_event,
            sample_rate=self.sample_rate,
        )

        self.all_settings = [
            self.planar_setting,
            self.single_plane_settings,
            self.volume_setting,
            self.calibration,
            self.calibration.z_settings,
        ]

        self.current_plane = 0
        self.waveform = None
        self.last_params = None

    def start(self):
        self.scanner.start()

    @property
    def n_planes(self):
        if self.scanning_mode == ScanningUseMode.VOLUME:
            return (
                self.volume_setting.n_planes
                - self.volume_setting.n_skip_start
                - self.volume_setting.n_skip_end
            )
        else:
            return 1

    @property
    def volume_rate(self) -> Optional[float]:
        return self.volume_setting.frequency

    @property
    def interplane_distance(self):
        scan_length = (
            self.volume_setting.piezo_scan_range[1]
            - self.volume_setting.piezo_scan_range[0]
        )
        return scan_length / self.volume_setting.n_planes

    def settings_changed(self):
        self.configure_scanning()

    def configure_scanning(self):
        if self.scanning_mode == ScanningUseMode.PAUSED:
            params = ScanParameters(mode=ScanningMode.PAUSED)

        elif self.scanning_mode == ScanningUseMode.PREVIEW:
            params = convert_calibration_params(
                self.planar_setting, self.calibration.z_settings
            )

        elif self.scanning_mode == ScanningUseMode.PLANAR:
            params = convert_single_plane_params(
                self.planar_setting, self.single_plane_settings, self.calibration,
            )

        elif self.scanning_mode == ScanningUseMode.VOLUME:
            params = convert_volume_params(
                self.planar_setting, self.volume_setting, self.calibration
            )
            # Make sure that current plane is updated if we changed number of planes
            self.current_plane = min(self.current_plane, self.n_planes - 1)
            if self.waveform is not None:
                pulses = self.calculate_pulse_times() * self.sample_rate
                try:
                    pulse_log = self.waveform[pulses.astype(int)]
                    self.all_settings["piezo_log"] = {"trigger": pulse_log.tolist()}
                except IndexError:
                    pass

        params.experiment_state = self.scanning_mode

        if merits_restart(params, self.last_params):
            self.restart_event.set()

        if significant_scanning_change(params, self.last_params):
            self.scanning_changed.emit()

        # TODO introduce previous_mode to persist z settings across the modes
        # if param_changed is not None:
        #     key = list(param_changed.keys())[0]
        #     if "piezo" in key:
        #         val = param_changed[key]
        #         piezo_pos = val[0] if type(val) is tuple else val
        #
        #         # Block change signals, change, and unblock
        #         self.single_plane_settings.block_signal = True
        #         self.calibration.z_settings.block_signal = True
        #         self.volume_setting.block_signal = True
        #
        #         # Change z values:
        #         self.single_plane_settings.piezo = piezo_pos
        #         # self.calibration.z_settings.piezo = piezo_pos
        #         current_range = self.volume_setting.piezo_scan_range[1] - self.volume_setting.piezo_scan_range[0]
        #         self.volume_setting.piezo_scan_range = (piezo_pos, piezo_pos + current_range)
        #
        #         # Unblock change signals:
        #         self.single_plane_settings.block_signal = False
        #         self.calibration.z_settings.block_signal = False
        #         self.volume_setting.block_signal = False

        self.scanner.parameter_queue.put(params)

        self.last_params = params

    def prepare_experiment(self):
        self.scanner.wait_signal.set()

    def wrap_up(self):
        self.scanner.join(timeout=10)

    def calculate_pulse_times(self):
        return np.arange(
            self.volume_setting.n_skip_start,
            self.volume_setting.n_planes - self.volume_setting.n_skip_end,
        ) / (self.volume_setting.frequency * self.volume_setting.n_planes)

    def piezo_values_at_trigger_times(self):
        pulses = self.calculate_pulse_times() * self.sample_rate
        try:
            pulse_log = self.waveform[pulses.astype(int)]
            return dict(trigger=pulse_log.tolist())
        except IndexError:
            pass

    def get_waveform(self):
        get_last_parameters(self.scanner.waveform_queue)
