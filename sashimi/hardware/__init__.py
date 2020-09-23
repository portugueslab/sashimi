from sashimi.hardware.light_source.mock import MockLaser
from sashimi.hardware.light_source.cobolt import CoboltLaser
from sashimi.hardware.external_trigger.stytra import StytraComm
from sashimi.hardware.external_trigger.mock import MockComm

# Update this dictionary and add the import above when adding a new laser
light_source_class_dict = dict(
    cobolt=CoboltLaser,
    test=MockLaser,
)

# Update this dictionary and add the import above when adding a new external communication
external_comm_class_dict = dict(
    stytra=StytraComm,
    test=MockComm,
)
