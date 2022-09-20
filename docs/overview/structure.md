# The structure of Sashimi

Sashimi is structured in modules that communicate with each other via signals and use shared queues to broadcast data to different processes. In a simplified schematic (see [fig](sashimi-struct)) we can see how the `State.py` file is the core of the program, which controls and ties together the core functions.

It communicates with GUI and updates values for the GUI to read. It creates and overlooks processes that are responsible for directly controlling the hardware through custom interfaces. Moreover, the `State` controls the `Global State` variable of the program which defines the mode in which the program is. This is used by the GUI to change the interface and settings accordingly and by the different processes to control the hardware.

```{figure} ../images/sashimi_struct.png
---
height: 500px
name: sashimi-struct
---
Sashimi simplified code structure
```
