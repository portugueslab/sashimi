from sashimi.hardware.lasers.mock import MockLaser
from sashimi.hardware.lasers.cobolt import CoboltLaser

# Update this dictionary and add the import above when adding a new laser
laser_class_dict = dict(
    cobolt=CoboltLaser,
    test=MockLaser,
)
