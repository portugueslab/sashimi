from sashimi.hardware.cameras.hamamatsu.interface import HamamatsuCamera
import napari
import time

hcam = HamamatsuCamera(camera_id=0, sensor_resolution=(2048, 2048))

hcam.start_acquisition()

hcam.get_frames()

hcam.stop_acquisition()



print("frames: ", len(hcam.get_frames()))

hcam.set_property_value("subarray_mode", "ON")
hcam.set_property_value("binning", "2x2")
hcam.set_property_value("subarray_hsize", 100)
hcam.set_property_value("subarray_vsize", 100)

print("binning", hcam.get_property_value("binning"))
print("\n this", hcam.get_property_value("image_height"))

hcam.shutdown()
