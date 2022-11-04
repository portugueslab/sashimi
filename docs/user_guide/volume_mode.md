# Volume mode

The volumetric mode (see the [fig](sashimi-mode_vol)) is the core function of the software since it allows for fast volume acquisition. It can be divided into two sections, the first one allows for the input of various settings, while the second one displays the waveform of the piezo vs lateral galvo with the camera triggers overlaid on top. The setting that can be input into the software are the following:

- A scanning range from ventral to rostral piezo position.
- A volume rate per second.
- The number of planes to acquire for each volume.
- The number of planes to skip at the beginning of each volume.
- The number of planes to skip at the end of each volume.
- A button to select whether to pause the live view after the experiment.

```{figure} ../images/mode_vol.png
---
width: 350px
name: sashimi-mode_vol
---
Sashimi volume mode GUI
```
  
To understand why it may be necessary to drop some planes at the beginning and end of the volume acquisition is important to understand how the volumetric scanner works. During the volumetric scanning the piezo keeps moving following a waveform (see the white line in the [fig](sashimi-mode_vol)), and the galvos follow it based on the calibration. During the acquisition of each frame, the piezo will not be stopping, hence it will keep moving following the waveform. During the constant incline, except for long exposures, the effects of the movement are outweighed by the increased performance.

However, in some sections of the waveform, this will generate noise and unwanted artifacts which can be avoided by dropping any frame that does not line up with the linear part of the piezo waveform. This can be easily seen in the second section of the volumetric widget, where the waveform and camera frames are plotted.

The camera impulses are also stretched to match the length of the exposure time, this allows the user to intuitively see whether there may be overlapping frames when volume rate and exposure time are not matched correctly (see the shaded regions in the [fig](sashimi-mode_vol2)). Moreover, in the status bar, at the bottom of the GUI, the software will automatically print the current frame-rate and highlight it in red if the current frame-rate isn’t high enough. Disregarding these warnings may impair the quality of the experiment.

```{figure} ../images/volum2.png
---
width: 250px
name: sashimi-mode_vol2
---
Sashimi frames overlapping
```
