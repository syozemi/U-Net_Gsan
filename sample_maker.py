# [HWR-01] 必要なモジュールをインポートします。
# In [1]:

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import pickle
from tensorflow.examples.tutorials.mnist import input_data

# for CNN
# batch_size = 100
#
# train_x = np.random.rand(batch_size * 360 * 360).reshape(batch_size, 360 * 360)
# train_t = np.zeros(batch_size * 10).reshape(batch_size, 10)
#
#
# for i in range(batch_size):
#     a = np.random.rand()
#     train_t[i][int(a * 10)] = 1
#
# print (train_x, train_t)
#
# with open('data/train_x', mode='wb') as f:
#     pickle.dump(train_x, f)
#
# with open('data/train_t', mode='wb') as f:
#     pickle.dump(train_t, f)

#for UNET
batch_size = 5
num_class = 2

input_sizex = 572
input_sizey = 588
train_x = np.random.rand(batch_size * input_sizex * input_sizey).reshape(
        batch_size, input_sizex, input_sizey)

train_t = np.zeros(batch_size * input_sizex * input_sizey * num_class).reshape(batch_size, input_sizex, input_sizey, num_class)

for i in range(batch_size):
    for j in range(input_sizex):
        for k in range(input_sizey):
            if np.sign(np.random.rand() - 0.5) >= 0:
                train_t[i][j][k][0] = 1
            else:
                train_t[i][j][k][1] = 1


print (train_x.shape)
print (train_t)
print (train_t.shape)


with open('data/train_x', mode = 'wb') as f:
    pickle.dump(train_x, f)

with open('data/train_t', mode = 'wb') as f:
    pickle.dump(train_t, f)
