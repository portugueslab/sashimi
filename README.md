# Sashimi

<a href="url"><img 
src="https://github.com/portugueslab/sashimi/blob/master/sashimi/icons/main_icon.png" 
align="left" 
height="190" 
width="270"></a>


Sashimi is a user-friendly software for efficient control of digital scanned light sheet microscopes (DSLMs).
It was developed by members of the [PortuguesLab](http://www.portugueslab.com/)
 at the Technical University of Munich and Max Planck Institute of Neurobiology. Sashimi relies on the fast, multidimensional
 [Napari viewer](https://github.com/napari/napari) and is accelerated by [numba](https://github.com/numba/numba) for real-time processing.

 
Hardware is controlled through [pyvisa](https://github.com/pyvisa/pyvisa) for serial communication and 
 [nidaqmx](https://github.com/ni/nidaqmx-python/) for National Instruments I/O boards.
 

 
# Installation

[Install the latest Anaconda](https://www.anaconda.com/) distribution of Python 3.

Clone this repository and navigate to the main folder (`../sashimi`)

### Recommended: Create a new environment

It is a good practice to create an environment for every project. You will now make an environment called `sashimi` which will run python 3.8:

    conda create -n sashimi python=3.8

We will run all related to this software in this environment. You can activate the environment running:

    conda activate sashimi
    
### Install with pip

For a non-editable installation run:

    pip install .

Otherwise, if you want to contribute to the project as a developer, for editable installation run:

    pip install -e .

Now you are ready to go!

# Starting the software from command line

Open a new anaconda prompt and activate your environment like above. Then run:

    sashimi
    
Press __User guide__ to pop-up instructions that will drive you through the whole experiment preparation, acquisition and termination.

# Configuring sashimi

You can ask sashimi for help:
   
    sashimi --help
    
Running `sashimi --debug` lets you start the software without any hardware connected to the machine. Sashimi includes the
`sashimi-config` module that lets you interact with the hardware and software settings from command line. You can display the
 current configuration of the system by running:
 
    sashimi-config show
 
More information on its usage can be found by asking `sashimi-config` for help:

    sashimi-config --help
   
You can add and modify parameters just from the command line. For example, to set the piezo waveform readout channel to `Dev1/ao0:0` just run:

    sashimi-config edit -n piezo.position_write.pos_chan -v Dev1/ao0:0
    
Or to modify the minimum and maximum voltage (in Volts) of the channel:
    
    sashimi-config edit -n piezo.position_write.min_val -v 0
    sashimi-config edit -n piezo.position_write.max_val -v 10
