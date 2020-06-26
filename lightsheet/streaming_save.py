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
import yagmail
import time
import os
from math import ceil


@dataclass
class SavingParameters:
    output_dir: Path = r"F:/Vilim"
    n_t: int = 10000
    n_planes: int = 1
    n_volumes: int = 10000
    chunk_size: int = 1000
    notification_email: str = "None"
    framerate: float = 1


@dataclass
class SavingStatus:
    target_params: SavingParameters
    i_in_chunk: int = 0
    i_volume: int = 0
    i_chunk: int = 0
    i_frame: int = 0


class StackSaver(Process):
    def __init__(self, stop_event, duration_queue, max_queue_size=2000):
        super().__init__()
        self.stop_event = stop_event
        self.save_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.writer_queue = ArrayQueue(max_mbytes=max_queue_size)
        self.saving_signal = Event()
        self.saver_stopped_signal = Event()
        self.saving_parameter_queue = Queue()
        self.save_parameters: Optional[SavingParameters] = SavingParameters()
        self.i_in_chunk = 0
        self.i_chunk = 0
        self.i_plane = 0
        self.i_frame = 0
        self.i_volume = 0
        self.current_data = None
        self.saved_status_queue = Queue()
        self.saved_status_queue_2 = Queue()
        self.frame_shape = None
        self.dtype = np.uint16
        self.duration_queue = duration_queue

    def run(self):
        while not self.stop_event.is_set():
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
        self.i_frame = 0
        self.i_in_chunk = 0
        self.i_chunk = 0
        self.i_plane = 0
        self.i_volume = 0
        self.current_data = None
        n_total = self.save_parameters.n_t
        while (
                self.i_frame < n_total
                and self.saving_signal.is_set()
                and not self.stop_event.is_set()
        ):
            self.receive_save_parameters()
            try:
                n_total = self.save_parameters.n_t
            except Empty:
                pass
            try:
                frame = self.save_queue.get(timeout=0.01)
                self.fill_dataset(frame)
                self.i_frame += 1
            except Empty:
                pass

        if self.i_frame > 0:
            self.send_to_writer()
            self.update_saved_status_queue()
            self.finalize_dataset()
            self.current_data = None
            if self.save_parameters.notification_email != "None":
                self.send_email_end()

        while not self.saver_stopped_signal.is_set():
            time.sleep(0.001)
        self.saving_signal.clear()
        self.save_parameters = None

    def send_email_end(self):
        sender_email = "fishgitbot@gmail.com"  # TODO this should go to thecolonel
        # TODO: Send email every x minutes with image like in 2P
        receiver_email = self.save_parameters.notification_email
        subject = "Your lightsheet experiment is complete"
        sender_password = "think_clear2020"

        yag = yagmail.SMTP(user=sender_email, password=sender_password)

        body = [
            "Hey!",
            "\n",
            "Your lightsheet experiment has completed and was a success! Come pick up your little fish",
            "\n"
            "Always yours,",
            "fishgitbot"
        ]

        yag.send(
            to=receiver_email,
            subject=subject,
            contents=body,
            attachments=r"icons/main_icon.png"
        )

    def cast(self, frame):
        """
        Conversion into a format appropriate for saving
        """
        return frame

    def fill_dataset(self, frame):
        if self.current_data is None:
            self.current_data = np.empty(
                (self.save_parameters.chunk_size, self.save_parameters.n_planes, *frame.shape),
                dtype=self.dtype
            )

        self.current_data[self.i_in_chunk, self.i_plane, :, :] = self.cast(frame)

        self.i_plane += 1
        if self.i_plane >= self.save_parameters.n_planes:
            self.i_plane = 0
            self.i_in_chunk += 1
            self.i_volume += 1
            self.update_saved_status_queue()

        if self.i_in_chunk == self.save_parameters.chunk_size:
            self.send_to_writer()

    def update_saved_status_queue(self):
        self.saved_status_queue.put(
            SavingStatus(
                target_params=self.save_parameters,
                i_in_chunk=self.i_in_chunk,
                i_chunk=self.i_chunk,
                i_volume=self.i_volume,
                i_frame=self.i_frame
            )
        )

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
                        self.save_parameters.n_t // self.current_data.shape[1],
                        *self.current_data.shape[1:],
                    ),
                    "shape_block": (
                        self.save_parameters.chunk_size,
                        *self.current_data.shape[1:],
                    ),
                    "crop_start": [0, 0, 0, 0],
                    "crop_end": [0, 0, 0, 0],
                    "padding": [0, 0, 0, 0],
                },
                f,
            )

    def receive_save_parameters(self):
        try:
            self.save_parameters = self.saving_parameter_queue.get(timeout=0.001)
        except Empty:
            pass
        try:
            new_duration = self.duration_queue.get(timeout=0.001)
            self.save_parameters.n_t = int(np.ceil(self.save_parameters.framerate * new_duration))
            self.save_parameters.n_volumes = int(np.ceil(self.save_parameters.n_t / self.save_parameters.n_planes))
        except Empty:
            pass

    def send_to_writer(self):
        self.writer_queue.put(self.current_data[:self.i_in_chunk, :, :, :])
        self.saved_status_queue_2.put(
            SavingStatus(
                target_params=self.save_parameters,
                i_chunk=self.i_chunk,
                i_frame=self.i_frame
            )
        )
        self.i_chunk += 1


class DiskWriter(Process):
    def __init__(self, stop_event, saving_signal, saved_status_queue, writer_queue, saver_stopped_signal):
        super().__init__()
        self.stop_event = stop_event
        self.saving_signal = saving_signal
        self.saver_stopped_signal = saver_stopped_signal
        self.saved_status = saved_status_queue
        self.writer_queue = writer_queue
        self.chunk = None
        self.saved_status = None
        self.bytes_chunk = 0
        self.chunk_gb_queue = Queue()

    def run(self):
        while not self.stop_event.is_set():
            if self.saving_signal.is_set():
                self.receive_chunk()

    def receive_chunk(self):
        try:
            self.chunk = self.writer_queue.get(timeout=0.001)
        except Empty:
            pass
        try:
            new_status = self.saved_status.get(timeout=0.001)
            self.saved_status = new_status
        except Empty:
            pass

    def save_chunk(self):
        if self.chunk is not None:
            fl.save(
                Path(self.saved_status.target_params.output_dir)
                / "original/{:04d}.h5".format(self.saved_status.i_chunk),
                {"stack_4D": self.chunk},
                compression="blosc",
            )
            self.chunk = None
        if self.saved_status.i_chunk == 0:
            self.bytes_chunk = os.stat(
                Path(self.saved_status.target_params.output_dir)
                / "original/{:04d}.h5".format(self.saved_status.i_chunk)
            ).st_size
            n_chunks = ceil(self.saved_status.target_params.n_volumes / self.saved_status.target_params.chunk_size)
            experiment_gb = self.bytes_chunk * n_chunks / 1073741824
            self.chunk_gb_queue.put(experiment_gb)
        if self.saved_status.i_frame == self.saved_status.taget_params.n_total:
            self.saver_stopped_signal.set()
