# -*- coding: utf-8 -*-
__author__ = 'S.I. Mimilakis & S.H. Hawley'

# imports
import torch


# Alternatives to mae (see https://heartbeat.fritz.ai/5-regression-loss-functions-all-machine-learners-should-know-4fb140e9d4b0)
def logcosh(y_hat, y):
    return torch.mean( torch.log( torch.cosh(y - y_hat) ))

def smoothl1(x, x_hat, delta=0.5):  # Huber loss
    #return torch.sum ( torch.where(torch.abs(true-pred) < delta , 0.5*((true-pred)**2), \
    #    delta*toch.abs(true - pred) - 0.5*(delta**2)) )
    return torch.nn.SmoothL1Loss(true-pred)


def mse(x, x_hat):
    return torch.mean((x - x_hat)**2)


def mae(x, x_hat):
    return torch.mean(torch.abs(x - x_hat))

# Main loss function
def calc_loss(y_hat, y_cuda, mag_hat, batch_size=20, scale_by_freq=None, l1_lambda=2e-5, reg_logcosh=False):
    # Reconstruction term plus regularization -> Slightly less wiggly waveform

    #loss = logcosh(y_hat, y_cuda) + 1e-5*torch.abs(mag_hat).mean()
    # loss = logcosh(y_hat, y_cuda) + 2e-5*torch.abs(mag_hat).mean()
    #print("y_hat.dtype, y_cuda.dtype, mag_hat.dtype, scale_by_freq.dtype =",y_hat.dtype, y_cuda.dtype, mag_hat.dtype, scale_by_freq.dtype)
    if not reg_logcosh:
        if scale_by_freq is None:
            loss = logcosh(y_hat, y_cuda) + l1_lambda*torch.abs(mag_hat).mean()    # second term is an L1 regularization to help 'damp' high-freq noise
        else:
            loss = logcosh(y_hat, y_cuda) + l1_lambda/10*torch.abs(mag_hat*scale_by_freq).mean()    # second term is an L1 regularization to help 'damp' high-freq noise
    else:
        if scale_by_freq is None:
            loss = logcosh(y_hat, y_cuda) + l1_lambda*torch.mean(torch.log(torch.cosh(mag_hat)))   # second term is an L1 regularization to help 'damp' high-freq noise
        else:
            loss = logcosh(y_hat, y_cuda) + l1_lambda/10*torch.mean(scale_by_freq*torch.log(torch.cosh(mag_hat)))    # second term is an L1 regularization to help 'damp' high-freq noise

    return loss



# EOF
