# The structure of Sashimi

Sashimi is built around the `State` class, which acts as the main process of the software, initializing other subprocesses and handling the core part of the data acquisiton.
As shown in the figure below, the GUI is composed of multiple widgets which take care of specific functionalities.
Each of them communicates with the state to get and send information to the hardware.
The state communicates with all the subprocesses which in turn control the hardware components through an interface.

![Sashimi Structure](../images/sashimi_structure.drawio.png)
