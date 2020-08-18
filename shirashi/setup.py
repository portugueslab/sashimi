from distutils.core import setup
from setuptools import find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="shirashi2",
    version="0.2.0",
    author="Vilim Stih @portugueslab",
    author_email="vilim@neuro.mpg.de",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="imaging microscopy lightsheet",
    description="A user-friendly software for efficient control of digital scanned light sheet microscopes (DSLMs).",
    entry_points={
        "console_scripts": [
            "shirashi2=shirashi2.main:main",
            "shirashi2-config=shirashi2.config:cli_modify_config",
        ]
    },
)
