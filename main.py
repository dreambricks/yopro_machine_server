from webserver import ThreadedHTTPServer, PyServer
from serverdata import ServerData, VendingMachineState
from arduino_controller import ArduinoControllerThread


def start_arduino_thread():
    # start the hand movement thread
    thread1 = ArduinoControllerThread(1, "ArduinoController")
    thread1.start()

    return thread1


def run_webserver(addr="localhost", port=80):
    sd = ServerData()
    ard_thread = start_arduino_thread()

    server_address = (addr, port)
    httpd = ThreadedHTTPServer(server_address, PyServer)

    try:
        print(f"Starting httpd server on {addr}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        sd.state = VendingMachineState.EXIT
        ard_thread.join()

    httpd.server_close()
    print("Server stopped.")


def main():
    run_webserver()


if __name__ == "__main__":
    main()
