from sashimi.hardware.external_trigger.stytra import StytraComm
from sashimi.hardware.external_trigger.mock import MockComm


# Update this dictionary and add the import above when adding a new external communication
external_comm_class_dict = dict(stytra=StytraComm, mock=MockComm,)
