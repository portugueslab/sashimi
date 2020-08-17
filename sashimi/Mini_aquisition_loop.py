if __name__ == "__main__":

    from camera import CameraProcess, CamParameters, CameraMode, TriggerMode
    from streaming_save_OLD import StackSaver
    from multiprocessing import Queue, Event
    import time
    import nidaqmx


    def write_sample():
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan("Dev2/ao1", min_val=0, max_val=5)
            task.write(5)

    finished_event = Event()
    save_queue = Queue()
    camera_process = CameraProcess()
    cam_parameters = CamParameters()
    saver = StackSaver(stop_event=finished_event, save_queue=save_queue)#, duration_queue=self.stytra_comm.duration_queue)
    saver.start()
    camera_process.start()
    start = time.time()
    elapsed = 0
    i_frames = 0
    time.sleep(3)
    # cam_parameters.camera_mode = CameraMode.TRIGGERED
    # cam_parameters.trigger_mode = TriggerMode.EXTERNAL_TRIGGER

    cam_parameters.camera_mode = CameraMode.PREVIEW
    cam_parameters.trigger_mode = TriggerMode.FREE

    cam_parameters.exposure_time = 10
    camera_process.parameter_queue.put(cam_parameters)
    time.sleep(1)
    write_sample()
    while elapsed < 10:
        saver.saving_signal.set()
        frame = camera_process.image_queue.get()
        # frame_rate = camera_process.triggered_frame_rate_queue.get()
        # print("frame rate ", frame_rate)
        save_queue.put(frame)

        if frame is not None:
            # print(frame[:10, 0])
            i_frames += 1
            print("Yay! We have: {}".format(i_frames))
        elapsed = time.time() - start

    finished_event.set()
    saver.join(timeout=10)
    camera_process.join(timeout=10)
    print ("aqisition done")


