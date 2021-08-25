from flask import Flask
from waitress import serve

import agent.app as app
import sys
if __name__ == "__main__":

    NodeFlask = app.NodeFlask
    port = int(sys.argv[2])
    serve(NodeFlask, host='0.0.0.0', port=port)
