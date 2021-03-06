#!/usr/bin/env python
# https://github.com/pytorch/examples/blob/master/regression/main.py
from __future__ import print_function
from itertools import count

import torch
import torch.autograd
import torch.nn.functional as F
from torch.autograd import Variable

POLY_DEGREE = 4
W_target = torch.randn(POLY_DEGREE, 1) * 5
b_target = torch.randn(1) * 5


def make_features(x):
    """Builds features i.e. a matrix with columns [x, x^2, x^3, x^4]."""
    x = x.unsqueeze(1)
    return torch.cat([x ** i for i in range(1, POLY_DEGREE+1)], 1)


def f(x):
    """Approximated function."""
    return x.mm(W_target) + b_target[0]


def poly_desc(W, b):
    """Creates a string description of a polynomial."""
    result = 'y = '
    for i, w in enumerate(W):
        result += '{:+.2f} x^{} '.format(w, len(W) - i)
    result += '{:+.2f}'.format(b[0])
    return result


def get_batch(batch_size=32):
    """Builds a batch i.e. (x, f(x)) pair."""
    random = torch.randn(batch_size)
    x = make_features(random)
    y = f(x)
    return Variable(x), Variable(y)


# Define model
fc = torch.nn.Linear(W_target.size(0), 1)

optimizer = torch.optim.SGD(fc.parameters(), lr=0.1, momentum=0.9)

y_old = []
x_old = []
for batch_idx in count(1):
    # Get data
    batch_x, batch_y = get_batch()

    # Reset gradients
    fc.zero_grad()

    # Forward pass
    y_est = fc(batch_x)
    y_old.append(y_est.squeeze().data.numpy())
    x_old.append(batch_x[:,0].data.numpy())
    output = F.smooth_l1_loss(y_est, batch_y)
    loss = output.data[0]

    # Backward pass
    output.backward()

    # Apply gradients
    for param in fc.parameters():
        param.data.add_(-0.1 * param.grad.data)

    # Stop criterion
    if loss < 1e-3:
        break

print('Loss: {:.6f} after {} batches'.format(loss, batch_idx))
print('==> Learned function:\t' + poly_desc(fc.weight.data.view(-1), fc.bias.data))
print('==> Actual function:\t' + poly_desc(W_target.view(-1), b_target))

#
# optim
fc = torch.nn.Linear(W_target.size(0), 1)

optimizer = torch.optim.SGD(fc.parameters(), lr=0.001, momentum=0.9)

optimizer = torch.optim.Adam(fc.parameters(), lr=0.1) 

# Define model
loss_hist = []
idx_hist = []
idx = 0

for i in range(1000):
    batch_x, batch_y = get_batch()
    optimizer.zero_grad()
    y_est = fc(batch_x)
    output = F.smooth_l1_loss(y_est, batch_y)
    loss = output.data[0]
    output.backward()
    optimizer.step()
    print('{}: {}'.format(i, loss))
    idx += 1
    idx_hist.append(idx)
    loss_hist.append(loss)

plt.figure(1)
plt.clf()
plt.semilogy(idx_hist,loss_hist)
plt.show()
