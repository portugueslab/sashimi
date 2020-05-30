from multiprocessing import Process, Event, Queue
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from queue import Empty
import flammkuchen as fl
import numpy as np
import shutil
import json
from arrayqueues.shared_arrays import ArrayQueue
from threading import Thread


@dataclass
class SavingParameters:
    output_dir: Path = r"F:/Vilim"
    n_t: int = 1000
    chunk_size: int = 1000


@dataclass
class SavingStatus:
    target_params: SavingParameters
    i_t: int = 0
    i_chunk: int = 0


class StackSaver(Thread):
    def __init__(self, stop_signal, max_queue_size=1000):
        super().__init__()
        self.stop_signal = stop_signal
        self.save_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.saving_signal = Event()
        self.saving = False
        self.saving_parameter_queue = Queue()
        self.save_parameters: Optional[SavingParameters] = SavingParameters()
        self.i_in_chunk = 0
        self.i_chunk = 0
        self.current_data = None
        self.saved_status_queue = Queue()
        self.dtype = np.uint16

    def run(self):
        while not self.stop_signal.is_set():
            if self.saving_signal.is_set() and self.save_parameters is not None:
                self.save_loop()
            else:
                self.receive_save_parameters()

    def save_loop(self):
        # remove files if some are found at the save location
        Path(self.save_parameters.output_dir).mkdir(parents=True, exist_ok=True)
        if (
                Path(self.save_parameters.output_dir) / "original" / "stack_metadata.json"
        ).is_file():
            shutil.rmtree(Path(self.save_parameters.output_dir) / "original")

        (Path(self.save_parameters.output_dir) / "original").mkdir(
            parents=True, exist_ok=True
        )
        i_received = 0
        self.i_in_chunk = 0
        self.i_chunk = 0
        # FIXME: 1024 x 1024 is only for 2x2 binning. Extract info from camera param Queue
        self.current_data = np.empty(
            (self.save_parameters.n_t, 1, 1024, 1024),
            dtype=self.dtype
        )
        n_total = self.save_parameters.n_t
        while (
                i_received < n_total
                and self.saving_signal.is_set()
                and not self.stop_signal.is_set()
        ):
            #self.receive_save_parameters()
            #try:
            #    n_total = self.save_parameters.n_t
            #except Empty:
            #    pass
            try:
                frame = self.save_queue.get(timeout=0.01)
                self.fill_dataset(frame)
                i_received += 1
            except Empty:
                pass

        if self.i_chunk > 0:
            self.finalize_dataset()

        self.saving_signal.clear()
        self.save_parameters = None

    def cast(self, frame):
        """
        Conversion into a format appropriate for saving
        """
        return frame

    def fill_dataset(self, frame):
        self.current_data[self.i_in_chunk, 0, :] = self.cast(frame)
        self.i_in_chunk += 1
        self.saved_status_queue.put(
            SavingStatus(
                target_params=self.save_parameters,
                i_t=self.i_in_chunk,
                i_chunk=self.i_chunk,
            )
        )
        if self.i_in_chunk == self.save_parameters.chunk_size:
            self.save_chunk()

    def finalize_dataset(self):
        with open(
            (
                Path(self.save_parameters.output_dir)
                / "original"
                / "stack_metadata.json"
            ),
            "w",
        ) as f:
            json.dump(
                {
                    "shape_full": (
                        self.save_parameters.n_t,
                        self.i_chunk,
                        *self.current_data.shape[2:],
                    ),
                    "shape_block": (
                        self.save_parameters.chunk_size,
                        1,
                        *self.current_data.shape[2:],
                    ),
                    "crop_start": [0, 0, 0, 0],
                    "crop_end": [0, 0, 0, 0],
                    "padding": [0, 0, 0, 0],
                },
                f,
            )

    def save_chunk(self):
        fl.save(
            Path(self.save_parameters.output_dir)
            / "original/{:04d}.h5".format(self.i_chunk),
            {"stack_4D": self.current_data},
            compression="blosc",
        )
        self.i_in_chunk = 0
        self.i_chunk += 1

    def receive_save_parameters(self):
        try:
            self.save_parameters = self.saving_parameter_queue.get(timeout=0.001)
        except Empty:
            pass
