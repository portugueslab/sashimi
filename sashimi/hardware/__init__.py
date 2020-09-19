from sashimi.hardware.light_source.mock import MockLaser
from sashimi.hardware.light_source.cobolt import CoboltLaser

# Update this dictionary and add the import above when adding a new laser
light_source_class_dict = dict(
    cobolt=CoboltLaser,
    test=MockLaser,
)
