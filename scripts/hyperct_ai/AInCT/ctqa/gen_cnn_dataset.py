"""
Dataset generation of the training and testing procedure
"""
import numpy as np
import torch
from torch.utils.data import Dataset
from .cnn_utils import *

class RealDataset(Dataset): # for LSTM and Real Test
    def __init__(self, cube_slots):
        """
        Args:
            cube_slots: Splited reconstruction cubes.
        """
        self.cube_slots = cube_slots
        #self.transforms = transforms

    def __len__(self):
        return len(self.cube_slots)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        cube = self.cube_slots[idx, ]
        cube = np.moveaxis(cube, -1, 0)
        cube = np.expand_dims(cube, axis = 0)
        cube = cube_normalize(cube)
        cube = torch.tensor(cube)

        return cube


class ReconDataset(Dataset): # For training dataset
    def __init__(self, csv_file, im_dir):
        """
        Args:
            csv_file (string): file name of csv
            im_dir (string): Directory with all the images.
        """
        self.labels = pd.read_csv(csv_file)
        self.im_dir = im_dir

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        im_name = '.'.join([os.path.join(self.im_dir, self.labels.iloc[idx][1])])

        cube = imread(im_name)
        cube = np.moveaxis(cube, -1, 0)
        cube = np.expand_dims(cube, axis = 0)
        cube = cube_normalize(cube)

        score = self.labels.iloc[idx][2]
        cube, score = torch.tensor(cube), torch.tensor(score)

        return cube, score
