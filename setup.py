from distutils.core import setup
from setuptools import find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="sashimi",
    version="0.2.0",
    author="Vilim Stih @portugueslab",
    author_email="vilim@neuro.mpg.de",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={"console_scripts": ["sashimi=sashimi.main:main",
                                      "sashimi-config=sashimi.config:cli_modify_config"]},
)
