#! /usr/bin/env python
import signal
# Flask
from flask import Flask, render_template, flash, request
from flask_socketio import SocketIO, emit
from collections import namedtuple

from ml_thread import MLThread
from udp_thread import UDPThread

__FADE__=False

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
    threads = [udp_thread, ml_thread]

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
        global __FADE__
        if ">>fd" in msg['text']:
            __FADE__ = not __FADE__
            socketio.emit("fade", {"value":__FADE__})
            return
        if ">>re" in msg['text'] or ">>rs" in msg['text']:
            idx = msg['text'].find(">>rs")
            ml_thread.pause_flag.clear()
            msg['text']= msg['text'][idx+4:]
            ml_thread.clear_history(msg['text'])
        if ">>cl" in msg['text']:
            socketio.emit("clear", {})
            ml_thread.pause_flag.set()
            return
        if ">>sp" in msg['text']:
            idx = msg['text'].find(">>sp")
            speed = float(msg['text'][idx+5:])
            print(speed)
            if speed >= 0:
                ml_thread.set_update_delay(speed)
            else:
                ml_thread.pause_flag.set()
            return
        else:
            ml_thread.add_text(msg['text'])
        socketio.emit("generated_text", {"text": msg['text'], "color":True, "delay":1, "instant":True})
     
    def service_shutdown(signum, frame):
        print('Caught signal %d' % signum)
        raise Exception

    # Set ML thread callback
    def text_generated_cb(output_text):
        socketio.emit("generated_text", {"text": output_text, "color": False, "delay":ml_thread.update_delay, "instant":True})
        udp_thread.send_text(output_text)
    ml_thread.text_generated_cb = text_generated_cb
    # Set UDP callback
    def udp_receive_cb(input_text):
        input_text_cb(input_text)
    udp_thread.receive_cb = input_text_cb

    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    # Start the job threads
    try:
        for thread in threads:
            thread.start()
        socketio.run(app)
    except Exception:
        func = request.environ.get('werkzeug.server.shutdown')
        func()
        for thread in threads:
            thread.shutdown_flag.set()
            thread.join()

if __name__=='__main__':
    main()