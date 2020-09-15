from sashimi.hardware.cameras.hamamatsu_wrapper import HamamatsuCamera
from sashimi.hardware.cameras import MockCamera

# Update this dictionary when adding a new camera!
camera_class_dict = dict(
    hamamatsu=HamamatsuCamera,
    test=MockCamera,
)
