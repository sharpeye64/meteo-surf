"""Serveur local des fichiers du site (web/), avec l en-tete CORS comme GitHub Pages : donne les donnees a l appli pendant les tests.
Usage : python tools/serveur_local.py web 8766"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class H(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


root, port = sys.argv[1], int(sys.argv[2])
ThreadingHTTPServer(("0.0.0.0", port), partial(H, directory=root)).serve_forever()
