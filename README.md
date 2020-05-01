# Portugues lab lighthsheet control software

Reworked with knowledge acquired in the past 3 years.

The lightsheet software has two modes: setup and running.
In the setup mode two things need to be determined: 
1) the ranges and frequencies for lateral scanning
2) the piezo-galvo relation

In the running mode the estimated piezo-galvo relation has to be applied.

# TODO
 - [X] Camera triggering
 - [X] Stytra communication
 - [X] Settings saving and management
 - [X] Fix non-divisible frame rate bugs
 - [X] Single-plane experiments
 - [ ] Make the volumetric scanning more deterministic (so that one does not need to switch out and back in to get it to work)
 - [ ] Better calibration point management
 - [ ] While calibrating, when moving the piezo, take into account the current calibration and pre-move the galvos (maybe start with the default amplitude)
 - [ ] Camera display
 - [ ] Break up scanning.py
 - [ ] Make the GUI nice