#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import edward as ed
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
plt.ion()

from edward.stats import norm
from keras import backend as K
from keras.layers import Dense
from scipy.stats import norm as normal
from sklearn.model_selection import train_test_split


def plot_normal_mix(pis, mus, sigmas, ax, label='', comp=True):
  """Plots the mixture of Normal models to axis=ax comp=True plots all
  components of mixture model
  """
  x = np.linspace(-10.5, 10.5, 250)
  final = np.zeros_like(x)
  for i, (weight_mix, mu_mix, sigma_mix) in enumerate(zip(pis, mus, sigmas)):
    temp = normal.pdf(x, mu_mix, sigma_mix) * weight_mix
    final = final + temp
    if comp:
      ax.plot(x, temp, label='Normal ' + str(i))
  ax.plot(x, final, label='Mixture of Normals ' + label)
  ax.legend(fontsize=13)


def sample_from_mixture(x, pred_weights, pred_means, pred_std, amount):
  """Draws samples from mixture model.
  Returns 2 d array with input X and sample from prediction of mixture model.
  """
  samples = np.zeros((amount, 2))
  n_mix = len(pred_weights[0])
  to_choose_from = np.arange(n_mix)
  for j, (weights, means, std_devs) in enumerate(
          zip(pred_weights, pred_means, pred_std)):
    index = np.random.choice(to_choose_from, p=weights)
    samples[j, 1] = normal.rvs(means[index], std_devs[index], size=1)
    samples[j, 0] = x[j]
    if j == amount - 1:
      break
  return samples


def build_toy_dataset(N):
  y_data = np.float32(np.random.uniform(-10.5, 10.5, (1, N))).T
  r_data = np.float32(np.random.normal(size=(N, 1)))  # random noise
  x_data = np.float32(np.sin(0.75 * y_data) * 7.0 + y_data * 0.5 + r_data * 1.0)
  return train_test_split(x_data, y_data, random_state=42, train_size=0.1)



class MixtureDensityNetwork:
  """
  Mixture density network for outputs y on inputs x.
  p((x,y), (z,theta))
  = sum_{k=1}^K pi_k(x; theta) Normal(y; mu_k(x; theta), sigma_k(x; theta))
  where pi, mu, sigma are the output of a neural network taking x
  as input and with parameters theta. There are no latent variables
  z, which are hidden variables we aim to be Bayesian about.
  """
  def __init__(self, K):
    self.K = K

  def neural_network(self, X):
    """pi, mu, sigma = NN(x; theta)"""
    # fully-connected layer with 15 hidden units
    hidden1 = Dense(15, activation=K.relu, name="hidden1")(X)
    hidden2 = Dense(15, activation=K.relu, name="hidden2")(hidden1)
    self.mus = Dense(self.K, name="mus")(hidden2)
    self.sigmas = Dense(self.K, activation=K.exp, name="sigmas")(hidden2)
    self.pi = Dense(self.K, activation=K.softmax, name="pi")(hidden2)

  def log_prob(self, xs, zs):
    """log p((xs,ys), (z,theta)) = sum_{n=1}^N log p((xs[n,:],ys[n]), theta)"""
    # Note there are no parameters we're being Bayesian about. The
    # parameters are baked into how we specify the neural networks.
    X, y = xs['X'], xs['y']
    self.neural_network(X)
    result = self.pi * norm.prob(y, self.mus, self.sigmas)
    result = tf.log(tf.reduce_sum(result, 1))
    return tf.reduce_sum(result)



ed.set_seed(42)

N = 40000  # number of data points
D = 1  # number of features

# DATA
X_train, X_test, y_train, y_test = build_toy_dataset(N)
print("Size of features in training data: {!s:s}".format(X_train.shape))
print("Size of output in training data: {!s:s}".format(y_train.shape))
print("Size of features in test data: {!s:s}".format(X_test.shape))
print("Size of output in test data: {!s:s}".format(y_test.shape))
plt.figure(1)
plt.clf()
sns.regplot(X_train, y_train, fit_reg=False)
plt.show()

X = tf.placeholder(tf.float32, [None, D])
y = tf.placeholder(tf.float32, [None, D])
data = {'X': X, 'y': y}

# MODEL
model = MixtureDensityNetwork(20)

 init = tf.initialize_all_variables() #launch the graph 
 sess.run(init)

# INFERENCE
inference = ed.MAP([], data, model) # /home/abergman/.local/lib/python3.5/site-packages/edward/inferences/inference.py:171
config = tf.ConfigProto(device_count={'CPU': 8}) 
sess = tf.Session(config=config) 
# sess = ed.get_session()  # Start TF session ~/.local/lib/python3.5/site-packages/edward/util/graphs.py
K.set_session(sess)  # Pass session info to Keras
inference.initialize()

init = tf.initialize_all_variables()
init.run()


import timeit

n_epoch = 1000
train_loss = np.zeros(n_epoch)
test_loss = np.zeros(n_epoch)
start = timeit.default_timer()
for i in range(n_epoch):
  info_dict = inference.update(feed_dict={X: X_train, y: y_train})
  train_loss[i] = info_dict['loss']
  # test_loss[i] = sess.run(inference.loss, feed_dict={X: X_test, y: y_test})
end = timeit.default_timer()
print( (end-start)/n_epoch , "sec/iter\t", (end - start) , "sec" )
# 0.01175 sec/iter

start = timeit.default_timer()
test_loss[i] = sess.run(inference.loss, feed_dict={X: X_test, y: y_test})
end = timeit.default_timer()
print( (end - start) , "sec" )
# 0.02549 sec

#
# CRITICISM
pred_weights, pred_means, pred_std = \
    sess.run([model.pi, model.mus, model.sigmas], feed_dict={X: X_test})

def plotloss():
    plt.figure(2)
    plt.clf()
    plt.plot(np.arange(n_epoch), -test_loss / len(X_test), label='Test')
    plt.plot(np.arange(n_epoch), -train_loss / len(X_train), label='Train')
    plt.legend(fontsize=20)
    plt.xlabel('Epoch', fontsize=15)
    plt.ylabel('Log-likelihood', fontsize=15)
    plt.show()

plotloss()

obj = [0, 4, 6]
fig = plt.figure(3)
fig.clear()
axes = fig.add_subplot( nrows=3, ncols=1, figsize=(16, 6))

plot_normal_mix(pred_weights[obj][0], pred_means[obj][0],
                pred_std[obj][0], axes[0], comp=False)
axes[0].axvline(x=y_test[obj][0], color='black', alpha=0.5)

plot_normal_mix(pred_weights[obj][2], pred_means[obj][2],
                pred_std[obj][2], axes[1], comp=False)
axes[1].axvline(x=y_test[obj][2], color='black', alpha=0.5)

plot_normal_mix(pred_weights[obj][1], pred_means[obj][1],
                pred_std[obj][1], axes[2], comp=False)
axes[2].axvline(x=y_test[obj][1], color='black', alpha=0.5)

a = sample_from_mixture(X_test, pred_weights, pred_means,
                        pred_std, amount=len(X_test))
sns.jointplot(a[:, 0], a[:, 1], kind="hex", color="#4CB391",
              ylim=(-10, 10), xlim=(-14, 14))

sns.kdeplot( a[:,0], a[:,1], shade=True )
plt.show()
