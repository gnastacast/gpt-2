#! /usr/bin/env python
# Threading
from time import sleep
from threading import Thread, Event, Lock
import signal
# Flask
from flask import Flask, render_template, flash, request
from flask_socketio import SocketIO, emit
from collections import namedtuple
# ML network
import os
import sys
import json
import numpy as np
import tensorflow as tf
sys.path.append(os.path.join(os.path.dirname(__file__), '..','src'))
import model, sample, encoder

class MLThread(Thread):
    def __init__(self):
        self.model_name='Salem'
        self.seed=None
        self.nsamples=1
        self.batch_size=1
        self.length=28
        self.temperature=1
        self.top_k=0
        self.top_p=1
        self.models_dir=os.path.join(os.path.dirname(__file__), '..','models')
        self.shutdown_flag = Event()
        self.text_lock = Lock()
        self.current_text = ['Sarah & Rem. John Hathorn, both of Salem village']
        super(MLThread, self).__init__()

    def run(self):
        models_dir = os.path.expanduser(os.path.expandvars(self.models_dir))
        if self.batch_size is None:
            self.batch_size = 1
        assert self.nsamples % self.batch_size == 0

        enc = encoder.get_encoder(self.model_name, models_dir)
        hparams = model.default_hparams()
        with open(os.path.join(models_dir, self.model_name, 'hparams.json')) as f:
            hparams.override_from_dict(json.load(f))

        if self.length is None:
            self.length = hparams.n_ctx // 2
        elif self.length > hparams.n_ctx:
            raise ValueError("Can't get samples longer than window size: %s" % hparams.n_ctx)
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.75)
        with tf.Session(graph=tf.Graph(), config=tf.ConfigProto(gpu_options=gpu_options)) as sess:
            context = tf.placeholder(tf.int32, [self.batch_size, None])
            np.random.seed(self.seed)
            tf.set_random_seed(self.seed)
            output = sample.sample_sequence(
                hparams=hparams, length=self.length,
                context=context,
                batch_size=self.batch_size,
                temperature=self.temperature, top_k=self.top_k, top_p=self.top_p
            )

            saver = tf.train.Saver()
            ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, self.model_name))
            saver.restore(sess, ckpt)

            while not self.shutdown_flag.is_set():
                print("thread_cb")
                sleep(3)
                maxLen = 5
                if len(self.current_text) > maxLen:
                    self.current_text = self.current_text[len(self.current_text) - maxLen:]
                input_text = ""
                with self.text_lock:
                    for t in self.current_text:
                        input_text = input_text + t
                context_tokens = enc.encode(input_text)
                for _ in range(self.nsamples // self.batch_size):
                    out = sess.run(output, feed_dict={
                        context: [context_tokens for _ in range(self.batch_size)]
                    })[:, len(context_tokens):]
                    for i in range(self.batch_size):
                        output_text = enc.decode(out[i])
                        with self.text_lock:
                            socketio.emit("generated_text", {"text": output_text, "color": False})

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '1-9840-813413491340-813-04'
#turn the flask app into a socketio app
socketio = SocketIO(app)

thread = MLThread()

@app.route("/")
def hello():
    # global thread
    # with thread.text_lock:
    #     if request.method == 'POST':
    #         new_text=request.form['finput']
    #         print(new_text)
    #         thread.current_text= thread.current_text + [new_text]
    return render_template('index.html')

# @app.route('/')
# def index():
#   return render_template('index.html')
@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@socketio.on('input_text')
def input_text_cb(msg):
    global thread
    with thread.text_lock:
        thread.current_text = thread.current_text + [msg['text']]
        socketio.emit("generated_text", {"text": msg['text'], "color":True})
 
def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise Exception

if __name__=='__main__':
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    # Start the job threads
    try:
        thread = MLThread()
        thread.start()
        socketio.run(app)
    except Exception:
        thread.shutdown_flag.set()
        func = request.environ.get('werkzeug.server.shutdown')
        func()
        thread.join()
    