import logging
import os
import yaml
import glob
import shutil
import subprocess
import argparse
import numpy as np

LOG_FILE_MAX_LINES_NUMBER = 1000

PROJECT_ROOT_FOLDER = "/SNS/VENUS/IPTS-35790/shared/hype"
file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/logs/{file_name}.log"

# MCP_FOLDER = '/SNS/VENUS/IPTS-35790/images/mcp/images'
# OUTPUT_FOLDER_ON_HYPE = "/data/VENUS/IPTS-35790/images/mcp/2025_03_07/"

# DEBUG_MCP_FOLDER = '/SNS/VENUS/IPTS-35790/shared/ai_test_data/images/mcp'
# DEBUG_OUPUT_FOLDER_ON_HYPE = "/data/VENUS/IPTS-35790/images/mcp/2025_03_07/"

LAUNCH_SHIMIN_SCRIPT_EVERY_N_FILES = 3
SHIMIN_CODE = "/data/VENUS/IPTS-35790/shared/software/run/run_ai_loop.sh"

# OUTPUT_ROOT_FOLDER = '/SNS/VENUS/IPTS-33531/images/mcp/'
# REDUCED_FOLDER = '/SNS/VENUS/IPTS-33531/shared/autoreduce/mcp/'

# CLUSTER_CONFIG_FOLDER = "/storage/VENUS/IPTS-33531/shared/ai"

CONFIG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/configs/config.yaml"
with open(CONFIG_FILE_NAME, 'r') as stream:
    config = yaml.safe_load(stream)

debugging_flag = config['debugging']


if debugging_flag:
    MCP_FOLDER = config['debugging_mcp_folder']
    OUTPUT_FOLDER_ON_HYPE = config['debugging_output_folder_on_hype']
else:
    MCP_FOLDER = config['mcp_folder']
    OUTPUT_FOLDER_ON_HYPE = config['DataPath']

CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER = f"{PROJECT_ROOT_FOLDER}/logs/list_of_runs_found_in_folder.yaml"


def get_list_basename(list_full_folder_name):
    return [os.path.basename(_folder) for _folder in list_full_folder_name]


def copy_and_rename_that_folder(folder_to_move, new_name):
    # copy folder_to_move to OUTPUT_FOLDER_ON_HYPE
    logging.info(f"copying/renaming {folder_to_move} to {OUTPUT_FOLDER_ON_HYPE} with new name {new_name} ...")
    shutil.copytree(folder_to_move, os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name)))
    # change the permission of the copied file
    logging.info(f"changing the permission of the copied file (-r 777)")
    subprocess.run(["chmod", "-R", "777", os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name))])
    logging.info(f"done!")


def do_we_need_to_copy_that_folder(folder_to_copy):
    # check if the folder has already been copied and renamed
    # _base_name = os.path.basename(folder_to_copy)
    if os.path.exists(os.path.join(OUTPUT_FOLDER_ON_HYPE, folder_to_copy)):
        logging.info(f"{folder_to_copy} has already been copied!")
        return False
    else:
        logging.info(f"{folder_to_copy} has not been copied yet!")
        return True


def get_new_short_name_of_run_number_expected(full_path_of_run_number_expected):
    """will look for the first tiff file in the full_path_of_run_number_expected folder and will make up the new name
    ex: 20250312_Run_7287_testing_the_eic_loop_pre_exp_test_00_10C_Angle_090_000deg_000_1914480.tiff
    new name: 20250312_Run_7287_testing_the_eic_loop_pre_exp_test_00_10C_Angle_090_000deg_000"""

    list_tiff = glob.glob(f"{full_path_of_run_number_expected}/tpx3/*.tif*")    # add tpx3 for real case
    list_tiff.sort()
    first_file = os.path.basename(list_tiff[0])
    splitted_first_file = first_file.split("_")
    new_name = "_".join(splitted_first_file[:-1])
    return new_name


def  all_the_files_are_there(full_path_of_run_number_expected):
    logging.info(f"checking if the system is done writing all the files ...")
    list_of_files = glob.glob(f"{full_path_of_run_number_expected}/tpx3/*.tif*")   # add/remove /tpx3 for real case
    logging.info(f"number of files found: {len(list_of_files)}")
    number_of_files_for_each_run_expected = config['number_of_tiff_for_each_run']
    logging.info(f"number of files expected: {number_of_files_for_each_run_expected}")
    if len(list_of_files) < number_of_files_for_each_run_expected:
        return False
    return True


def processing():
    
     # load config file
    with open(CONFIG_FILE_NAME, 'r') as stream:
        config = yaml.safe_load(stream)

     # if flag is False, stop here
    if config['ai_process_running'] is False:
        logging.info(f"AI process is not running yet!")
        logging.info(f"... exiting the processing script!")
        return

    logging.info(f"debugging mode: {debugging_flag}")
    logging.info(f"MCP_FOLDER: {MCP_FOLDER}")
    logging.info(f"OUTPUT_FOLDER_ON_HYPE: {OUTPUT_FOLDER_ON_HYPE}")

    logging.info(f"AI process is now checking for new files!")
    run_number_expected = config['run_number_expected']
    logging.info(f"run_number_expected: {run_number_expected}")
    number_of_files_to_expect = config['step']
    logging.info(f"number_of_files_to_expect: {number_of_files_to_expect}")

    # check if run number expected showed up in the folder
    list_of_runs_expected = np.arange(run_number_expected, run_number_expected + number_of_files_to_expect)
    logging.info(f"{list_of_runs_expected = }")

    list_full_path_of_run_number_expected = [os.path.join(MCP_FOLDER, f"Run_{_run_expected:04d}") for _run_expected in list_of_runs_expected]
    logging.info(f"{list_full_path_of_run_number_expected = }")

    for _full_path_run_expected in list_full_path_of_run_number_expected:
        logging.info(f"looking for {os.path.basename(_full_path_run_expected)}")
        if not os.path.exists(_full_path_run_expected):
            logging.info(f"{os.path.basename(_full_path_run_expected)} not found!")
            logging.info(f"... exiting processing.py!")
            return
        else:
            logging.info(f"{os.path.basename(_full_path_run_expected)} found!")

    logging.info(f"All the runs expected have been found and we can copy/rename them!")

    # check if all files required are in the respective folders
    for _full_path_run_expected in list_full_path_of_run_number_expected:

        # is the system done writing all the files
        if not all_the_files_are_there(_full_path_run_expected):
            logging.info(f"not all the files are there yet!")
            logging.info(f"... exiting processing.py!")
            return
        else:
            logging.info(f"all the files required have been written for {os.path.basename(_full_path_run_expected)}!")   

    # check if folder has been copied already
    for _full_path_run_expected in list_full_path_of_run_number_expected:
        new_name_of_run_number_expected = get_new_short_name_of_run_number_expected(_full_path_run_expected)
        logging.info(f"File will be renamed {new_name_of_run_number_expected}")
        if not do_we_need_to_copy_that_folder(new_name_of_run_number_expected):
            logging.info(f"{os.path.basename(_full_path_run_expected)} has already been copied!")
            logging.info(f"... exiting processing.py!")
        else:
            copy_and_rename_that_folder(_full_path_run_expected, new_name_of_run_number_expected)

    # launch Shimin's script #2
    logging.info(f"launching Shimin's script ...")
    logging.info(f"SHIMIN_CODE = {SHIMIN_CODE}")
    os.system(SHIMIN_CODE)
    
    # update value of next run number expected
    config['run_number_expected'] += number_of_files_to_expect
    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)        
    

def pre_processing():

    # clean up log file
    with open(LOG_FILE_NAME, 'r') as log_file:
        log_file_content = log_file.readlines()

    if len(log_file_content) > LOG_FILE_MAX_LINES_NUMBER:
        log_file_content = log_file_content[-LOG_FILE_MAX_LINES_NUMBER:]

    with open(LOG_FILE_NAME, 'w') as log_file:
        log_file.writelines(log_file_content)

    # load config file
    with open(CONFIG_FILE_NAME, 'r') as stream:
        config = yaml.safe_load(stream)

    # if flag is False, stop here
    if config['ai_pre_process_running'] is False:
         logging.info(f"AI pre-process (ob, 0 and 180degrees) is not running yet!")
         logging.info(f"... exiting the run_autoreduction_and_move_folders.py!")
         return
    else:
        logging.info(f"AI pre-process (ob, 0 and 180 degrees) is now checking for new files!")
        # title = config['experiment_title']
        # logging.info(f"experiment title: {title}")
        # proton_charge = config['proton_charge']
        # logging.info(f"proton charge: {proton_charge}")
        number_of_obs = config['EIC_vals']['number_of_obs']
        logging.info(f"number of obs: {number_of_obs}")
        starting_run_number = config['starting_run_number']
        logging.info(f"starting run number: {starting_run_number}")
        run_number_expected = config['run_number_expected']
        logging.info(f"run_number_expected: {run_number_expected}")
        list_of_runs_expected = np.arange(starting_run_number, starting_run_number + 2 + number_of_obs)
        logging.info(f"{list_of_runs_expected = }")
        list_of_obs_expected = list_of_runs_expected[:-2]
        logging.info(f"{list_of_obs_expected = }")

    # check if run number expected showed up in the folder
    logging.info(f"looking at {MCP_FOLDER}/Run_{run_number_expected:04d}")
    full_path_of_run_number_expected = os.path.join(MCP_FOLDER, f"Run_{run_number_expected:04d}")
    logging.info(f"{full_path_of_run_number_expected = }")

    if not os.path.exists(full_path_of_run_number_expected):
        logging.info(f"Run_{run_number_expected:04d} not found!")
        logging.info(f"... exiting move_folders.py!")
        return
    
    logging.info(f"Run_{run_number_expected:04d} found!")

    # checking if the system is done writing all the files into the raw input folder
    if not all_the_files_are_there(full_path_of_run_number_expected):
        logging.info(f"not all the files are there yet!")
        logging.info(f"... exiting move_folders.py!")
        return
       
    logging.info(f"The source folder has all the files we need!")

    logging.info(f"looking at the short name of the run number expected ...")
    new_name_of_run_number_expected = get_new_short_name_of_run_number_expected(full_path_of_run_number_expected)
    logging.info(f"File will be renamed {new_name_of_run_number_expected}")

    # check if folder has been renamed and copied already
    if do_we_need_to_copy_that_folder(new_name_of_run_number_expected):
        copy_and_rename_that_folder(full_path_of_run_number_expected, new_name_of_run_number_expected)

        if run_number_expected in list_of_obs_expected:
            list_of_obs = config['ob_local_path']
            list_of_obs.append(os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(new_name_of_run_number_expected)))
            config['ob_local_path'] = list_of_obs
            with open(CONFIG_FILE_NAME, 'w') as write_out:
                yaml.dump(config, write_out, sort_keys=False)
            logging.info(f"added {new_name_of_run_number_expected} to the list of obs!")
        
    # check if we collected all the runs we wanted (2 + # of obs)
    logging.info(f"checking if we collected all the runs we wanted:")
    if run_number_expected == list_of_runs_expected[-1]:

        # we can stop the pre-processing
        logging.info(f"\tall runs have been collected!")
        logging.info(f"stopping pre-processing!")
        config['ai_pre_process_running'] = False
        config['DataPath'] = OUTPUT_FOLDER_ON_HYPE
        logging.info(f"done with pre-processing scripts!")
        #increment run_number_expected
        config['run_number_expected'] += 1
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)

        # copying the config file to the output folder
        logging.info(f"copying the config file to the output folder ...")
        shutil.copy(CONFIG_FILE_NAME, OUTPUT_FOLDER_ON_HYPE)
        logging.info(f"done!")

    else:
        logging.info(f"\twe are not done yet!")
        #increment run_number_expected
        config['run_number_expected'] += 1
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)
        logging.info(f"incrementing run_number_expected ...")
        logging.info(f"next run number expected: {config['run_number_expected']}")


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE_NAME,
						filemode='a',  # 'w'
						format="[%(levelname)s] - %(asctime)s - %(message)s",
						level=logging.INFO)
    logging.info("*** Starting checking for new files - version 03/06/2025")
    print(f"check log file at {LOG_FILE_NAME}")
	
    parser = argparse.ArgumentParser(description='Check for new files and move them to the output folder',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', action='store_true', default=False, help='Flag to turn on pre-processing')

    args = parser.parse_args()

    pre_processing_flag = args.p
    if pre_processing_flag:
        logging.info(f"pre-processing is ON!")
        pre_processing()
    else:
        processing()
