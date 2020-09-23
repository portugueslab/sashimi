from sashimi.hardware.light_source.mock import MockLaser
from sashimi.hardware.light_source.cobolt import CoboltLaser
from sashimi.hardware.external_trigger.stytra import StytraComm
from sashimi.hardware.external_trigger.mock import MockComm
from sashimi.hardware.cameras.mock import MockCamera
from sashimi.hardware.cameras.hamamatsu import HamamatsuCamera

# Update this dictionary and add the import above when adding a new laser
light_source_class_dict = dict(
    cobolt=CoboltLaser,
    mock=MockLaser,
)

# Update this dictionary and add the import above when adding a new external communication
external_comm_class_dict = dict(
    stytra=StytraComm,
    mock=MockComm,
)

# Update this dictionary and add the import above when adding a new camera
camera_class_dict = dict(
    hamamatsu=HamamatsuCamera,
    mock=MockCamera,
)
