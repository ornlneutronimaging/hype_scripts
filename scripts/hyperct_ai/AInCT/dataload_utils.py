import os, glob, dxchange, svmbir, h5py
import numpy as np
import pandas as pd
import multiprocessing as mp
from .utils import dir_check
from skimage.io import imread
from tqdm import tqdm
from functools import partial

class FrameLoader(object): 
    def __init__(self, fl, paras):
        self.fl = fl
        # for clean data
        self.bd = paras['bound']
        #self.r = paras['correct_radius']
        #self.CLEAN = paras['if_clean']
        #self.SAVE_CLEAN = paras['if_save_clean']
        #self.clean_path = clean_path
        # for alignment chips
        self.x_offset = paras['x_off']
        self.y_offset = paras['y_off']
        self.center_x = paras['cent_x'] 
        self.center_y = paras['cent_y']
        self.num_pix_unused = paras['unused_pix_num']
        self.num_pix_neighbor  = paras['neighbor_pix_num']

        _im = (imread(self.fl).astype(np.float32)).swapaxes(0,1)
        self.row, self.col = _im.shape
        self.im = _im[self.bd:self.row-self.bd, self.bd:self.col-self.bd]
        self.corr_im = np.nan_to_num(self.im.copy(), nan=0, posinf=0, neginf=0)
        #self.log = {}

    def run(self):
        #if self.CLEAN:
        #    self.replace_pix()
        self.row, self.col = self.corr_im.shape
        self.correct_alignment(fill_gap=True)
        #self.save_opt()

    def replace_pix(self):
        thres = 0.1*np.median(self.corr_im)
        x_coords, y_coords = np.nonzero(self.corr_im <= thres)
        r = self.r
        org_val, cor_val = [], []
        for x, y in zip(x_coords, y_coords):
            X_, _X = max(0, x-r), min(self.corr_im.shape[0], x+r)
            Y_, _Y = max(0, y-r), min(self.corr_im.shape[1], y+r)
            org_val.append(self.corr_im[x, y])
            pat = self.im[X_ : _X+1, Y_: _Y+1]
            if np.nonzero(pat > thres)[0].size >=4:
                _elements = list(pat.flatten())
                _elements.pop(r*(1+2*r)+r)
                _corrected = sum(_elements)/(pat.size-1)
                self.corr_im[x, y] = _corrected
                cor_val.append(_corrected)
            else:
                print('ERROR, too many zeros around pixel({},{})'.format(x, y))
                cor_val.append('-')
        
        self.log = {'fname': self.fl, 'X': x_coords, 'Y': y_coords, 
                    'original': org_val, 'corrected': cor_val}
        
    def correct_alignment(self, fill_gap=True):
        """
        Function to correct alignment of the 4 segments in each image caused by the mismatch between the 4 chips.
        Orginal @ Samin, revised for data shape (height x width)
        Args:
            unaligned_image(ndarray): 3D projection data (num_proj x height x width)
            offsets(list): a list of offset values along X and Y axis, respectively (X offset, Y offset) [2, 2]
            center(list,optional): X and Y coordinate of the center that is connected to all 4 chips
            fill_gap(bool,optional): true/false, the function will fill the gap after moving the chips according to the
                offsets if set to true
            num_pix_unused(int,optional): number of pixels along the border not to be used while filling the gap
            num_pix_neighbor(int,optional): number of neighboring pixels used for filling the gap
            
        Returns:
            ndarray: aligned projection data (height' x width' x wavelengths)
        """
        # Get the offsets
        
        # Get the center
        if self.center_x is not None:
            # Check if the unaligned image contains the alignemnt center along both axes
            if (self.center_x < 0) or (self.center_x > self.row):
                self.center_x = self.row // 2
                self.x_offset = 0
            if (self.center_y < 0) or (self.center_y > self.col):
                self.center_y = self.cols // 2
                self.y_offset = 0
        else:
            self.center_x = self.row // 2
            self.center_y = self.cols // 2
            
        # Return the original image if both the offset values are zero
        if (self.x_offset == 0) and (self.y_offset == 0):
            print("correct_alignment() Warning: Alignment correction not performed as both the offset values are zero.")

        # Get the chips
        chip_1 = self.corr_im[:self.center_x, :self.center_y]
        chip_2 = self.corr_im[:self.center_x, self.center_y:]
        chip_3 = self.corr_im[self.center_x:, :self.center_y]
        chip_4 = self.corr_im[self.center_x:, self.center_y:]

        # Move the chips and create aligned image
        moved_image = np.zeros((self.row + self.x_offset, self.col + self.y_offset,))

        moved_image[:self.center_x, :self.center_y] = chip_1
        moved_image[:self.center_x, self.center_y + self.y_offset:] = chip_2
        moved_image[self.center_x + self.x_offset:, :self.center_y] = chip_3
        moved_image[self.center_x + self.x_offset:, self.center_y + self.y_offset:] = chip_4

        if fill_gap is True:
            filled_image = np.copy(moved_image)

            # Fill gaps along row-axis
            if self.x_offset > 0:
                x_upper_bound = self.row - self.num_pix_unused - self.num_pix_neighbor
                x_lower_bound = self.num_pix_unused + self.num_pix_neighbor
                if x_upper_bound > self.center_x >= x_lower_bound:
                    x0_up = self.center_x - self.num_pix_unused - self.num_pix_neighbor
                    x1_up = self.center_x - self.num_pix_unused
                    region_up = np.expand_dims(np.mean(filled_image[x0_up:x1_up], axis=0), axis=0)

                    x0_down = self.center_x + self.x_offset + self.num_pix_unused
                    x1_down = self.center_x + self.x_offset + self.num_pix_unused + self.num_pix_neighbor
                    region_down = np.expand_dims(np.mean(filled_image[x0_down:x1_down], axis=0), axis=0)

                    weights_x = np.expand_dims(np.linspace(0, 1, self.x_offset + 2 * self.num_pix_unused), axis=1)
                    filled_image[self.center_x - self.num_pix_unused:self.center_x + self.x_offset + self.num_pix_unused] = np.matmul(
                        weights_x[::-1], region_up) + np.matmul(weights_x, region_down)
                else:
                    print("correct_alignment() Warning: Couldn't fill gaps along y-axis as the center is close to border.")

            # Fill gaps along col-axis
            if self.y_offset > 0:
                y_upper_bound = self.col - self.num_pix_unused - self.num_pix_neighbor
                y_lower_bound = self.num_pix_unused + self.num_pix_neighbor
                if y_upper_bound > self.center_y >= y_lower_bound:
                    y0_left = self.center_y - self.num_pix_unused - self.num_pix_neighbor
                    y1_left = self.center_y - self.num_pix_unused
                    region_left = np.expand_dims(np.mean(filled_image[:, y0_left:y1_left], axis=1), axis=1)

                    y0_right = self.center_y + self.y_offset + self.num_pix_unused
                    y1_right = self.center_y +self.y_offset + self.num_pix_unused + self.num_pix_neighbor
                    region_right = np.expand_dims(np.mean(filled_image[:, y0_right:y1_right], axis=1), axis=1)

                    weights_y = np.expand_dims(np.linspace(0, 1, self.x_offset + 2 * self.num_pix_unused), axis=0)
                    filled_image[:, self.center_y - self.num_pix_unused:self.center_y + self.y_offset + self.num_pix_unused] = np.matmul(
                        region_left, weights_y[:, ::-1]) + np.matmul(region_right, weights_y)
                else:
                    print("correct_alignment() Warning: Couldn't fill gaps along x-axis as the center is close to border.")

            self.corr_im = filled_image

        else:
            self.corr_im = moved_image
    
    def save_opt(self):
        if self.SAVE_CLEAN:
            fname = os.path.join(self.clean_path, 'ZeroRemove_{}'.format(self.fl.split('/')[-1][:-4]))
            dxchange.writer.write_tiff(self.corr_im, fname=fname, overwrite=True)

        log_fld = os.path.join(self.clean_path, 'logs')
        df = pd.DataFrame.from_dict(self.log, orient='columns')
        df.to_csv(os.path.join(log_fld, 'correct_summary_{}.csv'.format(self.fl.split('/')[-1][:-4])))

class HyperData(object):
    def __init__(self, paths, paras, clean_path, wav_st, wav_end):
        self.paths = paths
        self.wav_st, self.wav_end = wav_st, wav_end
        self.load_paras = paras
        self.clean_path = clean_path

    def get_hyper_data(self):
        hyper_data = []
        for p in tqdm(self.paths):
            _data = self.load_hyper(p)
            hyper_data.append(_data)
            #logs.append(_log)
        return hyper_data

    def get_sum_data(self):
        sum_data_cube = []
        for p in tqdm(self.paths):
            _data= self.load_hyper(p)
            _sum_data = np.sum(_data, axis = 0)

            if self.load_paras['if_clean']:
                _sum_data, _log = self.replace_pix(_sum_data)
            if self.load_paras['if_cali']:
                """ calibrated with p_charge & frame number
                """
                run_num = os.path.split(p)[-1]
                nuxus_fl = f"/storage/VENUS/IPTS-33531/nexus/{run_num.replace('Run', 'VENUS')}.nxs.h5"

                with h5py.File(nuxus_fl, 'r') as hdf5_data:
                    _proton_charge = hdf5_data['entry']["proton_charge"][0]/1e12
                    print(f"{_proton_charge = }")
                    _acq_number = hdf5_data['entry']['DASlogs']['BL10:Det:PIXELMAN:ACQ:NUM']['value'][:][-1]
                    print(f"{_acq_number = }")
                _sum_data = _sum_data/_proton_charge/_acq_number
                
            save_sub_fld = os.path.join(self.clean_path, f"wav_{self.wav_st}_{self.wav_end}") #os.path.split(fld)[-2]
            dir_check(save_sub_fld)
            dir_check(os.path.join(save_sub_fld, 'logs'))
            self.save_log(_log, _sum_data, save_sub_fld, 
                          '{}_{}'.format(p.split('/')[-2], p.split('/')[-1]))
            #---------------------------------

            sum_data_cube.append(_sum_data)

        return sum_data_cube
    
    def pre_proc(self, fl): # only move the chips and remove error value
        floader = FrameLoader(fl, self.load_paras)
        floader.run()
        return floader.corr_im
    
    def load_hyper(self, fld, type = 'tif*'):
        files = glob.glob('{}/*.{}'.format(fld, type))
        files.sort()
        fls_queue = files[self.wav_st : self.wav_end]

        #_f = partial(self.pre_proc) 

        with mp.Pool(processes=10) as pool:
            data = pool.map(self.pre_proc, fls_queue)
        
        return np.array(data)

    def replace_pix(self, _im):
        _corr_im = _im.copy()
        thres = 0.05*np.median(_im)
        print(f"clean thres_value = {thres}")
        x_coords, y_coords = np.nonzero(_corr_im <= thres)
        r = self.load_paras['correct_radius']
        org_val, cor_val = [], []
        for x, y in zip(x_coords, y_coords):
            X_, _X = max(0, x-r), min(_corr_im.shape[0], x+r)
            Y_, _Y = max(0, y-r), min(_corr_im.shape[1], y+r)
            org_val.append(_corr_im[x, y])
            pat = _im[X_ : _X+1, Y_: _Y+1]
            if np.nonzero(pat > thres)[0].size >=4:
                _elements = list(pat.flatten())
                _elements.pop(r*(1+2*r)+r)
                _corrected = sum(_elements)/(pat.size-1)
                _corr_im[x, y] = _corrected
                cor_val.append(_corrected)
            else:
                print('ERROR, too many zeros around pixel({},{})'.format(x, y))
                cor_val.append('-')
        
        log = {'X': x_coords, 'Y': y_coords, 
               'original': org_val, 'corrected': cor_val}
        
        return _corr_im, log

    def save_log(self, _log, _im, _pth, _f):
        if self.load_paras['if_save_clean']:
            fname = os.path.join(_pth, f'ZeroRemove_{_f}')
            dxchange.writer.write_tiff(_im, dtype = np.float32, fname=fname, overwrite=True)

        log_fld = os.path.join(_pth, 'logs')
        df = pd.DataFrame.from_dict(_log, orient='columns')
        df.to_csv(os.path.join(log_fld, f'correct_summary_{_f}.csv'))

     
class ProjData(HyperData):
    def __init__(self, paths, paras, clean_path, wav_st, wav_end, ob):
        super(ProjData, self).__init__(paths, paras, clean_path, wav_st, wav_end)
        self.ob = ob

    def get_normal_data(self):
        _sum_data = super().get_sum_data()
        norm_data = -np.log(np.array(_sum_data) / self.ob)
        norm_data = np.nan_to_num(norm_data, nan=0, posinf=0, neginf=0)
        return norm_data

def gen_paths(base_folders):
    """
    joint base folder and its subfolder
    Inputs: list of folders
    Outputs: list of jointed folders
    """
    joint_path = [os.path.join(f, os.listdir(f)[0]) for f in base_folders]
    return joint_path

def info_get(folders, loc, word):
    info_list = []
    for f in folders:
        temp_lis = os.path.split(f)[loc].split('_')
        pt = temp_lis.index(word)
        info_list.append(np.float_('.'.join([temp_lis[pt+1], temp_lis[pt+2][:-3]])))
    return info_list

def load_temp(temp_file):
    _temp = np.load(temp_file)
    norm_data, angle_list = _temp['norm_data'], _temp['angle_list']
    return norm_data, angle_list

def calibrate_background(norm_projection, back_calib_boxes):
    """
    @Samin
    Function to estimate background offsets caused by the mismatch of open beam and raw projection counts at all
    wavelengths and remove the offsets from the data. Four boxed regions from the four chips where there are no objects
    are used to estimate the background offsets.
    
    Args:
        norm_projection(ndarray): normalized 3D projection densities (proj_num x height x width)
        back_calib_boxes(list): list of 4 1D arrays containing calibration box information for the 4 chips
            chip sequence: (top left, top right, bottom left, bottom right)
            each 1D array: (x start, y start, box height, box width)

    Returns:
        ndarray: background offset corrected projection densities (height x width x wavelengths)
    """
    # Initialize background calibrated projection
    back_calib_projection = np.copy(norm_projection)

    # Define the chip starting/ending points
    _, p_height, p_width,  = norm_projection.shape
    
    y_s = [0, 0, p_height // 2, p_height // 2]
    y_e = [p_height // 2, p_height // 2, p_height, p_height]
    x_s = [0, p_width // 2, 0, p_width // 2]
    x_e = [p_width // 2, p_width, p_width // 2, p_width]

    # Compute and subtract background offset for each chip
    for i, back_calib_box in enumerate(back_calib_boxes):
        # Setup box
        box_x = back_calib_box[0]
        box_y = back_calib_box[1]
        box_height = back_calib_box[2]
        box_width = back_calib_box[3]
        box = norm_projection[:, box_x:box_x + box_height, box_y:box_y + box_width]

        # Compute background offset and subtract
        background_offset = np.mean(box, axis=(1, 2)).astype(np.float32)
        background_offset = np.expand_dims(background_offset, axis=(1, 2))
        back_calib_projection[:, y_s[i]:y_e[i], x_s[i]:x_e[i]] = (norm_projection[:, y_s[i]:y_e[i], x_s[i]:x_e[i]]
                                                                  - background_offset).astype(np.float32)

    return back_calib_projection

def crop(proj_data, crop_cols = None, z_start = None, z_numSlice = None):
    if crop_cols is None and z_start is None:
        crop_data = proj_data
    elif crop_cols is None:
        crop_data = proj_data[:, z_start:z_start + z_numSlice,]
    elif z_start is None:
        #cent_col = proj_data.shape[2]//2
        crop_data = proj_data[:, :, crop_cols[0] : crop_cols[1]]
    else:
        cent_col = proj_data.shape[2]//2
        crop_data = proj_data[:, z_start:z_start + z_numSlice,
                              crop_cols[0] : crop_cols[1]]
    return crop_data

def find_new_proj(proj_base_folders, proj_save_path):
    proj_name_list = ['{}.tiff'.format(os.path.split(fl)[-1]) for fl in proj_base_folders]
    saved_name_list = os.listdir(proj_save_path)

    new_proj_name = set(proj_name_list) - set(saved_name_list)
    return [list(filter(lambda x: name.split('.')[0] in x, proj_base_folders))[0]
            for name in new_proj_name]

