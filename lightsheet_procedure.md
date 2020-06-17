## First things

1.  Turn on the IR light ( 1/3 power), laser (key clockwise), piezo
    (under the anti-vibration table), CMOS camera (on top)

2.  Lift the objective

3.  Carefully put in the imaging chamber under the objective with objective
    manipulator. If you don't know which one it is, ask someone before
    making a guess.

4.  In the behaviour computer launch your StytraConfig protocol in PyCharm (ctrl + shift + F10)

5.  If it was not well-centred in embedding, using the camera on the
    behaviour computer, align the dish under the objective and move the
    paper window
    
## Calibration mode

1.  Open lightsheet control software. For that, open lightsheet_take_two 
    with PyCharm and run ```__init__.py```. The GUI will pop-up after some
    seconds. There are four modes available: Pause, calibration, planar and
    volumetric.

2.  Go to calibration tab to determine the piezo/galvo relation and the 
    extent of scanning for both lateral and frontal beams. Turn on the
    laser at a low current (min 23 mA) with a small lateral range
    of the lateral beam (block the frontal) and move the stage in X and Z
    (__use only stage manipulators__) to locate the laser beam over the fish 
    head by eye to the best of your ability - try not to hit the eyes
    (i.e. hit something a bit more caudal like the swimming bladder
    which also shows autofluorescence). You can turn off the laser now.

3.  With the room lights on, manually focus the objective with objective
    manipulator and find the eyes/silhouette of the fish by moving the stage
    with its X and Y manipulators. Now turn off room lights.

4. Turn on the laser again. Play with the piezo and galvo(s)
    positions until you see the most focused signal. Set lateral and frontal
    beam ranges to that that is inside the FOV but does not burn the eyes.
    If you want to do volumetric imaging continue here, else jump to planar
    mode section.
    
5. Now, add points to calibration by finding piezo and galvo(s)
    positions where you see the most focused signal. Add a point 
    by pressing "+". Repeat this a total of 3 times over the
    span of your desired recorded volume. If you added a point by mistake,
    press "-" to delete the last point added to calibration.
    
## Volumetric mode

** __note: If the piezo impulse-response seems funny or unexpected switch back to calibration tab, then again to volumetric
tab. This is a little bug -- which will be solved soon__ 

1. Once you are happy with the calibration points, move on to either volumetric
    or planar acquisition mode. Restrict the ROI in the display
    to only contain the area of interest by drawing a rectangle and
    clicking "set ROI". If you are unhappy with your ROI you can always go
    back to the full-size mode by pressing "set full-size frame". Use the
    precision slider to establish the volume of interest. You can leave the camera running over all planes
    by selecting "-1" in the selected plane for viewing or else you can stop at
    a plane by setting it to that number. If you are unhappy with your calibration
    you can always go back to the calibration tab, delete the calibration points
    and start over. By now you may also want to switch to lower exposure (4-10 ms)
    maintaining the binning at 2x2. You can also decrease the file size by binning 4x4
    at the cost of losing spatial resolution, but maybe gaining in SNR (however this is 
    unadvised unless you have a good reason for doing this).

2. Set the number of planes you want to divide your volume into. Pay attention to
    inter-plane distance and triggered frame rate -- this last one should be close to
    what you expect! Otherwise camera might be lagging behind (maybe exposure is too
    high?). Finally, fine-tune the piezo range by checking the last and first planes.
    The displayed values are in micrometers, so you can calculate the axial extent of the recorded volume.
    You might want to discard the last few ventral planes to account for the piezo 
    impulse-response, which you can see in the impulse-reponse graph widget. Keep only
    those in the linear range (e.g. discard most 3 ventral planes for 33 planes 200 um acquisition).
    
## Planar mode


## Preparing experiment

1. You might want to save the current configuration to set it up faster
    for a similar experiment or for the next subject. Press "save settings".
    You can load them next time at any point by pressing "load settings".
    
2. Select the saving folder in one of the HDD data drives. Chunk size is the number
    of frames in each .H5 file (data is saved directly as a split dataset). Check that there is
    enough space in the drive to save the whole experiment.
    
3. Remember to put the selected plane back to -1 so that acquisition runs over
    all the planes!

## Behaviour computer

1.  Ensure the stimulus display window is properly set and dimensions
    are properly calibrated

2.  If tail tracking is required, turn on IR light (~1/2 power) and
    set the correct tail location

3.  Set/update the correct metadata and experiment parameters. Ensure Stytra is connected to experiment database (red is
    not connected! Click to connect if it is red). Set the saving location or use the one by default (desktop).

4.  VERY IMPORTANT!! Check that both machines (behaviour and acquisition) are connected to the network.

5.  Check the box "Wait for scope".

## Starting the experiment

1.  In Stytra press start protocol.

3.  In the lightsheet control GUI press prepare experiment (after ensuring everything is ok!)

5.  Press "start experiment" in the lightsheet control GUI.

## After the experiment

1.  Move files to the workstation (J:/_shared/experiments/experimentXX/versionXX). The folder should be
    fish_id/session_id/, and it should contain the .H5 acquisition files, behavioural logs and data and
    metadata for the experiment and for the scope, along with a json file for the .H5 split dataset with no
    subfolders (this standardisation is important for analysis pipelines)

2.  Turn off IR light, laser key (anti-clockwise), piezo, CMOS camera

3.  Lift the objective, remove the fish

4.  Clean the objective with isopropanol on objective-grade tissues, no
    rubbing. If you don't know how to do this step, just don't do it. It
    is not strictly necessary.

## Troubleshooting & various tips

**Sources of blurriness:**

1.  Dirty glass cover slips

2.  Old agarose (always use fresh agarose!)

3.  Cutting away from the head

4.  Dirty objective

5.  Floating pieces of agarose/dirty fish water

6.  If all the above fails, likely the alignment of the microscope
