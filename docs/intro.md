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

# Configuring sashimi
    
Sashimi includes the `sashimi-config` module that lets you interact with the hardware and software
settings from command line. You can display the current configuration of the system.:
 
    sashimi-config show
    
You can ask sashimi for help:
   
    sashimi --help
 
More information on its usage can be found by asking `sashimi-config` for help:

    sashimi-config --help
   
You can add and modify parameters just from the command line. For example, to set the piezo waveform readout channel to `Dev1/ao0:0` just run:

    sashimi-config edit -n z_board.write.channel -v Dev1/ao0:0
    
Or to modify the minimum and maximum voltage (in Volts) of the channel:
    
    sashimi-config edit -n piezo.position_write.min_val -v 0
    sashimi-config edit -n piezo.position_write.max_val -v 10
    

# Starting the software from command line

Open a new anaconda prompt and activate your environment like above. Then run:

    sashimi
    
Add the option `--scopeless`:

    sashimi --scopeless
    
If you want to run the software with mock hardware, such as for debugging or developing.
