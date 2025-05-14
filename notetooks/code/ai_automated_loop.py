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
from scripts.EICClient import EICClient
from . import LAST_RUN_NUMBER_PV


PROJECT_ROOT_FOLDER = "/SNS/VENUS/shared/software/git/hype_scripts"
file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/logs/{file_name}.log"

def _worker(fl):
    return (imread(fl).astype(np.float32)).swapaxes(0,1)


class AiAutomatedLoop:

    def __init__(self, ipts=None, folder_title="", description_of_exp="", nbr_obs=4, proton_charge=1.0, debug=False):

        # load config file
        self.config_file = config_file
        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)
        self.config = config

        self.ipts = ipts
        self.folder_title = folder_title
        self.description_of_exp = description_of_exp
        self.nbr_obs = nbr_obs
        self.proton_charge = proton_charge

        first_run_number = self.get_first_run_number()
        self.run_number = first_run_number
        self.debug = debug
        self.script1_path = script1_path
        self.script2_path = script2_path
        self.output_config_file = f"/data/VENUS/IPTS-{self.ipts}/shared/ai/"
        self.input_folder = config['debugging_mcp_folder'] if debug else config['mcp_folder']

        logging.basicConfig(filename=LOG_FILE_NAME,
                            filemode='a',  # 'w'
                            format="[%(levelname)s] - %(asctime)s - %(message)s",
                            level=logging.INFO)
        
        logging.info(f"*** Starting AiAutomatedLoop - version 03/06/2025")
        logging.info(f"*** IPTS: {self.ipts}") 
        logging.info("*** Starting checking for new files - version 03/06/2025")
        print(f"check log file at {LOG_FILE_NAME}")
    
    def get_first_run_number(self):
        eic_token = self.config['EIC_vals']['eic_token']
        ipts = self.ipts
        beamline = "BL10"
        timeout = 10

        eic_client = EICClient(eic_token, ipts_number=ipts, beamline=beamline)
        pv_name = LAST_RUN_NUMBER_PV

        success_get, pv_value_read, response_data_get = eic_client.get_pv(pv_name, timeout)
        if success_get:
            prefix = f'Successfully read PV {pv_name} with value {pv_value_read}'
            run_number = int(pv_value_read) + 1
            logging.info(f"First run number requested: {run_number}")
            return run_number
        else:
            prefix = f'Failed to read PV {pv_name}'
            logging.info(f"Failed to read PV {pv_name}")
            raise KeyError(prefix)

    def launch_pre_processing_step(self):     

        config = self.config

        # update
        config['EIC_vals']['number_of_obs'] = self.nbr_obs
        config['EIC_vals']['proton_charge'] = float(self.proton_charge)
        config['run_number_expected'] = self.run_number
        config['starting_run_number'] = self.run_number
        config['EIC_vals']['experiment_title'] = self.folder_title.replace(" ", "_")
        config['EIC_vals']['scan_description'] = self.description_of_exp
        config['ai_pre_process_running'] = True
        config['ob_local_path'] = []
        config['EIC_vals']['ipts'] = self.ipts

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
            AiAutomatedLoop.logging_error_messages(result.stderr, type='stderr')
            AiAutomatedLoop.logging_error_messages(result.stdout, type='stdout')    
            if "FAILED" in result.stderr:
                    logging.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return

        except subprocess.CalledProcessError as e:
            # print(f"{e.stderr =}")  
            # print(f"{e.stdout =}")
            AiAutomatedLoop.logging_error_messages(e.stderr, type='stderr')
            AiAutomatedLoop.logging_error_messages(e.stdout, type='stdout')


    def check_that_pre_process_measurement_is_done(self):
        with open(config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if config['ai_pre_process_running']:
            print("Pre-processing still running, check back in a few minutes!")

        else:
            print("Pre-processing is DONE! Feel free to move to the next cell!")

    @staticmethod
    def retrieve_list_of_runs(top_folder):
        list_runs = glob.glob(os.path.join(top_folder, "*_Run_*"))
        list_runs.sort()
        return list_runs

    @staticmethod
    def retrieve_list_of_tif(folder):
        folder = os.path.join(folder, 'tpx3')  #remove if working with demo
        list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif.sort()
        return list_tif
    
    @staticmethod
    def retrieve_first_tif(folder):
        folder = os.path.join(folder, 'tpx3') #remove if working with demo
        list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif.sort()
        return list_tif[0]

    @staticmethod
    def retrieve_angle_value(tiff_file):
        splitted_tif_file = tiff_file.split("_")
        angle_value = f"{splitted_tif_file[-4]}.{splitted_tif_file[-3]}"
        return float(angle_value)

    @staticmethod
    def run_is_an_ob(run):
        if '_OB_' in run:
            return True
        else:
            return False

    @staticmethod
    def isolate_0_and_180_degrees_projections(list_of_runs):
        logging.info(f"isolating 0 and 180 degrees projections")
        list_sample_runs = []
        list_angles = []
        for _run in list_of_runs:
            first_tiff = AiAutomatedLoop.retrieve_first_tif(_run)
            if AiAutomatedLoop.run_is_an_ob(os.path.basename(first_tiff)):
                continue
            else:
                angle_value = AiAutomatedLoop.retrieve_angle_value(first_tiff)
                list_sample_runs.append(_run)
                list_angles.append(angle_value)

        logging.info(f"list_angles: {list_angles}")
        logging.info(f"list_sample_runs: {list_sample_runs}")

        # find the index of the angles closest to 0 and 180 degrees 
        idx_0_degree = np.argmin(np.abs(np.array(list_angles) - 0))
        idx_180_degree = np.argmin(np.abs(np.array(list_angles) - 180))

        return list_sample_runs[idx_0_degree], list_sample_runs[idx_180_degree]

    @staticmethod
    def load_data_using_multithreading(list_tif, combine_tof=False):
        with mp.Pool(processes=40) as pool:
            data = pool.map(_worker, list_tif)

        if combine_tof:
            return np.array(data).sum(axis=0)
        else:
            return np.array(data)

    def calculate_center_of_rotation(self, visualize=False):

        logging.info(f"calculate center of rotation:")
        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if not config['ai_pre_process_running']:
            
            # find 0 and 180 degrees projections
            list_runs = AiAutomatedLoop.retrieve_list_of_runs(self.input_folder)
            logging.info(f"{list_runs =}")
            if len(list_runs) == 0:
                print("No run found")
                logging.info(f"No run found")
                return
            elif len(list_runs) < 2:
                print("Not enough runs found")
                logging.info(f"Not enough runs found")
                return
            else:
                print("More than 2 runs found")
                run_0_degree, run_180_degree = AiAutomatedLoop.isolate_0_and_180_degrees_projections(list_runs)
                logging.info(f"0 degree run: {run_0_degree}")
                logging.info(f"180 degree run: {run_180_degree}")

            if (run_180_degree is None) or (run_0_degree is None):
                print("Could not find 0 and 180 degrees projections")
                logging.info(f"Could not find 0 and 180 degrees projections")
                return

            logging.info(f"retrieve list of tiff files ...")
            list_tiff_0 = AiAutomatedLoop.retrieve_list_of_tif(run_0_degree)
            list_tiff_180 = AiAutomatedLoop.retrieve_list_of_tif(run_180_degree)
            logging.info(f"retrieve list of tiff files ... DONE")
          
            logging.info(f"load data using multithreading ...")
            data_0 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_0)
            data_180 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_180)
            logging.info(f"load data using multithreading ... DONE")

            integrated_image = [np.sum(data_0, axis=0), np.sum(data_180, axis=0)]
            center_of_rotation = find_center_pc(integrated_image[0], integrated_image[1])
            logging.info(f"center_of_rotation: {center_of_rotation}")
            print(f"center_of_rotation: {center_of_rotation}")

            if visualize:

                integrated_min_image = [np.min(data_0, axis=0), np.min(data_180, axis=0)]
                final_integrated_image = np.min(integrated_min_image, axis=0)
                fig, ax = plt.subplots()
                im = ax.imshow(final_integrated_image)
                plt.colorbar(im, ax=ax)

            _, width = np.shape(integrated_image[0])
            config['center_offset'] = float(center_of_rotation) - float(width/2)

            # export
            with open(self.config_file, 'w') as outfile:
                yaml.dump(config, outfile, sort_keys=False)

    def logging_error_messages(message, type='error'):
        formatted_message = message.split("\n")
        for _message in formatted_message:
            if _message:
                logging.info(f"{type}: {_message}")

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
            AiAutomatedLoop.logging_error_messages(result.stderr, type='stdout')
            if "FAILED" in result.stderr:
                    logging.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return

        except subprocess.CalledProcessError as e:
            AiAutomatedLoop.logging_error_messages(e.stderr, type='stderr')
            AiAutomatedLoop.logging_error_messages(e.stdout, type='stdout')
