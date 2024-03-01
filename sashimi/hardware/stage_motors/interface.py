
class AbstractMotor:
    def __init__(self, serial_no, max_range=None):
        self.serial_no = serial_no
        self.max_range = max_range

    @property
    def get_id(self):
        pass

    def start(self):
        """
        Starts the motor
        """
        pass

    def stop(self):
        """
        Stops the motor
        """
        pass

    def home(self):
        """
        Homes the motor
        """
        pass

    @property
    def position(self):
        """

        Returns
        -------Motor position

        """
        pass

    def move_to(self, pos):
        """
        Moves the motor to desired position
        """
        pass