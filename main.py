import mimetypes
import urllib.parse
import json
import logging
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread


CSS_DIR = Path('css/')
IMG_DIR = Path('images/')
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler"""
    def do_GET(self):
        """GET request handler"""
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html_file('templates/index.html')
            case '/message':
                self.send_html_file('templates/message.html')
            case '/message.html':
                self.send_html_file('templates/message.html')
            case _:
                css_file = CSS_DIR.joinpath(route.path[1:])
                img_file = IMG_DIR.joinpath(route.path[1:])
                if css_file.exists():
                    self.send_static(css_file)
                elif img_file.exists():
                    self.send_static(img_file)
                else:
                    self.send_html_file('templates/error.html', 404)


    def do_POST(self):
        """POST request handler"""
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()


    def send_html_file(self, filename, status=200):
        """Method send html file from http-server"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


    def send_static(self, filename, status=200):
        """Method send static resources from http-server"""
        self.send_response(status)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type','text/plain')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

def save_data_from_form(data):
    """Save data from form to json"""
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        json_dict = {}
        with open('storage/data.json', 'r', encoding='utf-8') as fh:
            json_dict = json.load(fh)
        json_dict[str(datetime.now())] = parse_dict
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(json_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host,port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, HttpHandler)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == '__main__':
    json_file = Path('storage/data.json')
    if not json_file.exists():
        Path('storage').mkdir(exist_ok=True)
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()

