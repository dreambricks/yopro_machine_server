import threading
from singleton import Singleton
from parameters import *
from udp_sender import UDPSender
from enum import Enum


class VendingMachineState(Enum):
    WAITING_FOR_START = 0
    RUNNING = 1
    EXIT = 2


class ServerData(metaclass=Singleton):

    def __init__(self):
        self.udp_sender = UDPSender(port=UDP_PORT)
        self.link_id = ''
        self.log_filename = 'logfile.txt'
        self.log_file = None
        self.log_semaphore = threading.Semaphore()
        self.dispense = False
        self.state = VendingMachineState.WAITING_FOR_START
        self.machine_on = True
        self.num_gifts = 0

    def reset(self):
        self.link_id = ''
        self.state = VendingMachineState.WAITING_FOR_START

    def __del__(self):
        if self.log_file is not None:
            self.log_file.close()

    def log(self, msg):
        if self.log_file is None:
            self.log_file = open(self.log_filename, 'w')

        self.log_file.write(msg)
