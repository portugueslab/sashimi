# Hardware Control

One of the strengths of Sashimi is the smart use of interfaces for the connection with potentially any hardware component.
Whenever a component needs to be swapped it can be easily done by just creating a custom python file for its connection to the Sashimi interface.  The main hardware components needed are a light source (laser), a camera, a piezo and multiple galvos for directing the laser and creating a sheet of light, and, finally, a board to drive most of the triggers.
Each interface is defined as an Abstract class which ensures that while creating a new custom module, inheriting from the interface, all the functions and properties necessary for the software to work will be implemented.

## Light-Source Interface

The light source interface enforces that any custom light source module defines a method for setting the power of the laser, a method for closing the laser, and properties for reading the intensity of the laser and the status (ON, OFF).
At the moment, only two modules are present in the software:

- Mock light source, which mocks the behavior of the light source and it’s used mainly for testing purposes
- Cobolt light source, which takes care of the opening and setting up of the Cobolt laser.

## Camera Interface

The camera interface outlines the functions and properties needed for the control of the camera and for the adjustment of the most relevant settings.
The core methods are start/stop acquisition, shutdown the camera, and most importantly, get_frames which returns a list of images.
Using the camera interface it’s possible to change the following properties:

- Binning size
- Exposure time
- Trigger mode, which is expected to be external for Sashimi volumetric mode
- Frame Rate, which can only be read (to change this value you’ll need to change the exposure time)
- Sensor resolution, which computes the resolution based on the binning size and the maximum resolution (setting to be defined in the configuration file)

For this interface there’s a mock module which displays a gaussian filtered noise image, and a module for the Hamamatsu Orca flash 4.0 v3 camera.

## External-Trigger Interface

The external trigger interface allows synchronizing Sashimi with behavioral software for stimulus presentation. To achieve this it uses the python bindings of ZeroMQ, a high-performance asynchronous messaging library.
The interface takes care of establishing the connection to the other software and returning the total duration of the experiment protocol.
The duration will be then used by the external communication process to update the acquisition duration of the experiment inside Sashimi.
There’s a module that allows for built-in connection between Sashimi and [Stytra](https://www.portugueslab.com/stytra/index.html), an open-source software package, designed to cover all the general requirements involved in larval zebrafish behavioral experiments.  Once an experiment protocol is ready, and both softwares are set up correctly, Stytra will stand by and wait for a message from the acquisition software (Sashimi) to start the experiment.  This message is automatically sent once the acquisition start is triggered in the Sashimi GUI.

## Scanning Interface

The scanning interface is the more complicated interface since it needs to handle the NI board which in turn controls the scanning hardware.
This interface outlines three simple methods to write and read samples from the board, as well as initialization of the board and start of the relevant tasks.
There are multiple properties that control different functionalities:

- z_piezo, reads and writes values to move the piezo vertically.
- z_frontal, reads and writes values to move the frontal laser vertically.
- xy_frontal, reads and writes values to move the frontal laser horizontally.
- z_lateral, reads and writes values to move the lateral laser vertically.
- xy_lateral, reads and writes values to move the lateral laser horizontally.
- Camera_trigger, triggers the acquisition of one frame.

The implementation of the scanning interfaces connects to the NI board and initialize three analog strea:

- xy_writer, which combines the frontal and lateral galvos moving the laser horizontally and outputs a waveform.
- z_reader, which reads the piezo position.
- z_writer, which combines the frontal and lateral galvos moving the laser vertically, the piezo and the camera trigger.   For each of them the output varies depending on the mode in which the software is.

Inside the config file there’s a factor that allows applying a rescaling factor to the piezo.

Another major part of the interface is the implementation of different scanning loops to continuously move the laser to form a sheet of light and move it in z synchronously with the piezo in order to keep the focus.
There is a main class called ScanLoop  which continuously checks whether the settings have changed, fills the input arrays with the appropriate waveform, writes this array on the NI board (through the scanning interface), reads the values from the NI board, and keeps a count of the current written and read samples.
Two classes inherit from this main class:

- PlanarScanLoop
- VolumetricScanLoop

The main difference between the two is the way they fill the arrays responsible to control the vertical movement of Piezo and galvos.
Inside the planar loop there’s two possible modes, one of which is used for calibration purposes and it’s completely manual.  In this mode the piezo is moved independently of the lateral and frontal vertical galvos. This allows for proper calibration of the focus plane for each specimen placed in the microscope.
The other mode is synched and uses the linear function computed by the calibration to compute the appropriate value for each galvo, based on the piezo position.
The volumetric loop instead writes a sawtooth waveform to the piezo, then it reads the piezo position and computes the appropriate value to set the vertical galvos to.
Given the desired framerate, it will also generate an array of impulses for the camera trigger, where the initial or final frame can be skipped depending on the waveform of the piezo. For ease of use the waveform is shown in the GUI so that the user can decide how many frames to skip depending on the settings that they inserted.
