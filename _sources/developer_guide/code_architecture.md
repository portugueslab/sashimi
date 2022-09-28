# Code architecture

Sashimi is structured in modules that communicate with each other via signals and use shared queues to broadcast data to different processes.
In a simplified schematic we can see how the `State` file is the core of the program, which controls and ties together the core functions.
It communicates with GUI and updates values for the GUI to read, it creates and overlooks processes that then are responsible for directly controlling the hardware through custom interfaces.
Moreover, the State controls the _Global State_ variable of the program which defines the mode in which the program is.  This is used by the GUI to change the interface and settings accordingly and by the different processes to control the hardware.

![Sashimi Structure](../images/sashimi_structure.drawio.png)
