from lightsheet.hardware.hamamatsu_camera import HamamatsuCamera
import pyqtgraph as pg
from time import sleep

from PyQt5.QtWidgets import QApplication, QWidget

if __name__ == "__main__":

    app = QApplication([])

    cam = HamamatsuCamera(camera_id=0)
    print(cam.getModelInfo(0))
    cam.exposure = 0.005
    print("Cam exposure is", cam.exposure)

    cam.setACQMode("fixed_length", 5)
    cam.startAcquisition()

    sleep(2)

    fr, dims = cam.getFrames()

    print("Got x frames ", len(fr))

    wid = pg.ImageView()
    wid.setImage(fr[0].np_array.reshape(dims))
    cam.stopAcquisition()

    wid.show()
    app.exec()