# Scanning

The scanning interface is the more complicated interface since it needs to handle the NI board which in turn controls the scanning hardware.
This interface outlines three simple methods to write and read samples from the board, as well as initialization of the board and start of the relevant tasks.
There are multiple properties that control different functionalities:

- `z_piezo`, reads and writes values to move the piezo vertically.
- `z_frontal`, reads and writes values to move the frontal laser vertically.
- `xy_frontal`, reads and writes values to move the frontal laser horizontally.
- `z_lateral`, reads and writes values to move the lateral laser vertically.
- `xy_lateral`, reads and writes values to move the lateral laser horizontally.
- `Camera_trigger`, triggers the acquisition of one frame.

The implementation of the scanning interfaces connects to the NI board and initialize three analog streams:

- `xy_writer`, which combines the frontal and lateral galvos moving the laser horizontally and outputs a waveform.
- `z_reader`, which reads the piezo position.
- `z_writer`, which combines the frontal and lateral galvos moving the laser vertically, the piezo and the camera trigger.   For each of them the output varies depending on the mode in which the software is.

Inside the config file, there’s a factor that allows applying a rescaling factor to the piezo. 

Another major part of the interface is the implementation of different scanning loops to continuously move the laser to form a sheet of light and move it in z synchronously with the piezo to keep the focus. There is a main class called ScanLoop which continuously checks whether the settings have changed, fills the input arrays with the appropriate waveform, writes this array on the NI board (through the scanning interface), reads the values from the NI board, and keeps a count of the current written and read samples. Two classes inherit from this main class:

- `PlanarScanLoop`
- `VolumetricScanLoop`

The main difference between the two is the way they fill the arrays responsible to control the vertical movement of Piezo and galvos. Inside the `planar loop`, there are two possible modes, one of which is used for calibration purposes and is completely manual. In this mode, the piezo is moved independently of the lateral and frontal vertical galvos. This allows for proper calibration of the focus plane for each specimen placed in the microscope. The other mode is synched and uses the linear function computed by the calibration to compute the appropriate value for each galvo, based on the piezo position. 

The `volumetric loop` instead writes a sawtooth waveform to the piezo, then reads the piezo position and computes the appropriate value to set the vertical galvos to. Given the desired framerate, it will also generate an array of impulses for the camera trigger, where the initial or final frame can be skipped depending on the waveform of the piezo. For ease of use, the waveform is shown in the GUI so that the user can decide how many frames to skip depending on the settings that they inserted, see [figure](sashimi-mode_vol) , where the white line represents the waveform.

**PlanarScanLoop** fill array method:

```python
def fill_arrays(self):
        # Fill the z values
        self.board.z_piezo = self.parameters.z.piezo
        if isinstance(self.parameters.z, ZManual):
            self.board.z_lateral = self.parameters.z.lateral
            self.board.z_frontal = self.parameters.z.frontal
        elif isinstance(self.parameters.z, ZSynced):
            self.board.z_lateral = calc_sync(
                self.parameters.z.piezo, self.parameters.z.lateral_sync
            )
            self.board.z_frontal = calc_sync(
                self.parameters.z.piezo, self.parameters.z.frontal_sync
            )
        super().fill_arrays()

        self.wait_signal.clear()
```

**VolumetricScanLoop** fill array method:

```python
def fill_arrays(self):
        super().fill_arrays()
        self.board.z_piezo = self.z_waveform.values(self.shifted_time)
        i_sample = self.i_sample % len(self.recorded_signal.buffer)

        if self.recorded_signal.is_complete():
        wave_part = self.recorded_signal.read(i_sample, self.n_samples)
        max_wave, min_wave = (np.max(wave_part), np.min(wave_part))
        if (
                -2 < calc_sync(min_wave, self.parameters.z.lateral_sync) < 2
                and -2 < calc_sync(max_wave, self.parameters.z.lateral_sync) < 2
        ):
                self.board.z_lateral = calc_sync(
                wave_part, self.parameters.z.lateral_sync
                )
        if (
                -2 < calc_sync(min_wave, self.parameters.z.frontal_sync) < 2
                and -2 < calc_sync(max_wave, self.parameters.z.frontal_sync) < 2
        ):
                self.board.z_frontal = calc_sync(
                wave_part, self.parameters.z.frontal_sync
                )
```
