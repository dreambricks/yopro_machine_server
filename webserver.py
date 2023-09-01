import socketserver
from datetime import datetime
import threading
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

import parameters as pm
from serverdata import ServerData, VendingMachineState
from loguser import LogUser

exit_flag = False
# semaphore = threading.Semaphore()
log_semaphore = threading.Semaphore()

# semaphore controlled variables
# log_file = None

last_sent_json = ''


# https://pymotw.com/2/SocketServer/index.html#module-SocketServer
class PyServer(SimpleHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server, directory=pm.DIRECTORY)

    def _set_headers(self, header_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", header_type)
        self.end_headers()

    def _html(self, message):
        """This just generates an HTML document that includes `message`
        in the body. Override, or re-write this do do more interesting stuff.

        """
        content = f"<html><body><h1>{message}</h1></body></html>"
        return content.encode("utf8")  # NOTE: must return a bytes object!

    def _json(self, points, end="N"):
        global last_sent_json
        content = '{ "points" : "%d", "end" : "%s" }' % (points, end)
        # return content.encode("utf8")  # NOTE: must return a bytes object!

        if content != last_sent_json:
            print('JSON: "%s"' % content)
            last_sent_json = content

        return bytes(content, "utf-8")

    def _send_img(self, path_to_image):
        self.send_response(200)
        self.send_header("Content-type", "image/png")
        # self.send_header("Content-length", img_size)
        self.end_headers()
        f = open(path_to_image, 'rb')
        self.wfile.write(f.read())
        f.close()

    def _send_msg(self, msg):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(self._html(msg))

    @staticmethod
    def url_match(url1, url2):
        l2 = len(url2)
        return url1[:l2] == url2

    @staticmethod
    def is_link_id_valid(path_link_id):
        sd = ServerData()
        print(f"checking if link <{path_link_id}> is valid")
        if path_link_id == pm.MASTER_ID:
            sd.link_id = path_link_id
            return True

        if path_link_id == pm.MASTER_ID_NON_BLOCKING:
            sd.link_id = path_link_id
            return True

        sd = ServerData()
        return sd.state == VendingMachineState.WAITING_FOR_START and path_link_id == sd.link_id

    @staticmethod
    def should_block_users():
        sd = ServerData()
        if sd.link_id == pm.MASTER_ID_NON_BLOCKING:
            return False

        return pm.BLOCK_USERS

    def do_GET(self):
        sd = ServerData()

        url_data = self.path.split('?')

        if url_data[0] == '/alive.html' or url_data[0] == '/alive':
            self._send_msg("YES")
            return

        elif url_data[0] == '/working':
            if sd.machine_on:
                self._send_msg("YES")
            else:
                self._send_msg("NO")
            return

        elif url_data[0] == '/count':
            self._send_msg(f"{sd.num_gifts}")
            return

        elif url_data[0] == '/' or url_data[0] == '/aceite.html':
            print("Returning Error")
            self.path = '/link_erro.html'

        elif url_data[0] == '/reset':
            sd.reset()
            self._send_msg("OK")
            return

        elif url_data[0] == '/dispensegift':
            print("Dispensing the gift")
            sd.dispense = True
            sd.reset()
            self._send_msg("OK")
            return

        print(self.path)
        return SimpleHTTPRequestHandler.do_GET(self)

    def log(self, add_msgs):
        global logfile
        message_parts = [
            'time=%s' % datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            'CLIENT VALUES:',
            'client_address=%s (%s)' % (self.client_address,
                                        self.address_string()),
            'command=%s' % self.command,
            'path=%s' % self.path,
            'request_version=%s' % self.request_version,
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        for msg in add_msgs:
            message_parts.append(msg)

        logmessage = '|'.join(message_parts)

        log_semaphore.acquire()
        logfile.write(logmessage)
        logfile.write("\n")
        logfile.flush()
        log_semaphore.release()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        post_data = post_data.decode("utf-8")
        self._set_headers()
        msg = "<html><body><h1>POST!</h1><pre>" + post_data + "</pre></body></html>"
        self.wfile.write(msg.encode("utf-8"))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def run(server_class=HTTPServer, handler_class=PyServer, addr="localhost", port=8000):
    global exit_flag
    server_address = (addr, port)
    # httpd = server_class(server_address, handler_class)
    httpd = ThreadedHTTPServer(server_address, handler_class)

    try:
        print(f"Starting httpd server on {addr}:{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        exit_flag = True
        # thread1.join()
        logfile.close()

    httpd.server_close()
    print("Server stopped.")


if __name__ == "__main__":
    global logfile
    logfile = open('logfile.txt', 'a')

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=80,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
