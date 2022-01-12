from flask import Flask
from waitress import serve

import agent.app as app
import sys
import logging
if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    NodeFlask = app.NodeFlask
    port = int(sys.argv[1])
    serve(NodeFlask, host='0.0.0.0', port=port)
