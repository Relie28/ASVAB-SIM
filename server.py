import http.server
import socketserver
import sys
import os

PORT = 8765
DIR  = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, directory=DIR, **kwargs)
        except OSError:
            pass  # iOS Safari drops pre-emptive connections — harmless

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.address_string(), fmt % args))

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    def handle_error(self, request, client_address):
        pass  # Silence dropped-connection tracebacks

print("  Serving on http://0.0.0.0:%d" % PORT)
try:
    with Server(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n  Server stopped.")
