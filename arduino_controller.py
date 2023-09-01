import time
import os
import serial
from parameters import *
import threading
import pickle


from serverdata import ServerData, VendingMachineState


class ArduinoControllerThread(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.arduino = serial.Serial(port=ARDUINO_PORT, baudrate=ARDUINO_SPEED, timeout=.5)
        self.dispensers = VENDING_MACHINE_DISPENSERS_ID
        self.num_dispensers = len(self.dispensers)
        self.pkl_file = VENDING_MACHINE_PERSIST_FILENAME
        if os.path.isfile(self.pkl_file):
            with open(self.pkl_file, 'rb') as file:
                self.current_dispenser = pickle.load(file)
                self.dispensed = pickle.load(file)
        else:
            self.current_dispenser = 0
            self.dispensed = [0] * self.num_dispensers
            self.store()
        sd = ServerData()
        sd.num_gifts = self.num_left()

    def run(self):
        print("Starting " + self.name)
        self.pool_arduino()
        print("Exiting " + self.name)

    def pool_arduino(self):
        sd = ServerData()
        while sd.state != VendingMachineState.EXIT:
            if sd.dispense:
                print('dispense!')
                sd.dispense = False
                self.dispense()

            if self.arduino.in_waiting > 0:
                data = self.arduino.readline()
                if len(data) > 0:
                    if data == b'recharge\r\n':
                        print(f"received from arduino: <{data}>")
                        print("recharge")
                        self.refill()
                        sd.udp_sender.send("REFILL")
                    elif data == b'on\r\n' and sd.machine_on is False:
                        print("on")
                        sd.machine_on = True
                        sd.udp_sender.send("ON")
                    elif data == b'off\r\n' and sd.machine_on is True:
                        print("off")
                        sd.machine_on = False
                        sd.udp_sender.send("OFF")

            time.sleep(.05)
            #print('pool arduino', sd.dispense)

    def store(self):
        with open(self.pkl_file, 'wb') as file:
            pickle.dump(self.current_dispenser, file)
            pickle.dump(self.dispensed, file)

    def dispense(self):
        if self.dispensed[self.current_dispenser] >= VENDING_MACHINE_GIFTS_PER_DISPENSER:
            self.current_dispenser = (self.current_dispenser + 1) % self.num_dispensers

        self.send_vending_command(self.dispensers[self.current_dispenser])
        self.dispensed[self.current_dispenser] += 1
        self.store()
        sd = ServerData()
        sd.num_gifts = self.num_left()

    def send_vending_command(self, dispenser_id):
        dispenser_str = f"{dispenser_id}\n"
        print(dispenser_str)
        self.arduino.write(bytes(dispenser_str, 'utf-8'))
        time.sleep(0.05)
        #data = self.arduino.readline()
        #print(f"received from arduino: <{data}>")

    def refill(self):
        self.dispensed = [0] * self.num_dispensers
        self.store()
        sd = ServerData()
        sd.num_gifts = self.num_left()

    def num_dispensed(self):
        return sum(self.dispensed)

    def num_left(self):
        return self.num_dispensers * VENDING_MACHINE_GIFTS_PER_DISPENSER - self.num_dispensed()


def test_arduino():
    arduino = serial.Serial(port='COM44', baudrate=9600, timeout=.1)

    def write_read(x):
        arduino.write(bytes(f"{x}\n", 'utf-8'))
        time.sleep(0.05)
        data = arduino.readline()
        return data

    while True:
        num = input("Enter a number: ")  # Taking input from user
        value = write_read(num)
        print(value)  # printing the value


if __name__ == "__main__":
    sd = ServerData()

    #test_arduino()

    thread1 = ArduinoControllerThread(1, "ArduinoController")
    thread1.start()

    while True:
        num = input("Digite Enter")
        sd.dispense = True
        time.sleep(0.5)
        #print(sd.dispense)

