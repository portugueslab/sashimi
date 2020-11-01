from sashimi.hardware.cameras.hamamatsu.interface import HamamatsuCamera
import napari

hcam = HamamatsuCamera(camera_id=0, sensor_resolution=(2048, 2048))

hcam.set_property_value("subarray_mode", "ON")
hcam.start_acquisition()
print(hcam.get_property_value("binning"))


params = [
    "internal_frame_rate",
    "timing_readout_time",
    "exposure_time",
    "image_height",
    "image_width",
    "image_framebytes",
    "buffer_framebytes",
    "buffer_rowbytes",
    "buffer_top_offset_bytes",
    "subarray_hsize",
    "subarray_vsize",
    "binning",
]

# for param in params:
#     print(param, (hcam.get_property_value(param)))

frames = hcam.get_frames()

print([f.shape for f in frames])
f0 = frames[0]

hcam.stop_acquistion()
print(hcam.get_property_value("subarray_hsize"))
hcam.set_property_value("binning", "4x4")
print(hcam.get_property_value("subarray_hsize"))
print(hcam.get_property_value("binning"))

# hcam.frame_shape = (512, 512)

hcam.start_acquisition()

frames = hcam.get_frames()
print([f.shape for f in frames])

hcam.shutdown()

with napari.gui_qt():
    napari.view_image(f0)
    napari.view_image(frames[0])

