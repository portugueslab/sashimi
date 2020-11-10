from sashimi.hardware.scanning.mock import open_mockboard
from sashimi.hardware.scanning.interface import ScanningError, AbstractScanInterface

try:
    from sashimi.hardware.scanning.ni import open_niboard

    NI_AVAILABLE = True
except ImportError:
    NI_AVAILABLE = False

# Dictionary of options for the context within which the scanning has to run.
scan_conf_dict = dict(mock=open_mockboard)

# Add NI context if available. NI board will be initialized there.
if NI_AVAILABLE:
    scan_conf_dict["ni"] = open_niboard
