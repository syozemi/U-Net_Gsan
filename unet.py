import tensorflow as tf
import numpy as np
import os
import shutil
import batch
from collections import OrderedDict
from libs import (get_variable, get_conv, get_bias, get_pool, get_crop, get_concat, get_deconv2)


class UNET:
    #テストデータ[-1, input_sizex, input_sizey]
    #ラベル[-1, input_sizex, input_sizey, 2]
    #初期化はinput_sizex, input_sizey, num_classは必ず指定、depthとかは"depth ="で行う 
    #input_sizex, input_sizeyを変に設定するとpoolで死ぬ可能性あり。

    def __init__(self, input_sizex , input_sizey, num_class, depth = 4, layers_default = 8):
        with tf.Graph().as_default():

            self.depth = depth
            self.layers_default = layers_default
            self.input_sizex = input_sizex
            self.input_sizey = input_sizey
            self.num_class = num_class

            self.prepare_model()
            self.prepare_session()

    def prepare_model(self):
        depth = self.depth
        layers_default = self.layers_default
        input_sizex = self.input_sizex
        input_sizey = self.input_sizey
        num_class = self.num_class

        with tf.name_scope('input'):
            with tf.device('/gpu:0'):
                x = tf.placeholder(tf.float32, [None, input_sizex, input_sizey])
                h_pool = tf.reshape(x, [-1, input_sizex, input_sizey, 1])

        with tf.name_scope('contracting'):
            layers = layers_default
            h_array = OrderedDict()

            output_sizex = input_sizex
            output_sizey = input_sizey

            with tf.device('/gpu:0'):

                for i in range(depth):
                    if i == 0:
                        filter1 = get_variable([3, 3, 1, layers])
                    else:
                        filter1 = get_variable([3, 3, layers // 2, layers])
                    h1 = get_conv(h_pool, filter1, 1, 'VALID')

                    filter2 = get_variable([3, 3, layers, layers])
                    h2 = get_conv(h1, filter2, 1, 'VALID')

                    h_array[i] = h2
                    h_pool = get_pool(h2, 2)

                    layers = layers * 2
                    output_sizex = (output_sizex - 4) // 2
                    output_sizey = (output_sizey - 4) // 2


        
        with tf.name_scope('floor'):
            with tf.device('/gpu:0'):
                filter5_1 = get_variable([3, 3, layers // 2, layers])
                h5_1 = get_conv(h_pool, filter5_1, 1, 'VALID')

                filter5_2 = get_variable([3, 3, layers, layers])
                h_pool = get_conv(h5_1, filter5_2, 1, 'VALID')

                output_sizex = output_sizex - 4
                output_sizey = output_sizey - 4

        with tf.name_scope('expanding'):
            with tf.device('/gpu:0'):
                for i in range(depth):
                    filter5 = get_variable([2, 2, layers // 2, layers])
                    h3 = get_deconv2(h_pool, filter5)

                    hcat = get_concat(h_array[depth - 1- i], h3)
                    filter1 = get_variable([3, 3, layers, layers // 2])
                    h1 = get_conv(hcat, filter1, 1, 'VALID')

                    filter2 = get_variable([3, 3, layers // 2, layers // 2])
                    h_pool = get_conv(h1, filter2, 1, 'VALID')

                    layers = layers // 2
                    output_sizex = output_sizex * 2 - 4
                    output_sizey = output_sizey * 2 - 4


        with tf.name_scope('dropout'):
            with tf.device('/gpu:0'):
                keep_prob = tf.placeholder(tf.float32)
                h_pool = tf.nn.dropout(h_pool, keep_prob)

        with tf.name_scope('softmax'):
            with tf.device('/gpu:0'):
                filter1_3 = get_variable([1, 1, layers, num_class])
                h_pool = get_conv(h_pool, filter1_3, 1, 'VALID') 

                result_logits = tf.reshape(h_pool, [-1, num_class])

                result = tf.nn.softmax(result_logits)

        with tf.name_scope('optimizer'):
            with tf.device('/gpu:1'):
                    t = tf.placeholder(tf.float32, [None, input_sizex, input_sizey, num_class])
                    tcrop = get_crop(t, [output_sizex, output_sizey])
                    tout = tf.reshape(tcrop, [-1, num_class])
                    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=tout,logits=result_logits))
                    train_step = tf.train.MomentumOptimizer(learning_rate = 0.02, momentum = 0.02).minimize(loss)

        with tf.name_scope('evaluator'):
            with tf.device('/gpu:1'):
                correct_prediction = tf.equal(tf.argmax(result, 1), tf.argmax(tout, 1))
                accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        tf.summary.scalar("loss", loss)
        tf.summary.scalar("accuracy", accuracy)
        # tf.summary.histogram("result", result[...,1])
        
        self.x, self.t, self.result, self.keep_prob = x, t, result, keep_prob
        self.train_step = train_step
        self.loss = loss
        self.tout = tout
        self.result = result
        self.accuracy = accuracy
        self.output_sizex = output_sizex
        self.output_sizey = output_sizey

    def prepare_session(self):
        sess = tf.InteractiveSession()
        sess.run(tf.global_variables_initializer())
        summary = tf.summary.merge_all()

        saver = tf.train.Saver()
        if os.path.isdir('/tmp/logs'):
            shutil.rmtree('/tmp/logs')
        writer = tf.summary.FileWriter("/tmp/logs", sess.graph)
        
        self.sess = sess
        self.summary = summary
        self.writer = writer
        self.saver = saver

