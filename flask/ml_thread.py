#! /usr/bin/env python
# Threading
from time import sleep
from threading import Thread, Event, Lock
# ML network
import os
import sys
import json
import numpy as np
import tensorflow as tf
sys.path.append(os.path.join(os.path.dirname(__file__), '..','src'))
import model, sample, encoder

# A class that can be used to begin a threaded version of GPT-2
class MLThread(Thread):
    def __init__(self, model_name, seed = None, nsamples = 1, batch_size = 1,
                 length = 32, temperature = 1, top_k = 0, top_p = 1, update_hz = 7):
        # Populate defaults
        self.model_name = model_name
        self.seed = seed
        self.nsamples = nsamples
        self.batch_size = batch_size
        self.length = length
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.update_hz = update_hz
        self.models_dir = os.path.join(os.path.dirname(__file__), '..','models')
        self.current_text = ['Sarah & Rem. John Hathorn, both of Salem village']
        # Initialize threading variables
        self.shutdown_flag = Event()
        self.text_lock = Lock()
        super(MLThread, self).__init__()
        self.daemon = True

    # Will be called when thread.start is called
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
                sleep(self.update_hz)
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
                            self.text_generated_cb(output_text)

    # Function to insert input text
    def add_text(self, text):
        with self.text_lock:
            self.current_text = self.current_text + [text]

    # Empty function called when new text is generated to be implemented by user
    def text_generated_cb(self, output_text):
        pass