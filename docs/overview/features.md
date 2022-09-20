# Features

Thanks to the modular structure of Sashimi many hardware components can be switched easily by writing a custom python script to interface them with the software.
This allows to update the hardware and improve the performances over time.

## Core Functionality

### Calibration

Sashimi has an integrate calibration mode that allows the user to synch the sheet of light with the distance from the objective.
This is achieved by moving the sheet of light at multiple depths of the piezo (see hardware section for more informations on the specific components) and saving the points in which the image in the viewer is focused.
Once saved, the software will move the lightsheet of the correct amount for any given piezo to keep the sample in focus.

```{hint}
If you intend to image a certain range in z, make sure to acquire calibration points slightly beyond your working range.
```

```{hint}
More calibration points will allow the software to compute a more correct estimate.
```

### Planar Acquisition

```{warning}
This mode is still under construction and doesn't fully work yet!
```

Sashimi offers the possibility acquire images of only one plane with this specific mode.  The only input necessary is the position at which to place the objective, the software will use this position and the calibration point to move the sheet of light at the correct distance to keep the image in focus.

### Volumetric Acquisition

The core functionality of Sashimi is the volumetric acquisition.
It allows to select a range in the _z_ axis and acquire _n_ planes at a desired _volume_rate_.
Depending on the mazimum framerate of the camera, the exposure time, and the number of planes per volume, this mode allows for fast acquisition of entire volumes.  
With the hardware described in the next sections, a volume rate of 5Hz with 20 planes.

## Additional Features

### 3D Visualization

The Sashimi viewer is built around the [Napari](https://napari.org) viewer.  
This allows to easily visualize the data stream in real time, both as an overlay of multiple planes and as a 3D volume.
This allows the user to comprehensively inspect the data on the go, without the need to wait for the end of the acquisition.

### Drift Visualization

In the visualization widget there is an option to toggle on the drift visualization. This saves the first volume/plane of any acquisition and overlays it on top of the live feed.
This allows the user to see if the sample has moved during the acquisition.
This phenomenon can happen when a sample is embedded in agarose, but the widget can still be used as a useful comparison to the beginning of the acquisition.

### Noise Filtering

During the calibration phase it's possible to activate a noise filter which will compute the sensor average noise and subtract it to each frame acquired by the camera.
