#! /usr/bin/env python
import signal
# Flask
from flask import Flask, render_template, flash, request
from flask_socketio import SocketIO, emit
from collections import namedtuple

from ml_thread import MLThread
from udp_thread import UDPThread

# Generates a flask app that lets you type to interact
def main():
    # Create a flask app
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config['SECRET_KEY'] = '1-9840-813413491340-813-04'
    # Turn the flask app into a socketio app
    socketio = SocketIO(app)

    # Make threads
    udp_thread = UDPThread()
    ml_thread = MLThread('Salem', update_delay=5)

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
        ml_thread.add_text(msg['text'])
        socketio.emit("generated_text", {"text": msg['text'], "color":True, "delay":1, "instant":True})
     
    def service_shutdown(signum, frame):
        print('Caught signal %d' % signum)
        raise Exception

    # Set thread callbacks
    def text_generated_cb(output_text):
        socketio.emit("generated_text", {"text": output_text, "color": False, "delay":ml_thread.update_delay, "instant":True})
        udp_thread.send_text(output_text)
    ml_thread.text_generated_cb = text_generated_cb
    udp_thread.receive_cb = input_text_cb

    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    # Start the job threads
    try:
        ml_thread.start()
        udp_thread.start()
        socketio.run(app)
    except Exception:
        func = request.environ.get('werkzeug.server.shutdown')
        func()
        ml_thread.shutdown_flag.set()
        udp_thread.shutdown_flag.set()
        ml_thread.join()
        udp_thread.join()

if __name__=='__main__':
    main()