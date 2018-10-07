#!/usr/bin/env python

import argparse
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class StaticImageHttpServer(HTTPServer):

    def __init__(self, *args, **kwargs):
        super(StaticImageHttpServer, self).__init__(*args, **kwargs)
        self.image = None
        self.image_lock = threading.Lock()

    def get_image(self):
        with self.image_lock:
            return self.image

    def set_image(self, image):
        with self.image_lock:
            self.image = image


class ImageRequestHandler(BaseHTTPRequestHandler):

    # TODO: add automatic page refresh

    page = '<html><body align="center"><img src="image.jpg" alt="Image" /></body></html>'

    def do_GET(self):
        if self.path == '/image.jpg':
            self.serve_image()
        else:
            self.serve_page()
        return

    def serve_page(self):
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(self.page, "utf8"))

        return

    def serve_image(self):
        im = self.server.get_image()

        if not im:
            self.send_error(404)
            return

        image_data = self.read_image(im)
        if not image_data:
            self.send_error(404)
            return

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'image/jpeg')
        self.end_headers()

        self.wfile.write(image_data)
        return

    def read_image(self, image):
        try:
            with open(image, 'rb') as file:
                return file.read()
        except FileNotFoundError:
            self.log_error('Failed to read image file: {}'.format(image))
            return None


class WebServer:

    def __init__(self, handler=ImageRequestHandler):
        self.handler = handler
        self.httpd = None
        self.thread = None

    def start(self, port):
        logging.info('Starting web server at port {port}'.format(port=port))
        self.httpd = StaticImageHttpServer(('', port), self.handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.start()

    def stop(self):
        if self.httpd:
            logging.info('Stopping web server')
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

        if self.thread:
            logging.debug('Joining on server thread')
            self.thread.join()
            self.thread = None

    def update_image(self, image):
        if self.httpd:
            logging.debug('Updating web server image to {}'.format(image))
            self.httpd.set_image(image)
        else:
            logging.debug('Image not updated, web server not running')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=None, type=int, help='Run webserver on this port')

    options = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    web_server = WebServer()
    if options.port:
        web_server.start(options.port)
    else:
        logging.info('No web server specified - images will not be published')

    web_server.update_image('/home/sfx/irtest.jpg')

    try:
        # TODO: add camera related stuff here
        while 1:
            time.sleep(1)

    except KeyboardInterrupt:
        if web_server:
            web_server.stop()


if __name__ == '__main__':
    main()