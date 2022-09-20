# Multiprocessing

Multiprocessing allows programs to run multiple sets of instructions in separate processing units at the same time. The correctly implemented programs run much faster and take full advantage of multi-core CPUs. Python has an entire built-in library that offers multiprocessing tools and functionalities, such as the spawning and synching of separate processes, and the sharing of information between them. In microscopy, it is crucial to have events that happen fast and synchronously to one another, especially for light-sheet microscopy, where the piezo, vertical galvos, and the camera trigger must be synchronized to deliver a focused image. Multiprocessing ensures that multiple hardware components and functionalities can work simultaneously, and even more importantly can redistribute priority to make sure that the most important tasks are executed in the correct time frame, while other, less time-sensitive tasks, can be processed less promptly.

As an example, in a light-sheet microscope, it is of the utmost importance that galvos, camera triggers, and piezo are synchronized, while the process that saves the data in the memory can work asynchronously with the other processes. Obviously, most processes need to keep up with the whole program in order to avoid stalls and delays, but given enough speed and buffers, some functionalities do not need to be as precise and synched as others. This allows the computer to also allocate resources dynamically to fulfill the tasks at hand.

## Logging

The `logging process` is a simple class that implements a **concurrence logger** inside it. This means that the logger will log the message and the context in which a message was sent.The logger has built-in functions to log events, queues, and any particular message in a custom file. Any other process inherits from this class and will have a logger built-in which will make logging events and messages easy and organized. To automatically log inside events there’s another class called LoggedEvent which accepts a range of internally defined events and a logger and returns an Event (from the multiprocessing library) which expands each functionality of the event class with an in-built logger. 
The initialization process follows these steps:

1. The main process creates a `LoggedEvent`
2. The `LoggedEvent` is passed to one of the processes
3. The process assigns it’s logger to the `LoggedEvent`
4. Now, every time the event is set, cleared or pinged, it will be automatically logged in the process logging file

## Camera

The camera process handles all the camera-related functionality and sets the camera parameters, mode, and trigger. It computes and checks the framerate and runs the camera in a mode-dependent loop. 

If the current program mode is `Paused`, then the loop waits for the mode to change and keeps checking for updates of the camera parameters, on the other hand, if the mode is `Preview`, the loop gets new frames from the camera and inserts them in a queue, at the end it checks for changes in the camera parameters and eventually updates them. Until the program is closed, the camera is kept in this constant loop between preview mode and pause mode.
he last possible camera mode is used to abort the current preview, stop the camera, and set the paused mode.

## Scanning

The scanning process leverages the implementations of the scanning loops inside the interface and it mainly sets the loop and updates the relevant settings. It initializes the board, settings, and queues, which then passes to a loop object. This loop object will be either an implementation of the `PlanarScanLoop` or of the `VolumetricScanLoop` depending on the mode in which the program is.

## External Communication

The external communication process uses the connection made by the external trigger interface to keep updating the settings, and checking the trigger conditions. Once these conditions are set, it sends a trigger and receives the duration of the experiment. The duration is then inserted inside a queue, where it will be read by the main process and used to compute the end signal of the acquisition.

## Dispatching & Saving

There are two more processes that take care of the setup of the volumes and their saving in memory. The dispatcher process runs a loop where it gets the newest settings and gets a frame from the camera process queue. 

This frame is then optionally filtered from the sensor background noise (this can be activated in the volumetric mode widget) and stacked with others until it completes a volume. The volume is then fed to two queues, one is for saving the volume and the other one is for the preview which is displayed by the viewer. The saving process is a bit more complex since it also holds the saving parameters and the saving status (which is important to keep track of the current chunk which has been saved). 

The saving loop executes the following actions:

1. Initialize the saving folder
2. Reads a volume from the dispatcher queue
3. Calculates the optimal size for a file to be saved in chunks based on the size of the data and the ram memory
4. It stores n volumes until it reaches the optimal size
5. It saves the chunk in an .h5 file
6. Once it finishes saving it saves a .json file with all the metadata inside

This dynamical approach to the saving process ensures that the program doesn't get overloaded while trying to save the acquired data.
