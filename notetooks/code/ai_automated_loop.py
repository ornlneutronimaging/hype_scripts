import yaml
import os
import numpy as np
import multiprocessing as mp
import glob
from tqdm import tqdm
from skimage.io import imread
import matplotlib.pyplot as plt
from tomopy.recon.rotation import find_center_pc
import shutil

from . import list_of_runs_found_file, config_file, script1_path, script2_path


def _worker(fl):
    return (imread(fl).astype(np.float32)).swapaxes(0,1)


class AiAutomatedLoop:

    def __init__(self, folder_title="", description_of_exp="", nbr_obs=4, proton_charge=1.0, debug=False):
        self.folder_title = folder_title
        self.description_of_exp = description_of_exp
        self.nbr_obs = nbr_obs
        self.proton_charge = proton_charge
        self.debug = debug
        self.config_file = config_file
        self.script1_path = script1_path
        self.script2_path = script2_path
        self.output_config_file = "/storage/VENUS/IPTS-33531/shared/ai/"

        self.input_folder = "/SNS/VENUS/IPTS-33531/shared/autoreduce/mcp/" if debug else "/storage/VENUS/IPTS-33531/images/mcp"

    def launch_pre_processing_step(self):     

        # load
        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        # update
        config['number_of_obs'] = self.nbr_obs
        config['proton_charge'] = float(self.proton_charge)
        config['experiment_title'] = self.folder_title.replace(" ", "_")
        config['scan_description'] = self.description_of_exp
        config['ai_pre_process_running'] = True

        # export
        with open(self.config_file, 'w') as outfile:
            yaml.dump(config, outfile, sort_keys=False)

        # reset list of runs found
        # load
        with open(list_of_runs_found_file, 'r') as stream_config:
            config_file = yaml.safe_load(stream_config)

        config_file['ob'] = []
        config_file['projections'] = []

        with open(list_of_runs_found_file, 'w') as outfile:
            yaml.dump(config_file, outfile, sort_keys=False)

        self.launching_shimin_cmd1()

    def launching_shimin_cmd1(self):
        print(self.script1_path)
        cmd = f'python {self.script1_path} --cfg_file {self.config_file}'
        os.system(cmd)

    def check_that_pre_process_measurement_is_done(self):
        with open(config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if config['ai_pre_process_running']:
            print("Pre-processing still running, check back in a few minutes!")

        else:
            print("Pre-processing is DONE! Feel free to move to the next cell!")

    @staticmethod
    def retrieve_list_of_runs(top_folder):
        list_runs = glob.glob(os.path.join(top_folder, "Run_*"))
        list_runs.sort()
        return list_runs

    @staticmethod
    def retrieve_list_of_tif(folder):
        list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif.sort()
        return list_tif

    @staticmethod
    def load_data_using_multithreading(list_tif, combine_tof=False):
        with mp.Pool(processes=40) as pool:
            data = pool.map(_worker, list_tif)

        if combine_tof:
            return np.array(data).sum(axis=0)
        else:
            return np.array(data)

    def calculate_center_of_rotation(self, visualize=False):

        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if not config['ai_pre_process_running']:
            # load 0 and 180 degrees projections to calculate center of rotation
            list_all_projections = config['list_of_runs_reduced']
            list_not_obs_projections = [_folder_name for _folder_name in list_all_projections if not _folder_name.startswith('ob_')]
            if len(list_not_obs_projections) == 2:
                
                # we have 0 and 180 degrees projections
                list_projections_full_path = [os.path.join(self.input_folder, _file) for _file in list_not_obs_projections]
                
                # get run folder
                dict_stack_tiff = {}
                integrated_min_image = []
                integrated_image = []
                for _folder in tqdm(list_projections_full_path):
                    run = AiAutomatedLoop.retrieve_list_of_runs(_folder)[0]
                    list_tiff = AiAutomatedLoop.retrieve_list_of_tif(run)
                    _data = AiAutomatedLoop.load_data_using_multithreading(list_tiff)
                    dict_stack_tiff[os.path.basename(run)] = _data
                    integrated_min_image.append(np.min(_data, axis=0))
                    integrated_image.append(np.sum(_data, axis=0))

            if visualize:

                final_integrated_image = np.min(integrated_min_image, axis=0)
                fig, ax = plt.subplots()
                im = ax.imshow(final_integrated_image)
                plt.colorbar(im, ax=ax)

            center_of_rotation = find_center_pc(integrated_image[0], integrated_image[1])
            _, width = np.shape(integrated_image[0])
            config['center_offset'] = center_of_rotation - int(width/2)

            # export
            with open(self.config_file, 'w') as outfile:
                yaml.dump(config, outfile, sort_keys=False)

    def launching_ai_loop(self):
        #shutil.copy(self.config_file, self.output_config_file)
        cmd = f'python {self.script2_path} --cfg_file {self.config_file}'
        os.system(cmd)
