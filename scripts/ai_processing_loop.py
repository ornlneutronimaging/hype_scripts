import logging
import os
import yaml
import glob
import shutil
import subprocess
import argparse
import numpy as np
import stat
from pathlib import Path
import sys
import h5py

PROJECT_ROOT_FOLDER = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOLDER))

from notebooks.code import config_file as CONFIG_FILE_NAME

LOG_FILE_MAX_LINES_NUMBER = 1000

with open(CONFIG_FILE_NAME, 'r') as stream:
    config = yaml.safe_load(stream)

version = config['version']
ipts = config['EIC_vals']['ipts']
file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = PROJECT_ROOT_FOLDER / "logs" / f"{file_name}_{ipts}.log"
if not LOG_FILE_NAME.parent.exists():
    LOG_FILE_NAME.parent.mkdir(parents=True, exist_ok=True)

LOGGER = logging.getLogger("ai_processing_loop")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
if not LOGGER.handlers:
    _file_handler = logging.FileHandler(LOG_FILE_NAME, mode='a')
    _file_handler.setFormatter(logging.Formatter("[%(levelname)s] - %(asctime)s - %(message)s"))
    LOGGER.addHandler(_file_handler)

LOGGER.info(f"*** Starting checking for new files (ai_processing_loop)- version {version}")
LOGGER.info(f"check log file at {LOG_FILE_NAME}")

LAUNCH_SHIMIN_SCRIPT_EVERY_N_FILES = 3
SHIMIN_CODE = "/data/VENUS/shared/software/run/run_ai_loop.sh"   

debugging_flag = config['debugging']

if debugging_flag:
    MCP_FOLDER = config['debugging_mcp_folder']
    OUTPUT_FOLDER_ON_HYPE = config['debugging_output_folder_on_hype']
else:
    # MCP_FOLDER = config['mcp_folder']
    MCP_FOLDER = os.path.join(f"/SNS/VENUS/IPTS-{ipts}", "shared/autoreduce/")
    OUTPUT_FOLDER_ON_HYPE = config['DataPath']

CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER = PROJECT_ROOT_FOLDER / "logs" / "list_of_runs_found_in_folder.yaml"


def get_list_basename(list_full_folder_name):
    return [os.path.basename(_folder) for _folder in list_full_folder_name]


def copy_and_rename_that_folder(folder_to_move, new_name):
    # copy folder_to_move to OUTPUT_FOLDER_ON_HYPE
    LOGGER.info(f"copying/renaming {folder_to_move} to {OUTPUT_FOLDER_ON_HYPE} with new name {new_name} ...")
    shutil.copytree(folder_to_move, os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name)))
    # change the permission of the copied file
    LOGGER.info(f"changing the permission of the copied file (-r 777)")
    subprocess.run(["chmod", "-R", "777", os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name))])
    LOGGER.info(f"done!")


def do_we_need_to_copy_that_folder(folder_to_copy):
    # check if the folder has already been copied and renamed
    # _base_name = os.path.basename(folder_to_copy)
    if os.path.exists(os.path.join(OUTPUT_FOLDER_ON_HYPE, folder_to_copy)):
        LOGGER.info(f"{folder_to_copy} has already been copied!")
        return False
    else:
        LOGGER.info(f"{folder_to_copy} has not been copied yet!")
        return True


def get_new_short_name_of_run_number_expected(full_path_of_run_number_expected):
    """will look for the first tiff file in the full_path_of_run_number_expected folder and will make up the new name
    ex: 20250312_Run_7287_testing_the_eic_loop_pre_exp_test_00_10C_Angle_090_000deg_000_1914480.tiff
    new name: 20250312_Run_7287_testing_the_eic_loop_pre_exp_test_00_10C_Angle_090_000deg_000"""

    list_tiff = glob.glob(f"{full_path_of_run_number_expected}/*.tif*")    # add tpx3 for real case
    list_tiff.sort()
    first_file = os.path.basename(list_tiff[0])
    splitted_first_file = first_file.split("_")
    new_name = "_".join(splitted_first_file[:-1])
    return new_name

def get_number_of_files_for_each_run_expected(full_path_of_run_number_expected):
    """
    Look at the Spectra file and the number of lines in it to determine the number of files we should expect for each run.
     - if the Spectra file is not there, return a huge number to make sure we wait for the files to be there
     - if the Spectra file is there, we will expect 1 + number of lines in the Spectra file (the tiff file + the txt files)
    """
    spectra_file = os.path.join(full_path_of_run_number_expected, "*_Spectra.txt")
    list_spectra = glob.glob(spectra_file)
    if not list_spectra:
        return 100000  # Return a large number to wait for files
    with open(list_spectra[0], 'r') as f:
        number_of_lines = sum(1 for line in f)
    return 4 + number_of_lines


def  all_the_files_are_there(full_path_of_run_number_expected):
    LOGGER.info(f"checking if the system is done writing all the files ...")
    list_of_files = glob.glob(f"{full_path_of_run_number_expected}/*")   # add/remove /tpx3 for real case
    LOGGER.info(f"number of files found: {len(list_of_files)}")
    number_of_files_for_each_run_expected = get_number_of_files_for_each_run_expected(full_path_of_run_number_expected)
    LOGGER.info(f"number of files expected: {number_of_files_for_each_run_expected}")
    if len(list_of_files) < number_of_files_for_each_run_expected:
        return False
    return True


def processing():
    
     # load config file
    with open(CONFIG_FILE_NAME, 'r') as stream:
        config = yaml.safe_load(stream)

     # if flag is False, stop here
    if config['ai_process_running'] is False:
        LOGGER.info(f"AI process is not running yet!")
        LOGGER.info(f"... exiting the processing script!")
        return

    LOGGER.info(f"debugging mode: {debugging_flag}")
    LOGGER.info(f"MCP_FOLDER: {MCP_FOLDER}")
    LOGGER.info(f"OUTPUT_FOLDER_ON_HYPE: {OUTPUT_FOLDER_ON_HYPE}")
    LOGGER.info(f"AI process is now checking for new files!")
    run_number_expected = config['run_number_expected']
    LOGGER.info(f"run_number_expected: {run_number_expected}")
    
    working_with_first_processing_angles = config['working_with_first_processing_angles']
    LOGGER.info(f"working_with_first_processing_angles: {working_with_first_processing_angles}")
    if working_with_first_processing_angles:
        number_of_files_to_expect = config['num_ini_ang']
    else:
        number_of_files_to_expect = config['step']
    LOGGER.info(f"number_of_files_to_expect: {number_of_files_to_expect}")

    # check if run number expected showed up in the folder
    list_of_runs_expected = np.arange(run_number_expected, run_number_expected + number_of_files_to_expect)
    LOGGER.info(f"{list_of_runs_expected = }")

    list_full_path_of_run_number_expected = [os.path.join(MCP_FOLDER, f"Run_{_run_expected:04d}") for _run_expected in list_of_runs_expected]
    LOGGER.info(f"{list_full_path_of_run_number_expected = }")

    for _full_path_run_expected in list_full_path_of_run_number_expected:
        LOGGER.info(f"looking for {os.path.basename(_full_path_run_expected)}")
        if not os.path.exists(_full_path_run_expected):
            LOGGER.info(f"{os.path.basename(_full_path_run_expected)} not found!")
            LOGGER.info(f"... exiting processing.py!")
            return
        else:
            LOGGER.info(f"{os.path.basename(_full_path_run_expected)} found!")

    LOGGER.info(f"All the runs expected have been found and we can copy/rename them!")

    # check if all files required are in the respective folders
    for _full_path_run_expected in list_full_path_of_run_number_expected:

        # is the system done writing all the files
        if not all_the_files_are_there(_full_path_run_expected):
            LOGGER.info(f"not all the files are there yet!")
            LOGGER.info(f"... exiting processing.py!")
            return
        else:
            LOGGER.info(f"all the files required have been written for {os.path.basename(_full_path_run_expected)}!")   

    # check if folder has been copied already
    for _full_path_run_expected in list_full_path_of_run_number_expected:
        new_name_of_run_number_expected = get_new_short_name_of_run_number_expected(_full_path_run_expected)
        LOGGER.info(f"File will be renamed {new_name_of_run_number_expected}")
        if not do_we_need_to_copy_that_folder(new_name_of_run_number_expected):
            LOGGER.info(f"{os.path.basename(_full_path_run_expected)} has already been copied!")
            LOGGER.info(f"... exiting processing.py!")
        else:
            copy_and_rename_that_folder(_full_path_run_expected, new_name_of_run_number_expected)

    # launch Shimin's script #2
    LOGGER.info(f"launching Shimin's script ...")
    LOGGER.info(f"SHIMIN_CODE = {SHIMIN_CODE}")
    # os.system(SHIMIN_CODE)
    subprocess.run([SHIMIN_CODE])
   
    # update value of next run number expected
    config['run_number_expected'] += number_of_files_to_expect
    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)        
    

def change_permissions_recursive(path):
    """
    Change permissions of a directory and all its subdirectories recursively.

    Args:
        path (str): The path to the directory.
        mode (int): The permission mode to set (e.g., 0o755 for rwxr-xr-x).
    """
    for root, dirs, _ in os.walk(path):
      for dirname in dirs:
        os.chmod(os.path.join(root, dirname), stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
        print(f"Changed permission of {os.path.join(root, dirname)} to full read write excecute access")
    os.chmod(path, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)

def pre_processing():

    LOGGER.info(f"pre-processing():")

    # clean up log file
    if not os.path.exists(LOG_FILE_NAME):
        with open(LOG_FILE_NAME, 'w') as log_file:
            log_file.write("Starting log file for AI processing loop pre-processing ...\n")

    with open(LOG_FILE_NAME, 'r') as log_file:
        log_file_content = log_file.readlines()

    if len(log_file_content) > LOG_FILE_MAX_LINES_NUMBER:
        log_file_content = log_file_content[-LOG_FILE_MAX_LINES_NUMBER:]

    with open(LOG_FILE_NAME, 'w') as log_file:
        log_file.writelines(log_file_content)

    # load config file
    LOGGER.info(f"loading config file {CONFIG_FILE_NAME} ...")
    with open(CONFIG_FILE_NAME, 'r') as stream:
        config = yaml.safe_load(stream)

    # if flag is False, stop here
    if config['ai_pre_process_running'] is False:
         LOGGER.info(f"AI pre-process (ob, 0 and 180degrees) is not running yet! We are done here")
         return

    else:
        LOGGER.info(f"AI pre-process (ob, 0 and 180 degrees) is now checking for new files!")
        # title = config['experiment_title']
        # LOGGER.info(f"experiment title: {title}")
        # proton_charge = config['proton_charge']
        # LOGGER.info(f"proton charge: {proton_charge}")
        number_of_obs = config['EIC_vals']['number_of_obs']
        LOGGER.info(f"number of obs: {number_of_obs}")
        starting_run_number = config['starting_run_number']
        LOGGER.info(f"starting run number: {starting_run_number}")
        run_number_expected = config['run_number_expected']
        LOGGER.info(f"run_number_expected: {run_number_expected}")
        list_of_runs_expected = np.arange(starting_run_number, starting_run_number + 2 + number_of_obs)
        LOGGER.info(f"{list_of_runs_expected = }")
        list_of_obs_expected = list_of_runs_expected[:-2] # OBs then 0 and 180 degrees, so we take all the runs except the last 2 to be OBs
        LOGGER.info(f"{list_of_obs_expected = }")
        LOGGER.info(f"list of obs expected: {list_of_obs_expected}")
        list_of_0_and_180_expected = list_of_runs_expected[-2:] # the last 2 runs are the 0 and 180 degrees
        LOGGER.info(f"{list_of_0_and_180_expected = }")

    # create the output path on hype
    data_path = config['DataPath']
    if not os.path.exists(data_path):
        LOGGER.info(f"creating the output path on hype: {data_path}")
        os.makedirs(data_path)

        # making sure the folder is fully accessible
        output_path = f"/data/VENUS/IPTS-{ipts}"
        LOGGER.info(f"making sure the permission to the shared folder are right!")
        change_permissions_recursive(output_path)

    # check that NeXus is there
    NEXUS_FOLDER = config['nexus_folder']
    expected_nexus_file = os.path.join(NEXUS_FOLDER, f"VENUS_{run_number_expected}.nxs.h5")
    LOGGER.info(f"checking that NeXus {expected_nexus_file} is there (acquisition of that run is done) ...")
    if not os.path.exists(expected_nexus_file):
        LOGGER.info(f"NeXus file {expected_nexus_file} not found!")
        LOGGER.info(f"... exiting move_folders.py!")
        return

    list_raw = config['marimo']['pre_processing_table']['raw']
    list_raw.append(run_number_expected)
    list_raw = set(list_raw)
    config['marimo']['pre_processing_table']['raw'] = list(list_raw)
    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)

    # if nexus is there, we can retrieve the location of the corrected MCP folder
    LOGGER.info(f"NeXus file {expected_nexus_file} found! Let's retrieve the location of the corrected MCP folder from the NeXus file ...  ")
    # retrieve the location of the corrected MCP folder from the NeXus file 
    with h5py.File(expected_nexus_file, 'r') as f:
        try:
            mcp_corrected_folder = f['entry']['DASlogs']['BL10:Exp:IM:ImageFilePath']['value'][-1][0].decode('utf-8')
        except KeyError:
            mcp_corrected_folder = f['entry']['DASlogs']['BL10:Exp:IM:ConfigTpxFilePath']['value'][0][0].decode('utf-8')
        mcp_corrected_folder = mcp_corrected_folder.strip()

    full_path_of_corrected_run_number_expected = os.path.join(MCP_FOLDER, mcp_corrected_folder)  
    LOGGER.info(f"looking at {full_path_of_corrected_run_number_expected} to find the corrected MCP folder name ...")
    LOGGER.info(f"{full_path_of_corrected_run_number_expected = }")

    if not os.path.exists(full_path_of_corrected_run_number_expected):
        LOGGER.info(f"Corrected MCP folder of run {run_number_expected} not found in {full_path_of_corrected_run_number_expected}!")
        LOGGER.info(f"... exiting move_folders.py!")
        return
    
    LOGGER.info(f"run number {run_number_expected:04d} found!")
    
    # checking if the system is done writing all the files into the raw input folder
    if not all_the_files_are_there(full_path_of_corrected_run_number_expected):
        LOGGER.info(f"not all the files are there yet!")
        LOGGER.info(f"... exiting move_folders.py!")
        return
    
    list_corrected = config['marimo']['pre_processing_table']['corrected']
    list_corrected.append(run_number_expected)
    list_corrected = set(list_corrected)
    config['marimo']['pre_processing_table']['corrected'] = list(list_corrected)
    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)
   
    LOGGER.info(f"The source folder has all the files we need!")

    LOGGER.info(f"looking at the short name of the run number expected ...")
    new_name_of_run_number_expected = get_new_short_name_of_run_number_expected(full_path_of_corrected_run_number_expected)
    LOGGER.info(f"File will be renamed {new_name_of_run_number_expected}")

    # check if folder has been renamed and copied already
    if do_we_need_to_copy_that_folder(new_name_of_run_number_expected):
        copy_and_rename_that_folder(full_path_of_corrected_run_number_expected, new_name_of_run_number_expected)

        if run_number_expected in list_of_obs_expected:
            list_of_obs = config['ob_local_path']
            list_of_obs.append(os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name_of_run_number_expected)))
            config['ob_local_path'] = list_of_obs
            with open(CONFIG_FILE_NAME, 'w') as write_out:
                yaml.dump(config, write_out, sort_keys=False)
            LOGGER.info(f"added {new_name_of_run_number_expected} to the list of obs!")
        
        if run_number_expected in list_of_0_and_180_expected:
            list_of_0_and_180 = config['0_and_180_local_path']
            list_of_0_and_180.append(os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name_of_run_number_expected)))
            config['0_and_180_local_path'] = list_of_0_and_180
            with open(CONFIG_FILE_NAME, 'w') as write_out:
                yaml.dump(config, write_out, sort_keys=False)
            LOGGER.info(f"added {new_name_of_run_number_expected} to the list of 0 and 180 degrees!")

        list_final = config['marimo']['pre_processing_table']['final']
        list_final.append(run_number_expected)
        list_final = set(list_final)
        config['marimo']['pre_processing_table']['final'] = list(list_final)
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)

    # check if we collected all the runs we wanted (2 + # of obs)
    LOGGER.info(f"checking if we collected all the runs we wanted:")
    if run_number_expected == list_of_runs_expected[-1]:

        # we can stop the pre-processing
        LOGGER.info(f"\tall runs have been collected!")
        LOGGER.info(f"stopping pre-processing!")
        config['ai_pre_process_running'] = False
        config['DataPath'] = OUTPUT_FOLDER_ON_HYPE
        LOGGER.info(f"done with pre-processing scripts!")
        #increment run_number_expected
        config['run_number_expected'] += 1
        config['working_with_first_processing_angles'] = False  # next time we will look for 'step' number of files
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)

        # copying the config file to the output folder
        LOGGER.info(f"copying the config file to the output folder /data/VENUS/shared.")
        LOGGER.info(f"\t{CONFIG_FILE_NAME =}")
        path_copied = shutil.copy(CONFIG_FILE_NAME, "/data/VENUS/shared")
        LOGGER.info(f"done with {path_copied}")

        # we need to define the top_projections_folder_name
     
        shutil.copy(CONFIG_FILE_NAME, "~/")
        
        # os.system("/data/VENUS/shared/software/auto_gen_run_scrs/ini_exp_hype.sh")
        subprocess.run(["/data/VENUS/shared/software/auto_gen_run_scrs/ini_exp_hype.sh"])


    else:
        LOGGER.info(f"\twe are not done yet!")
        #increment run_number_expected
        config['run_number_expected'] += 1
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)
        LOGGER.info(f"incrementing run_number_expected ...")
        LOGGER.info(f"next run number expected: {config['run_number_expected']}")


if __name__ == "__main__":
    _LOG_FILE_NAME = PROJECT_ROOT_FOLDER / "logs" / f"{file_name}_{ipts}.log"
    LOGGER.info(f"*** Starting checking for new files - version {version}")
    print(f"check log file at {_LOG_FILE_NAME}")
	
    parser = argparse.ArgumentParser(description='Check for new files and move them to the output folder',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', action='store_true', default=False, help='Flag to turn on pre-processing')

    args = parser.parse_args()

    pre_processing_flag = args.p
    if pre_processing_flag:
        LOGGER.info(f"pre-processing is ON!")
        pre_processing()
    else:
        processing()
