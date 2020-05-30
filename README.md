# Portugues lab lighthsheet control software

Reworked with knowledge acquired in the past 3 years.

The lightsheet software has four modes: pause, calibration, planar and volumetric.
In the calibration mode two things need to be determined:

1) the ranges and frequencies for lateral scanning
2) the piezo-galvo relation

In the planar or volumetric adquisition mode the estimated piezo-galvo relation is applied. In the later, the piezo range has to be determined. NB. -1 in I freeze frees the camera to run over all planes. Any other number freezer the camera over that particular plane. "N skip start" and "N skip end" skip ventral and dorsal planes, respectively
