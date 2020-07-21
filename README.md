# SLiM

<a href="url"><img 
src="https://github.com/portugueslab/lightsheet_take_two/blob/master/lightsheet/icons/main_icon.png" 
align="left" 
height="190" 
width="270"></a>

<br/>SLiM is a user-friendly software for efficient control of digital scanned light sheet microscopes (DSLMs).
It was developed by members of the [PortuguesLab](http://www.portugueslab.com/)
 at the Technical University of Munich and Max Planck Institute of Neurobiology. SLiM relies on the fast, multidimensional
 [Napari viewer](https://github.com/napari/napari) and is powered by [numba](https://github.com/numba/numba) for increased efficiency.
 
Hardware is controlled through [pyvisa](https://github.com/pyvisa/pyvisa) for serial communication and 
 [nidaqmx](https://github.com/ni/nidaqmx-python/) for National Instruments I/O boards.
 
<br/><br/>
 
# Installation

[Install the latest Anaconda](https://www.anaconda.com/) distribution of Python 3.

Clone this repository and navigate to the main folder (`/lightsheet_take_two`)

### Recommended: Create a new environment

For instructions visit [this site](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands). Then activate the environment (replace `my_env` for the name of your environment):

    conda activate my_env
    
### Install with pip

For a non-editable installation run:

    pip install .

Otherwise, for editable installation run:

    pip install -e .

Now you are ready to go!

# Starting the software from command line

Open a new anaconda prompt and activate your environment like above. Then run:

    slim

Sit back, relax and enjoy your experience!
