#! /usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Scott H. Hawley'
__copyright__ = 'Scott H. Hawley'

"""
Draft. Just a demo for now.

Visualization of model activations (and weights)
-  in realtime, based on live microphone input - 'oscilloscope-like' display
-  TODO: from audio file(s)

Still under development.  Currently it just reads from the (live) default microphone,
multiplies by one array of weights and shows the result.
Later I will try to load layers from a model, e.g. from checkpoint files

Tested only on Mac OS X High Sierra with Python 3.6 (Anaconda)
"""

import numpy as np
import torch
import argparse
import signaltrain as st
import cv2                  # pip install opencv-python
import soundcard as sc      # pip install git+https://github.com/bastibe/SoundCard
#from matplotlib.pylab import cm   # color map, not working yet
from scipy.ndimage.interpolation import shift  # used for oscilloscope trigger


layer_in_dim, layer_out_dim = 1024, 800    # input & output dimensions of the weights

imWidth = layer_in_dim      # image width for 'oscilloscope display'
imHeight = 600               # image height for oscilloscope display; can be anything.

yo = imHeight/4               # vertical location of horizontal axis for input
max_amp_pixels = imHeight/5   # maximum amplitude in pixels

# OpenCV BGR colors
blue, green, cyan = (255,0,0), (0,255,0), (255,255,0)

def draw_weights(weights, title="weights"):
    img = np.clip(weights*255 ,-255,255).astype(np.uint8)              #scale
    img = np.repeat(img[:,:,np.newaxis],3,axis=2)                # add color channels
    #img = cm.jet(img).astype(np.uint8)
    cv2.imshow(title, img)                      # show what we've got


def draw_activations(screen, weights, mono_audio, xs, \
    title="activations (cyan=input, green=output)", gains=[3,0.3]):

    screen *= 0                                # clear the screen
    act = np.matmul(mono_audio, weights)       # activations are a new waveform

    # minux sign in the following is because computer graphics are 'upside down'
    ys_in = ( yo - max_amp_pixels * np.clip( gains[0] * mono_audio[0:len(xs)], -1, 1) ).astype(np.int)
    ys_out = ( 3*yo - max_amp_pixels * np.clip( gains[1] * act[0:len(xs)], -1, 1) ).astype(np.int)

    ys_out = ys_out[0:layer_out_dim]            # don't show more than is supposed to be there
    pts_in = np.array(list(zip(xs,ys_in)))      # pair up xs & ys for input
    cv2.polylines(screen,[pts_in],False,cyan)   # draw lines connecting the points

    pts_out = np.array(list(zip(xs,ys_out)))    # pair up xs & ys for output
    cv2.polylines(screen,[pts_out],False,green)

    cv2.imshow(title, screen.astype(np.uint8))
    return

# this is a trigger function for the oscilloscope
def find_trigger(mono_audio, thresh=0.02, pos_slope=True):  # thresh = trigger level
    start_ind = None     # this is where in the buffer the trigger should go; None
    shift_forward = shift(mono_audio, 1, cval=0)
    if pos_slope:
        inds = np.where(np.logical_and(mono_audio >= thresh, shift_forward <= thresh))
    else:
        inds = np.where(np.logical_and(mono_audio <= thresh, shift_forward >= thresh))
    if (len(inds[0]) > 0):
        start_ind = inds[0][0]
    return start_ind


# just prints the keys one can use. wish I could get arrow keys working
def instructions():
    print("Keys: ")
    print("  = : increase input gain")
    print("  ' : decrease input gain")
    print("  ] : increase output gain")
    print("  [ : decrease output gain")
    print("  - : increase trigger level")
    print("  p : decrease trigger level")


# 'Oscilloscope' routine; audio buffer & sample rate; make the audio buffer a little bigger than 'needed',
#  to avoid showing zero-pads (which are primarily there for 'safety')
def scope(weights, buf_size=2000, fs=44100):

    default_mic = sc.default_microphone()
    print("oscilloscope: listening on ",default_mic)
    instructions()

    trig_level = 0.01   # trigger value for input waveform
    gains = [10,1]    # gains for input and output


    # allocate storage for 'screen'
    screen = np.zeros((imHeight,imWidth,3), dtype=np.uint8) # 3=color channels
    xs = np.arange(imWidth).astype(np.int)                  # x values of pixels (time samples)
    draw_weights(weights)

    while (1):                             # keep looping until someone stops this
        with default_mic.recorder(samplerate=fs) as mic:
            audio_data = mic.record(numframes=buf_size)  # get some audio from the mic

        bgn = find_trigger(audio_data[:,0], thresh=trig_level)    # try to trigger
        if bgn is not None:
            end = min(bgn+layer_in_dim, buf_size)                 # don't go off the end of the buffer
            pad_len = max(0, layer_in_dim - (end-bgn) )           # might have to pad with zeros
            padded_data = np.pad(audio_data[bgn:end,0],(0,pad_len),'constant',constant_values=0)
            draw_activations(screen, weights, padded_data, xs, gains=gains)             # draw left channel
        else:
            draw_activations(screen, weights, audio_data[0:layer_in_dim,0]*0, xs, gains=gains)   # draw zero line


        key = cv2.waitKeyEx(1) & 0xFF         # keyboard input

        # Couldn't get arrow keys to work.
        if (key != -1) and (key !=255):
            print('key = ',key)
        if ord('q') == key:       # quit key
            break
        elif ord('=') == key:  # equal sign
            gains[0] *= 1.1
            print("gains =",gains)
        elif ord("'") == key:  # signle quote
            gains[0] *= 0.9
            print("gains =",gains)
        elif ord(']') == key:  #  right bracket
            gains[1] *= 1.1
            print("gains =",gains)
        elif ord('[') == key:  # left bracket
            gains[1] += 0.9
            print("gains =",gains)
        elif ord('-') == key:     # minus sign
            trig_level += 0.001
            print("trig_level =",trig_level)
        elif ord("p") == key:     # letter p
            trig_level -= 0.001
            print("trig_level =",trig_level)

    return



def main():
    # set up the 'transform' weights  TODO: load these from PyTorch model
    ny, nx = (layer_in_dim, layer_out_dim)
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    xv, yv = np.meshgrid(x,y)
    weights = 0.2*np.sin(2*3.14*4*xv)*np.sin(2*3.14*4*yv)
    weights += 0.1*np.random.rand(layer_in_dim, layer_out_dim)             # these map from audio to screen!

    # call the oscilloscope in order to visualize activations
    scope(weights, buf_size=int(layer_in_dim*1.5))

    # Note: by using multiprocessing or threading, could run scope & other visualizations simultaneously
    # not sure how the audio library would like that maybe via threading so they all share the same
    # input buffer
    return


if __name__ == '__main__':
    main()

# EOF
