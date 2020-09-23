from pathlib import Path
import click
import toml
from lightparam import set_nested, get_nested

CONFIG_FILENAME = "hardware_config.toml"
CONFIG_DIR_PATH = Path.home() / ".sashimi"
CONFIG_DIR_PATH.mkdir(exist_ok=True)
PRESETS_DIR_PATH = Path.home() / "presets"
PRESETS_DIR_PATH.mkdir(exist_ok=True)
LOGS_DIR_PATH = Path.home() / "logs"
LOGS_DIR_PATH.mkdir(exist_ok=True)
SCOPE_INSTRUCTIONS_PATH = Path()

CONFIG_PATH = CONFIG_DIR_PATH / CONFIG_FILENAME

# 2 level dictionary for sections and values:
# TODO this will obviously have to change to fit scanning declarations
TEMPLATE_CONF_DICT = {
    "scanning": "mock",
    "scopeless": False,
    "scanless": False,
    "sample_rate": 40000,
    "default_paths": {
        "data": str(Path.home()),
        "presets": str(PRESETS_DIR_PATH),
        "log": str(LOGS_DIR_PATH),
        "scope_instructions": str(SCOPE_INSTRUCTIONS_PATH),
    },
    "z_board": {
        "read": {
            "channel": "Dev1/ai0:0",
            "min_val": 0,
            "max_val": 10,
        },
        "write": {
            "channel": "Dev1/ao0:3",
            "min_val": -5,
            "max_val": 10,
        },
        "sync": {"channel": "/Dev1/ao/StartTrigger"},
    },
    "piezo": {
        "scale": 1 / 40,
    },
    "xy_board": {
        "write": {
            "channel": "Dev2/ao0:1",
            "min_val": -5,
            "max_val": 10,
        }
    },
    "light_source": {
        "name": "mock",
        "port": "COM4",
        "intensity_units": "mA"

    },
    "notifier": "none",
    "notifier_options": {},
    "array_ram_MB": 450,
}


def write_default_config(file_path=CONFIG_PATH, template=TEMPLATE_CONF_DICT):
    """Write configuration file at first repo usage. In this way,
    we don't need to keep a confusing template config file in the repo.

    Parameters
    ----------
    file_path : Path object
        Path of the config file (optional).
    template : dict
        Template of the config file to be written (optional).

    """

    with open(file_path, "w") as f:
        toml.dump(template, f)


def read_config(file_path=CONFIG_PATH):
    """Read Sashimi config.

    Parameters
    ----------
    file_path : Path object
        Path of the config file (optional).

    Returns
    -------
    ConfigParser object
        sashimi configuration
    """

    # If no config file exists yet, write the default one:
    if not file_path.exists():
        write_default_config()

    return toml.load(file_path)


def write_config_value(dict_path, val, file_path=CONFIG_PATH):
    """Write a new value in the config file. To make things simple, ignore
    sections and look directly for matching parameters names.

    Parameters
    ----------
    dict_path : str or list of strings
        Full path of the section to configure
        (e.g., ["piezo", "position_read", "min_val"])
    val :
        New value.
    file_path : Path object
        Path of the config file (optional).

    """
    # Ensure path to entry is always a string:
    if type(dict_path) == str:
        dict_path = [dict_path]

    # Read and set:
    conf = read_config(file_path=file_path)
    set_nested(conf, dict_path, val)

    # Write:
    with open(file_path, "w") as f:
        toml.dump(conf, f)


@click.command()
@click.argument("command")
@click.option("-n", "--name", help="Path (section/name) of parameter to be changed")
@click.option("-v", "--val", help="Value of parameter to be changed")
@click.option(
    "-p",
    "--file_path",
    default=CONFIG_PATH,
    help="Path to the config file (optional)",
)
def cli_modify_config(command, name=None, val=None, file_path=CONFIG_PATH):
    file_path = Path(file_path)
    if command == "edit":
        cli_edit_config(name, val, file_path)

    elif command == "show":
        click.echo(_print_config(file_path=file_path))


def cli_edit_config(name=None, val=None, file_path=CONFIG_PATH):
    conf = read_config(file_path=file_path)

    # Cast the type of the previous variable
    # (to avoid overwriting values with strings)
    dict_path = name.split(".")
    old_val = get_nested(conf, dict_path)
    val = type(old_val)(val)  # Convert to keep the same type

    write_config_value(dict_path, val, file_path)


def _print_config(file_path=CONFIG_PATH):
    """Return configuration string for printing."""
    config = read_config(file_path=file_path)
    return toml.dumps(config)
