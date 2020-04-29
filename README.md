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
 - [ ] Settings saving and management
 - [ ] Fix non-divisible frame rate bugs
 - [ ] Single-plane experiments
 - [ ] Better calibration point management
 - [ ] Camera display
 - [ ] Break up scanning.py
 - [ ] Invstigate time shift calculation
 - [ ] Make the GUI nice