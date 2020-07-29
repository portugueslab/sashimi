import napari
import split_dataset
from PyQt5.QtWidgets import QApplication, QFileDialog


if __name__ == "__main__":
    # TODO make this run as an independent python program with the correct path argument
    # for the last stack on button press
    app = QApplication([])
    folder = QFileDialog.getExistingDirectory()
    ds = split_dataset.SplitDataset(folder)
    # TODO check opening as Dask
    napari.view_image(ds, contrast_limits=(0, 2000), multiscale=False, scale=[1, 7, 0.6, 0.6])
    app.exec_()