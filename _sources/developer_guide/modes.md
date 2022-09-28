# Modes Panel

## Calibration Mode

The calibration mode is divided in 2 sections, at the top there are three sliders which allow the user to manually set the vertical frontal galvo, the vertical lateral galvo and the piezo.
Below there are two buttons to add or remove a calibration point.
And at the bottom there is another section for activating the noise subtraction function.
The calibration routine works as follows:

- Firstly, you cover one laser beam (either the frontal or lateral)
- Move the piezo in a position
- Adjust the non-covered laser beam with the corresponding vertical galvo slider until the image in the viewer is sharp enough
- Cover the other laser and adjust the non-covered laser beam with the corresponding vertical galvo slider until the image in the viewer is sharp enough
- Add the calibration point with the button
- Repeat for multiple piezo positions

To choose the piezo position two things are important: firstly, it's best if  the piezo position used for the calibration includes the vertical scanning range that will be set in the volumetric mode, secondly, the more calibration points are present the more accurate the calibration will be.
The software will try to fit a linear function to the points, so the more points the more accurate the estimate will be.
The second section of the calibration mode allows the user to activate a noise subtraction filter.  Once it’s activated a pop-up will ask the user to turn off all the lights and the software will take an n number of images (see fig) to compute the average sensor noise.
This is then saved and subtracted to all the following acquired frames.

## Planar Mode

```{warning}
This mode is still under construction and doesn't fully work yet!
```

The planar mode is quite simple and has only two modifiable inputs:

- A slider to adjust the piezo position (here the galvos will be moved of an amount which is computed using the calibration points)
- A frequency selector, that allows us to set the frequency at which we desire to acquire images.

## Volumetric Mode

The  volumetric mode is the core function of the software, since it allows for  fast volume acquisition.
It can be divided in two sections, the first one allows for the input of various settings, while the second one displays the waveform of the piezo vs lateral galvo with the camera triggers overlaid on top.
The setting that can be input to the software are the following:

- A scanning range from ventral to rostral piezo position
- A volume rate per second
- The number of planes to acquire for each volume
- The number of planes to skip at the beginning of each volume
- The number of planes to skip at the end of each volume
- A button to select whether to pause the live view after the experiment

To understand why it may be necessary to drop some planes at the beginning and end of the volume acquisition is important to understand how the volumetric scanner works.
During the volumetric scanning the piezo keeps moving following a waveform (see fig), and the galvos follow it based on the calibration.   During the acquisition of each frame, the piezo will not be stopping, hence it will keep moving following the waveform.  During the constant incline, except for long exposures, the effects of the movement are outweighed by the increased performance.  However in some sections of the waveform this will generate noise and unwanted artifacts which can be avoided by dropping any frame that does not line up with the linear part of the piezo waveform.
This can be easily seen in the second section of the volumetric widget, where the waveform and camera frames are plotted.  The camera impulses are also stretched to match the length of the exposure time, this allows the user to intuitively see whether there may be overlapping frames when volume rate and exposure time are not matched correctly (see fig).

```{attention}
If you experience de-focusing when moving from planar mode (or calibration) to the volumetric mode it may be due to an imprecise calibration of the piezo inside the configuration file. 
To check, make sure that the value you write in the piezo is then the acqual value the piezo reads using an oscilloscope connected to the NI board
```
