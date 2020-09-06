from sashimi.hardware.cameras.Hamamatsu_ORCA_flash_wrapper import HamamatsuOrcaFlashCamera
from sashimi.hardware.cameras import MockCamera

# Update this dictionary when adding a new camera!
camera_class_dict = dict(
    hamamatsu=HamamatsuOrcaFlashCamera,
    test=MockCamera,
)
