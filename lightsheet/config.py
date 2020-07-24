import configparser
from pathlib import Path
from pkg_resources import resource_filename
import click

CONFIG_FILENAME = "hardware_config.conf"
CONFIG_PATH = Path(resource_filename("lightsheet", CONFIG_FILENAME))

# 2 level dictionary for sections and values:
TEMPLATE_CONF_DICT = {
    "piezo": {
        "dev": 0,
        "chan": 1,
    },
    "galvo_lat": {
            "dev": 1,
            "chan": 0,
        }
}


def write_default_config(path=CONFIG_PATH, template=TEMPLATE_CONF_DICT):
    """Write configuration file at first repo usage. In this way,
    we don't need to keep a confusing template config file in the repo.

    Parameters
    ----------
    path : Path object
        Path of the config file (optional).
    template : dict
        Template of the config file to be written (optional).

    """

    conf = configparser.ConfigParser()
    for k, val in template.items():
        conf[k] = val

    with open(path, "w") as f:
        conf.write(f)


def read_config(path=CONFIG_PATH):
    """Read Sashimi config.

    Parameters
    ----------
    path : Path object
        Path of the config file (optional).

    Returns
    -------
    ConfigParser object
        sashimi configuration
    """

    # If no config file exists yet, write the default one:
    if not path.exists():
        write_default_config()

    conf = configparser.ConfigParser()
    conf.read(path)

    return conf


def write_config_value(section_name, key, val, path=CONFIG_PATH):
    """Write a new value in the config file. To make things simple, ignore
    sections and look directly for matching parameters names.

    Parameters
    ----------
    sect_name : str
        Name of the section to configure.
    key : str
        Name of the parameter to configure.
    val :
        New value.
    path : Path object
        Path of the config file (optional).

    """
    # If no config file exists yet, write the default one:
    if not path.exists():
        write_default_config()

    conf = configparser.ConfigParser()
    conf.read(path)
    conf[section_name][key] = str(val)

    with open(CONFIG_PATH, "w") as f:
        conf.write(f)

@click.command()
@click.argument("command")
@click.option("-n", "--name",
              help="Path (section/name) of parameter to be changed")
@click.option("-v", "--val",
              help="Value of parameter to be changed")
def cli_modify_config(command, name=None, val=None):
    # Ensure that we choose valid paths for default directory. The path does
    # not have to exist yet, but the parent must be valid:
    if command == "edit":
        section_name, key = name.split("/")
        write_config_value(section_name, key, val)
    elif command == "show":
        click.echo(_print_config())


def _print_config():
    """Print configuration.
    """
    config = read_config()
    string = ""
    for sect_name, sect_content in config.items():
        string += f"[{sect_name}]\n"
        for k, val in sect_content.items():
            string += f"\t{k}: {val}\n"

    return string
