# Microscope Hardware

Sashimi was built for a two-beam digitally-scanning lightsheet microscope used for brain imaging zebrafish larvae and drosophila.

## Conceptual Schema

### Top view

![topview](../images/hw_top-Page-2.drawio.png)

### Side view

![sideview](../images/hw_top-Page-3.drawio.png)

## Digitally Scanned Lightsheet Microscopy (DLSM)

Light sheet fluorescence microscopy (LSFM) is a fluorescence microscopy technique that uses a light-sheet to illuminate a fluorescent sample.
In a digitally scanned lightsheet microscope the lightsheet is virtually created by moving  a laser beam horizontally hundreds of times per second.
The overall simplified structure consists of a laser beam, which is split in two separate beams, sent to multiple mirrors until it's redirected to two galvanometric mirrors.
Each side has 2 galvanometric mirrors which can move the beam horizontally and vertically.
The horizontal motion generates the lightsheet, while the vertical one moves the lightsheet across the sample.
After the galvanometric mirrors, the beam of light goes through multiple lenses to collimate and expand the beam, and finally passes through an objective.  The point where the waist of the beam is thinnest is the optimal location at which to construct the imaging path.
It’s important to note that both beams should meet and align where the waist is thinnest.
The imaging path comprises a camera, tube lens, imaging objective, piezo, and a filter.
The camera, tube lens and objective must be at a constant distance between each other, and are therefore mounted on a fixed railing system that can be moved as a whole piece.
The GFP filter ensures that only the photons at the right wavelength are collected by the camera, and therefore filters out any unwanted noise.
The piezo allows the object to move vertically to keep the focus on the sample while doing volumetric imaging.
The main components are camera, galvanometric mirrors, laser beam, lenses, objective, piezo-objective positioner, GFP filter, stage.

### Camera

The camera we used for our implementation is the ORCA Flash 4 from Hamamatsu.  It allows for fast imaging acquisition, in combination with a large sensor that can acquire large field images. Depending on the frame size the camera can achieve various frequencies (see table).

### Galvanometric mirrors

Galvanometric mirrors are used to move the laser beam both vertically and horizontally.
The horizontal fast motion (200-1000Hz) generates a lightsheet, while the slow vertical motion (1-20Hz) allows for volumetric imaging.  
Being a two-beam lightsheet, there are two sides (frontal and lateral) from which the sample is illuminated.
Therefore, there are 4 galvanometric mirrors, two of which are bigger in size and are used for slower motion, and the other two are smaller and move at faster speeds.  Each side has one of the kind, the bigger one for vertical motion and the smaller for horizontal motion.

### Laser


````{warning}
 UNDER CONSTRUCTION
 ```
                                ___
                        /======/   
                ____    //      \___
                | \\  //           
        |_______|__|_//            
        _L_____________\o           
      __(CCCCCCCCCCCCCC)____________

```
````


### Lenses

The lenses used are specific to the setup and depend on the distances the light needs to travel.  In our setup each excitation path (2 laser beams) has one scan lens and a tube lens. With the addition of another tube lens for the acquisition path.

### Objectives

The setup has a total of 3 objectives, 2 for the excitation path and one for the acquisition path:

- 4x 0.28 NA Objective (for excitation).
- 20x Objective (for collection).

### Piezo-objective Positioner

The piezoelectric objective positioner is a component attached to the acquisition objective that moves vertically with a range of 600 micrometers.  The piezo must be fast enough to be synched with the vertical galvanometric mirrors so that during the acquisition the distance between the objective and the light sheet does not change, and , thus, keeping the correct focus distance.

### GFP filter

The emission filter simply filters out light coming at it with wavelengths outside of its working range. This allows to filter out any unwanted light and to keep only the photons coming from the illuminated sample.

### Stage

To move the sample precisely in the optimal location we use a 3D moving stage.  This allows for precise manual adjustment in x,y,z.

### NI Board

The Ni board is a multifunction input/output device with multiple channels that allows for independent triggering of single channels as well as synched output for multiple devices (e.g. the piezo and galvos waveforms).
It is used to control the galvanometric mirrors, the piezo-objective positioner, and the camera trigger.

## Parts list


````{warning}
 UNDER CONSTRUCTION
 ```
                                ___
                        /======/   
                ____    //      \___
                | \\  //           
        |_______|__|_//            
        _L_____________\o           
      __(CCCCCCCCCCCCCC)____________

```
````
