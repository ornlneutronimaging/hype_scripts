from logging import config
from random import sample

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
from datetime import datetime
import datetime


PROJECT_ROOT_FOLDER = "/SNS/VENUS/shared/software/git/hype_scripts"
file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/logs/{file_name}.log"
os.makedirs(os.path.dirname(LOG_FILE_NAME), exist_ok=True)

LOGGER2 = logging.getLogger("ai_automated_loop")
LOGGER2.setLevel(logging.INFO)
LOGGER2.propagate = False
if not LOGGER2.handlers:
    _file_handler = logging.FileHandler(LOG_FILE_NAME, mode='a')
    _file_handler.setFormatter(logging.Formatter("[%(levelname)s] - %(asctime)s - %(message)s"))
    LOGGER2.addHandler(_file_handler)
    
LOGGER2.info(f"*** Starting AiAutomatedLoop - version 05_15_2026 ***")

from IPython.display import display
from IPython.core.display import HTML

from . import list_of_runs_found_file, config_file, script1_path, script2_path
from scripts.EICClient import EICClient
from . import LAST_RUN_NUMBER_PV


def _worker(fl):
    return (imread(fl).astype(np.float32)).swapaxes(0,1)


class AiAutomatedLoop:

    def __init__(self, 
                 live=True,
                 new_experiment=False,
                 ipts=None, 
                 sample_name="test_sample",
                 user_conditions="T10K",
                 debug=False,
                 description_of_exp="", 
                 nbr_obs=4, 
                 proton_charge=1.0, 
                 number_of_projections_at_each_angle=1,
                 first_run=None,
                 motor=1,
                 sample_alignment="",
                 ob_alignment="",
                 list_of_initial_angles=None,
                 ):
          
        # _remove_me_log = os.path.join(PROJECT_ROOT_FOLDER, "logs", "REMOVE_ME.log")
        # _called_params = {
        #     "live": live,
        #     "new_experiment": new_experiment,
        #     "ipts": ipts,
        #     "sample_name": sample_name,
        #     "user_conditions": user_conditions,
        #     "debug": debug,
        #     "description_of_exp": description_of_exp,
        #     "nbr_obs": nbr_obs,
        #     "proton_charge": proton_charge,
        #     "first_run": first_run,
        #     "motor": motor,
        #     "sample_alignment": sample_alignment,
        #     "ob_alignment": ob_alignment,
        #     "list_of_initial_angles": list_of_initial_angles,
        # }
        # with open(_remove_me_log, "a") as _f:
        #     _f.write("\n")
        #     _f.write(f"AiAutomatedLoop.__init__ called")
        #     for _key, _value in _called_params.items():
        #         _f.write(f"{_key}: {_value}\n")
        # with open(_remove_me_log, "a") as _f:
        #     _f.write(f"config_file_used: {self.config_file}\n")
        #     _f.write("-" * 80 + "\n")

        self.config_file = str(config_file)
        LOGGER2.info(f"Loading config file from {self.config_file}")

        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)
        self.config = config
        
        config['EIC_vals']['ipts'] = ipts
        with open(self.config_file, 'w') as outfile:
            yaml.dump(config, outfile, sort_keys=False)

        self.live = live
        if new_experiment:
            config['ob_local_path'] = []
            config['0_and_180_local_path'] = []

        self.ipts = ipts
        self.description_of_exp = description_of_exp
        self.nbr_obs = nbr_obs
        self.proton_charge = proton_charge
        self.number_of_projections_at_each_angle = number_of_projections_at_each_angle
        self.sample_alignment = sample_alignment
        self.ob_alignment = ob_alignment
        
        if not (list_of_initial_angles is None):
            str_list_of_initial_angles = list_of_initial_angles.strip().replace(" ", "")
            list_of_initial_angles = [float(angle) for angle in str_list_of_initial_angles.split(",")]
        else:
            list_of_initial_angles = []
        self.list_of_initial_angles = list_of_initial_angles

        first_run_number = self.get_first_run_number() if first_run is None else first_run
        self.run_number = first_run_number
        self.debug = debug
        self.script1_path = script1_path
        self.script2_path = script2_path
        self.output_config_file = f"/data/VENUS/IPTS-{self.ipts}/shared/ai/"

        config['EIC_vals']['sample_name'] = sample_name
        config['EIC_vals']['user_conditions'] = user_conditions
        config['EIC_vals']['motor_number'] = motor
        config['EIC_vals']['ipts'] = str(self.ipts)
        
        config['number_of_projections_at_each_angle'] = number_of_projections_at_each_angle
        
        # resetting the pre-processing table in the config file (used for marimo interface)
        config['marimo']['pre_processing_table']['raw'] = []
        config['marimo']['pre_processing_table']['corrected'] = []
        config['marimo']['pre_processing_table']['final'] = []

        config['ob_alignment_file'] = ob_alignment
        config['sample_alignment_file'] = sample_alignment
        config['list_of_initial_angles'] = list_of_initial_angles

        autoreduce_folder = f"/SNS/VENUS/IPTS-{self.ipts}/shared/autoreduce/images/mcp/tpx1/raw/ct"
        config['autoreduce_mcp_folder'] = autoreduce_folder
        
        datenow = datetime.date.today().strftime("%Y%m%d")
        proton_charge = f"{proton_charge:.2f}"
        list_proton_charge = proton_charge.split(".")
        str_proton_charge = f"{int(list_proton_charge[0]):02d}_{int(list_proton_charge[1]):02d}C"
        
        config['DataPath'] = f"/data/VENUS/IPTS-{self.ipts}/images/tpx1/raw/ct/{datenow}_{sample_name}_{user_conditions}_{str_proton_charge}"
        config['nexus_folder'] = f"/SNS/VENUS/IPTS-{self.ipts}/nexus"
                
        with open(self.config_file, 'w') as outfile:
            yaml.dump(config, outfile, sort_keys=False)

        self.input_folder = config['debugging_mcp_folder'] if debug else config['mcp_folder']
        self.autoreduce_folder = config['autoreduce_mcp_folder']    

        LOGGER2.info(f"*** IPTS: {self.ipts}") 
    
    def get_first_run_number(self):
        
        eic_token = self.config['EIC_vals']['eic_token']
        ipts = self.ipts
        beamline = "BL10"
        timeout = 10

        eic_client = EICClient(eic_token, ipts_number=str(ipts), beamline=beamline)
        pv_name = LAST_RUN_NUMBER_PV

        success_get, pv_value_read, response_data_get = eic_client.get_pv(pv_name, timeout)
        if success_get:
            prefix = f'Successfully read PV {pv_name} with value {pv_value_read}'
            run_number = int(pv_value_read) + 1
            LOGGER2.info(f"First run number requested: {run_number}")
            return run_number
        else:
            prefix = f'Failed to read PV {pv_name}'
            LOGGER2.info(f"Failed to read PV {pv_name}")
            raise KeyError(prefix)

    def launch_pre_processing_step(self):     

        config = self.config

        # update
        config['EIC_vals']['number_of_obs'] = self.nbr_obs
        config['EIC_vals']['proton_charge'] = float(self.proton_charge)
        config['run_number_expected'] = self.run_number
        config['starting_run_number'] = self.run_number
        config['EIC_vals']['scan_description'] = self.description_of_exp
        config['ai_pre_process_running'] = True
        config['ob_local_path'] = []
        config['EIC_vals']['ipts'] = str(self.ipts)
        config['working_with_first_processing_angles'] = True

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

        if self.live:
            self.launching_shimin_cmd1()

    def launching_shimin_cmd1(self):
        LOGGER2.info(f"Launching shimin cmd1: {self.script1_path}")
        cmd = f'python {self.script1_path} --cfg_file {self.config_file}'
        LOGGER2.info(f"launching {cmd}")
        #os.system(cmd)

        try:
            result = subprocess.run(cmd, shell=True,
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            LOGGER2.info(f"shimin cmd1 output: {result.stdout}")
            LOGGER2.info(f"shimin cmd1 errors: {result.stderr}")
            if "FAILED" in result.stderr:
                    LOGGER2.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return

        except subprocess.CalledProcessError as e:
            LOGGER2.error(f"shimin cmd1 failed: {e.stderr}")
            LOGGER2.error(f"shimin cmd1 output: {e.stdout}")
            AiAutomatedLoop.logging_error_messages(e.stderr, type='stderr')
            AiAutomatedLoop.logging_error_messages(e.stdout, type='stdout')

    def check_that_pre_process_measurement_is_done(self):
        with open(config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if config['ai_pre_process_running']:
            LOGGER2.info("Pre-processing still running, check back in a few minutes!")

        else:
            LOGGER2.info("Pre-processing is DONE! Feel free to move to the next cell!")

    @staticmethod
    def retrieve_list_of_runs(top_folder):
        list_runs = glob.glob(os.path.join(top_folder, "Run_*"))
        list_runs.sort()
        return list_runs

    @staticmethod
    def retrieve_list_of_tif(folder):
        # folder = os.path.join(folder, 'tpx3')  #remove if working with demo
        # list_tif = glob.glob(os.path.join(folder, "*.tif*"))
        list_tif = glob.glob(f"{folder}" + "*.tif*")
        list_tif.sort()
        return list_tif
    
    @staticmethod
    def retrieve_first_tif(folder):
        # folder = os.path.join(folder, 'tpx3') #remove if working with demo
        list_tif = glob.glob(f"{folder}" + "*.tif*")
        LOGGER2.info(f"{folder}" + "*.tif*")
        LOGGER2.info(f"{folder}")
        list_tif.sort()
        return list_tif[0]

    @staticmethod
    def retrieve_angle_value(tiff_file):
        LOGGER2.info(f"retrieve angle value from {tiff_file}")
        splitted_tif_file = tiff_file.split("_")
        LOGGER2.info(f"\t{splitted_tif_file = }")
        degree = splitted_tif_file[-5]
        minute = splitted_tif_file[-4][:-3]
        LOGGER2.info(f"\t{degree = }")
        LOGGER2.info(f"\t{minute = }")
        angle_value = f"{degree}.{minute}"
        return float(angle_value)

    @staticmethod
    def run_is_an_ob(run):
        if '_OB_' in run:
            return True
        else:
            return False

    @staticmethod
    def isolate_0_and_180_degrees_projections(list_of_runs):
        LOGGER2.info(f"isolating 0 and 180 degrees projections")
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

        LOGGER2.info(f"list_angles: {list_angles}")
        LOGGER2.info(f"list_sample_runs: {list_sample_runs}")

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

        LOGGER2.info(f"calculate center of rotation:")
        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        if not config['ai_pre_process_running']:
            
            # find 0 and 180 degrees projections
            LOGGER2.info(f"retrieve list of runs ...")
            LOGGER2.info(f"\t{self.autoreduce_folder = }")

            list_of_0_180_degrees_runs = config['0_and_180_local_path']

            # list_runs = AiAutomatedLoop.retrieve_list_of_runs(self.autoreduce_folder)
            if len(list_of_0_180_degrees_runs) == 0:
                print("No run found")
                LOGGER2.info(f"No run found")
                return
            elif len(list_of_0_180_degrees_runs) < 2:
                print("Not enough runs found")
                LOGGER2.info(f"Not enough runs found")
                return
            else:
                print("0 and 180 runs found")
                run_0_degree, run_180_degree = AiAutomatedLoop.isolate_0_and_180_degrees_projections(list_of_0_180_degrees_runs)
                LOGGER2.info(f"0 degree run: {run_0_degree}")
                LOGGER2.info(f"180 degree run: {run_180_degree}")

            if (run_180_degree is None) or (run_0_degree is None):
                print("Could not find 0 and 180 degrees projections")
                LOGGER2.info(f"Could not find 0 and 180 degrees projections")
                return

            LOGGER2.info(f"retrieve list of tiff files ...")
            list_tiff_0 = AiAutomatedLoop.retrieve_list_of_tif(run_0_degree)
            list_tiff_180 = AiAutomatedLoop.retrieve_list_of_tif(run_180_degree)
            LOGGER2.info(f"retrieve list of tiff files ... DONE")
          
            LOGGER2.info(f"load data using multithreading ...")
            data_0 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_0)
            data_180 = AiAutomatedLoop.load_data_using_multithreading(list_tiff_180)
            LOGGER2.info(f"load data using multithreading ... DONE")

            integrated_image = [np.sum(data_0, axis=0), np.sum(data_180, axis=0)]
            center_of_rotation = find_center_pc(integrated_image[0], integrated_image[1])
            LOGGER2.info(f"center_of_rotation: {center_of_rotation}")
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

    def crop_images(self):
        pass
    
    def select_tof_ranges(self):
        pass

    def logging_error_messages(message, type='error'):
        formatted_message = message.split("\n")
        for _message in formatted_message:
            if _message:
                LOGGER2.info(f"{type}: {_message}")

    def launching_ai_loop(self):
        #shutil.copy(self.config_file, self.output_config_file)

        with open(self.config_file, 'r') as stream_config:
            config = yaml.safe_load(stream_config)

        config['ai_process_running'] = True

        # export
        with open(self.config_file, 'w') as outfile:
            yaml.dump(config, outfile, sort_keys=False)
        
        cmd = f'python {self.script2_path} --cfg_file {self.config_file}'
        LOGGER2.info(f"launching {cmd}")

        if not self.live:
            LOGGER2.info(f"Not live, running {cmd}")
            return

        try:
            result = subprocess.run(cmd, shell=True,
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            AiAutomatedLoop.logging_error_messages(result.stderr, type='stdout')
            if "FAILED" in result.stderr:
                    LOGGER2.info(f"FAILED")
                    display(HTML("<font color='red'>FAILED! Check log file for more information</font>"))
                    return

        except subprocess.CalledProcessError as e:
            AiAutomatedLoop.logging_error_messages(e.stderr, type='stderr')
            AiAutomatedLoop.logging_error_messages(e.stdout, type='stdout')
