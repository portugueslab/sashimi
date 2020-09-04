class AbstractScanInterface:
    def __init__(self, n_samples, conf, *args, **kwargs):
        self.n_samples = n_samples
        self.conf = conf

    def start(self):
        pass

    @property
    def z_piezo(self):
        return None

    @z_piezo.setter
    def z_piezo(self, waveform):
        pass

    @property
    def z_frontal(self):
        return None

    @z_frontal.setter
    def z_frontal(self, waveform):
        pass

    @property
    def z_lateral(self):
        return None

    @z_lateral.setter
    def z_lateral(self, waveform):
        pass

    @property
    def camera_trigger(self):
        return None

    @camera_trigger.setter
    def camera_trigger(self, waveform):
        pass

    @property
    def xy_frontal(self):
        return None

    @xy_frontal.setter
    def xy_frontal(self, waveform):
        pass

    @property
    def xy_lateral(self):
        return None

    @xy_lateral.setter
    def xy_lateral(self, waveform):
        pass

    def write(self):
        pass

    def read(self):
        pass


class AbstractScanConfigurator:
    def __init__(self, n_samples, conf):
        self.n_samples = n_samples
        self.conf = conf

    def __enter__(self):
        return AbstractScanInterface(self.n_samples, self.conf)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
