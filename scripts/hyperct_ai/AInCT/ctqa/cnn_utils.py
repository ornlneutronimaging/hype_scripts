import os
import torch
import numpy as np
from collections import OrderedDict
from skimage.io import imread
from torch.utils.data import Dataset, DataLoader

def split_cube(dt, kernel_size, stride):
    """
    split reconstruion in spatial domain
    input: dt: 3D array; kernel_size=int, stride=int
    output: 4D array [total_patch_num, patch_height, patch_width, channel]
    """
    h, w, ch = dt.shape
    kh, kw = kernel_size
    #dt_split = np.zeros((int(((h-kh)/stride+1)*((w-kw)/stride+1)), kh, kw, ch))
    dt_split = np.zeros((len(np.arange(0,h-kh+1,stride))*len(np.arange(0,w-kw+1,stride)), kh, kw, ch))
    ct = 0
    for i in np.arange(0,h-kh+1,stride):
        for j in np.arange(0,w-kw+1,stride):
            dt_split[ct,] = dt[i:i+kh,j:j+kw,:]
            ct += 1
    return dt_split

def create_slots(roi_cube, cube_h, cube_w, stride, interval, stride_z):
    """
    split reconstruction on both spatial and slice domain
    input: roi_cube: 3D array; cube_h=int, cube_w=int, stride=spatial sampling stride
           interval=slice number of each sample, stride_z= slice sampling stride
    output: 4D array [total_cube_num, cube_h, cube_w, interval]
    """
    sq_tot_len = roi_cube.shape[-1]
    s_st = np.arange(0, sq_tot_len-interval+1, stride_z)
    sq_num = len(s_st)

    cubes = split_cube(roi_cube, (cube_h, cube_w), stride)
    cube_slots = np.zeros((cubes.shape[0]*sq_num, cube_h, cube_w, interval))

    for i in range(cube_slots.shape[0]):
        cube_slots[i,] = cubes[i//sq_num, :, :, s_st[i%sq_num]: s_st[i%sq_num]+interval]

    return cube_slots

def cube_normalize(cube):
    """
    0-1 Normalization (3D)
    """
    cube_min = cube.min()
    cube_max = cube.max()

    return (cube-cube_min)/(cube_max-cube_min)

def clean_model(state_dict): # remove `module.`in state_dict for model load
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:]
        new_state_dict[name] = v
    return  new_state_dict

def load_ckp(checkpoint_fpath, model, device):# Load trained model
    model_dict = model.state_dict()
    checkpoint = torch.load(checkpoint_fpath, map_location=device)
    model.load_state_dict(clean_model(checkpoint['model_state_dict']))
    return model
