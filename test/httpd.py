# Copyright © 2014 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import http.server
import os
import ssl
import sys
import threading

page_event = threading.Event()

class RequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello world!')
        self.wfile.flush()
        page_event.set()

    def log_request(self, *args, **kwargs):
        pass

class HTTPServer(http.server.HTTPServer):

    def handle_error(self, request, client_address):
        exc_type = sys.exc_info()[0]
        if issubclass(exc_type, ssl.SSLError):
            # SSL errors are expected and boring.
            return
        return super().handle_error(request, client_address)

def run():
    httpd = HTTPServer(('127.0.0.1', 0), RequestHandler)
    certfile = os.path.dirname(__file__) + '/httpd.pem'
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        certfile=certfile,
        server_side=True
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    httpd_thread.start()
    host, port = httpd.socket.getsockname()
    url = 'https://{host}:{port}/'.format(host=host, port=port)
    return url

# vim:ts=4 sts=4 sw=4 et
