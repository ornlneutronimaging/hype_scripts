from .DataLoader import *
import tomopy

class NICalibrator(object):
    """
    Class NICalibrator
    Args:
        data_path: autoreduced data loaction [string]
                   i.e. './data/autoreduced'
        cali_str: special words for filting out calibration data [string]
                  i.e. '*Meteorite_cali*'
        wav_st, wav_end: start idx and end idx of wavelengths to sum [int, int]
                         i.e. 30, 100

    Properties:
        NICalibrator.proj_data: white beam data of calibration data [ndarray][num_views, num_rows, num_cols]
        NICalibrator.rot_center: estimated rotation center [float]
        if input crop_cols
        NICalibrator.crop_data: cropped data [ndarray][num_view, num_rows, 2*crop_cols]
    """
    def __init__(self, data_path, cali_str, wav_st, wav_end):
        self.data_path = data_path
        self.cali_str = cali_str
        self.wav_st, self.wav_end = wav_st, wav_end
        self.crop_cols = None
        self.z_start, self.z_numSlice = None, None

        #load 0 and 180 degree data:ndarray[[num_views, num_rows, num_cols]]
        proj_paths = gen_paths(glob.glob(os.path.join(self.data_path, self.cali_str)))
        self.proj_data = np.array(HyperData(proj_paths, wav_st, wav_end).get_sum_data())[:, 5:-5, 5:-5]

        #calulate rot center
        self.rot_center = tomopy.find_center_pc(np.squeeze(self.proj_data[0,]),
                                                np.squeeze(self.proj_data[1,]), tol=0.5)
        self.center_offset = -(self.proj_data.shape[2]/2 - self.rot_center)

    def crop(self):
        if self.crop_cols is None and self.z_start is None:
            crop_data = self.proj_data
        elif self.crop_cols is None:
            crop_data = self.proj_data[:, self.z_start:self.z_start + self.z_numSlice,]
        elif self.z_start is None:
            cent_col = self.proj_data.shape[2]//2
            crop_data = self.proj_data[:, :, cent_col-self.crop_cols:cent_col+self.crop_cols]
        else:
            cent_col = self.proj_data.shape[2]//2
            crop_data = self.proj_data[:, self.z_start:self.z_start + self.z_numSlice,
                                       cent_col-self.crop_cols:cent_col+self.crop_cols]
        return crop_data
