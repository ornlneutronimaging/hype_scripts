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
import subprocess
import logging
from IPython.display import display
from IPython.core.display import HTML

from . import list_of_runs_found_file, config_file, script1_path, script2_path

IPTS = 35790
PROJECT_ROOT_FOLDER = "/SNS/VENUS/IPTS-35790/shared/hype"
file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/logs/{file_name}.log"

def _worker(fl):
    return (imread(fl).astype(np.float32)).swapaxes(0,1)


class AiAutomatedLoop:

    def __init__(self, folder_title="", description_of_exp="", nbr_obs=4, proton_charge=1.0, first_run_number=None, debug=False):
        self.folder_title = folder_title
        self.description_of_exp = description_of_exp
        self.nbr_obs = nbr_obs
        self.proton_charge = proton_charge
        self.run_number = first_run_number
        self.debug = debug
        self.config_file = config_file
        self.script1_path = script1_path
        self.script2_path = script2_path
        self.output_config_file = f"/data/VENUS/IPTS-{IPTS}/shared/ai/"
        self.input_folder = "/SNS/VENUS/IPTS-35790/shared/debugging_ai/images/mcp/debugging_hype/" if debug else "/SNS/VENUS/IPTS-35790/images/mcp/images/"

        logging.basicConfig(filename=LOG_FILE_NAME,
                            filemode='a',  # 'w'
                            format="[%(levelname)s] - %(asctime)s - %(message)s",
                            level=logging.INFO)
        logging.info("*** Starting checking for new files - version 03/06/2025")
        print(f"check log file at {LOG_FILE_NAME}")

    def launch_pre_processing_step(self):     

        # load
        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        # update
        config['EIC_vals']['number_of_obs'] = self.nbr_obs
        config['EIC_vals']['proton_charge'] = float(self.proton_charge)
        config['run_number_expected'] = self.run_number
        config['starting_run_number'] = self.run_number
        config['EIC_vals']['experiment_title'] = self.folder_title.replace(" ", "_")
        config['EIC_vals']['scan_description'] = self.description_of_exp
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
        logging.info(f"launching {cmd}")
        #os.system(cmd)

        try:
            result = subprocess.run(cmd, shell=True,
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            standard_output = result.stdout
            standard_output_formatted = standard_output.split("\n")
            for _standard_output in standard_output_formatted:
                if _standard_output:
                    logging.info(f"{_standard_output = }")
                if "FAILED" in _standard_output:
                    logging.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return
    
        except subprocess.CalledProcessError as e:
            logging.info(f"{e.stderr = }")
            logging.info(f"{e.stdout = }")

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
        folder = os.path.join(folder, 'tpx3')
        list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif.sort()
        return list_tif
    
    @staticmethod
    def retrieve_first_tif(folder):
        folder = os.path.join(folder, 'tpx3')
        list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif.sort()
        return list_tif[0]

    @staticmethod
    def isoalte_0_and_180_degrees_projections(list_of_runs):
        run_0_degree = None
        run_180_degree = None
        for _run in list_of_runs:
            list_tiff = AiAutomatedLoop.retrieve_first_tif(_run)
            if '000_000' in list_tiff:
                run_0_degree = _run
            elif '180_000' in list_tiff:
                run_180_degree = _run
        return run_0_degree, run_180_degree

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
            
            # find 0 and 180 degrees projections
            list_runs = AiAutomatedLoop.retrieve_list_of_runs(self.input_folder)
            run_0_degree, run_180_degree = AiAutomatedLoop.isoalte_0_and_180_degrees_projections(list_runs)

            if (run_180_degree is None) or (run_0_degree is None):
                print("Could not find 0 and 180 degrees projections")
                logging.info(f"Could not find 0 and 180 degrees projections")
                return

            list_tiff_0 = AiAutomatedLoop.retrieve_list_of_tif(run_0_degree)
            list_tiff_180 = AiAutomatedLoop.retrieve_list_of_tif(run_180_degree)
          
            data_0 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_0)
            data_180 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_180)

            integrated_image = [np.sum(data_0, axis=0), np.sum(data_180, axis=0)]
            center_of_rotation = find_center_pc(integrated_image[0], integrated_image[1])

            if visualize:

                integrated_min_image = [np.min(data_0, axis=0), np.min(data_180, axis=0)]
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

        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        config['ai_process_running'] = True

        # export
        with open(self.config_file, 'w') as outfile:
            yaml.dump(config, outfile, sort_keys=False)
        
        cmd = f'python {self.script2_path} --cfg_file {self.config_file}'
        # os.system(cmd)

        try:
            result = subprocess.run(cmd, shell=True,
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            standard_output = result.stdout
            standard_output_formatted = standard_output.split("\n")
            for _standard_output in standard_output_formatted:
                if _standard_output:
                    logging.info(f"{_standard_output = }")
                if "FAILED" in _standard_output:
                    logging.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return

        except subprocess.CalledProcessError as e:
            logging.info(f"{e.stderr = }")
            logging.info(f"{e.stdout = }")
