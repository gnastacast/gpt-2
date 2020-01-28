#! /usr/bin/env python
import signal
# Flask
from flask import Flask, render_template, flash, request
from flask_socketio import SocketIO, emit
from collections import namedtuple

from ml_thread import MLThread

# Generates a flask app that lets you type to interact
def main():
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config['SECRET_KEY'] = '1-9840-813413491340-813-04'
    #turn the flask app into a socketio app
    socketio = SocketIO(app)

    thread = MLThread('Salem')
    def text_generated_cb(output_text):
        socketio.emit("generated_text", {"text": output_text, "color": False})
    thread.text_generated_cb = text_generated_cb

    @app.route("/")
    def speed_reader():
        return render_template('speed_reader.html')

    @app.route("/text_input")
    def text_input():
        return render_template('text_input.html')

    @socketio.on('connect')
    def test_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def test_disconnect():
        print('Client disconnected')

    @socketio.on('input_text')
    def input_text_cb(msg):
        thread.add_text(msg['text'])
        socketio.emit("generated_text", {"text": msg['text'], "color":True})
     
    def service_shutdown(signum, frame):
        print('Caught signal %d' % signum)
        raise Exception

    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    # Start the job threads
    try:
        thread.start()
        socketio.run(app)
    except Exception:
        func = request.environ.get('werkzeug.server.shutdown')
        func()
        thread.shutdown_flag.set()
        thread.join()

if __name__=='__main__':
    main()