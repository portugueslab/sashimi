# Installation

[Install the latest Anaconda](https://www.anaconda.com/) distribution of Python 3.

Clone this repository and navigate to the main folder `../sashimi`

## Recommended: Create a new environment

It is a good practice to create an environment for every project. The provided `environment.yml` sets up almost all required dependencies (see below).

    conda env create -f {path to environment.yml}

You can activate the environment by running:

    conda activate sashimi
    
After this you moght have to install two extra dependencies for controlling a Cobolt laser:

    pip install pyvisa
    pip install pyvisa-py
    
## Install with pip

For a non-editable installation run:

    pip install .

Otherwise, if you want to contribute to the project as a developer, for editable installation run:

    pip install -e .

Now you are ready to go!
