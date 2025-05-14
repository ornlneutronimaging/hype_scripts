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

MCP_FOLDER = '/SNS/VENUS/IPTS-35790/images/mcp/images'
OUTPUT_FOLDER_ON_HYPE = "/data/VENUS/IPTS-35790/images/mcp/2025_03_07/"

DEBUG_MCP_FOLDER = '/SNS/VENUS/IPTS-35790/shared/debugging_ai/images/mcp'
DEBUG_OUPUT_FOLDER_ON_HYPE = "/SNS/VENUS/IPTS-35790/shared/debugging_ai/images/mcp/debugging_hype/"

LAUNCH_SHIMIN_SCRIPT_EVERY_N_FILES = 3
SHIMIN_CODE = "/SNS/users/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/run_ai_loop.sh"

# OUTPUT_ROOT_FOLDER = '/SNS/VENUS/IPTS-33531/images/mcp/'
# REDUCED_FOLDER = '/SNS/VENUS/IPTS-33531/shared/autoreduce/mcp/'

# CLUSTER_CONFIG_FOLDER = "/storage/VENUS/IPTS-33531/shared/ai"

cmd = 'mcp_detector_correction.py --skipimg '

CONFIG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/configs/config.yaml"
with open(CONFIG_FILE_NAME, 'r') as stream:
    config = yaml.safe_load(stream)

debugging_flag = config['debugging']

if debugging_flag:
    MCP_FOLDER = DEBUG_MCP_FOLDER
    OUTPUT_FOLDER_ON_HYPE = DEBUG_OUPUT_FOLDER_ON_HYPE

CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER = f"{PROJECT_ROOT_FOLDER}/logs/list_of_runs_found_in_folder.yaml"


def get_list_basename(list_full_folder_name):
    return [os.path.basename(_folder) for _folder in list_full_folder_name]


def copy_that_folder(folder_to_move):
    # copy folder_to_move to OUTPUT_FOLDER_ON_HYPE
    logging.info(f"moving {folder_to_move} to {OUTPUT_FOLDER_ON_HYPE} ...")
    shutil.copytree(folder_to_move, os.path.join(OUTPUT_FOLDER_ON_HYPE, os.path.basename(folder_to_move)))
    logging.info(f"done!")


def do_we_need_to_copy_that_folder(folder_to_copy):
    # check if the folder has already been moved
    _base_name = os.path.basename(folder_to_copy)
    if os.path.exists(os.path.join(OUTPUT_FOLDER_ON_HYPE, _base_name)):
        logging.info(f"{_base_name} has already been copied!")
        return False
    else:
        logging.info(f"{_base_name} has not been copied yet!")
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

    logging.info(f"AI process is now checking for new files!")
    run_number_expected = config['run_number_expected']
    logging.info(f"run_number_expected: {run_number_expected}")
    number_of_files_to_expect = config['step']
    logging.info(f"number_of_files_to_expect: {number_of_files_to_expect}")

    # check if run number expected showed up in the folder
    list_of_runs_expected = np.arange(run_number_expected, run_number_expected + number_of_files_to_expect+1)
    logging.info(f"{list_of_runs_expected = }")

    list_full_path_of_run_number_expected = [os.path.join(MCP_FOLDER, f"Run_{_run_expected:04d}") for _run_expected in list_of_runs_expected]

    for _full_path_run_expected in list_full_path_of_run_number_expected:
        logging.info(f"looking {os.path.basename(_full_path_run_expected)}")
        if not os.path.exists(_full_path_run_expected):
            logging.info(f"{os.path.basename(_full_path_run_expected)} not found!")
            logging.info(f"... exiting processing.py!")
            return

    logging.info(f"All the runs expected have been found and we can copy them!")

    # check if folder has been copied already
    for _full_path_run_expected in list_full_path_of_run_number_expected:
        if not do_we_need_to_copy_that_folder(_full_path_run_expected):
            logging.info(f"{os.path.basename(_full_path_run_expected)} has already been copied!")
            logging.info(f"... exiting processing.py!")
        else:
            copy_that_folder(_full_path_run_expected)

    # launch Shimin's script #2
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
        title = config['experiment_title']
        logging.info(f"experiment title: {title}")
        proton_charge = config['proton_charge']
        logging.info(f"proton charge: {proton_charge}")
        number_of_obs = config['number_of_obs']
        logging.info(f"number of obs: {number_of_obs}")
        starting_run_number = config['starting_run_number']
        logging.info(f"starting run number: {starting_run_number}")
        run_number_expected = config['run_number_expected']
        logging.info(f"run_number_expected: {run_number_expected}")

    # check if run number expected showed up in the folder
    logging.info(f"looking at {MCP_FOLDER}/Run_{run_number_expected:04d}")
    full_path_of_run_number_expected = os.path.join(MCP_FOLDER, f"Run_{run_number_expected:04d}")
    logging.info(f"{full_path_of_run_number_expected = }")

    if not os.path.exists(full_path_of_run_number_expected):
        logging.info(f"Run_{run_number_expected:04d} not found!")
        logging.info(f"... exiting move_folders.py!")
        return
    
    logging.info(f"Run_{run_number_expected:04d} found!")

    # check if folder has been copied already
    if not do_we_need_to_copy_that_folder(full_path_of_run_number_expected):
        logging.info(f"Run_{run_number_expected:04d} has already been copied!")
        logging.info(f"... exiting copy_that_folder.py!")
        return

    # copy folder to output folder
    copy_that_folder(full_path_of_run_number_expected)

    # check if we collected all the runs we wanted (2 + # of obs)
    if run_number_expected - starting_run_number + 1 >= 2 + number_of_obs:
        # we can stop the pre-processing
        logging.info(f"all runs have been collected!")
        logging.info(f"stopping pre-processing!")
        config['ai_pre_process_running'] = False
        with open(CONFIG_FILE_NAME, 'w') as write_out:
            yaml.dump(config, write_out, sort_keys=False)
        logging.info(f"... done with pre-processing scripts!")
        return
    

def processing():

    # load config file
    with open(CONFIG_FILE_NAME, 'r') as stream:
        config = yaml.safe_load(stream)





    # update value of next run number expected
    config['run_number_expected'] += 1
    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)

    return


    
    list_of_projections_folders_source = glob.glob(projections_folder_prefix + "_*")
    list_of_ob_folders_source = glob.glob(ob_folder_prefix + "_*")

    # no folders starting with those prefixes were found
    if (len(list_of_projections_folders_source) == 0) and (len(list_of_ob_folders_source) == 0):
        logging.info(f"looking at {projections_folder_prefix}_*")
        logging.info(f"no folder {os.path.basename(projections_folder_prefix)}_* found!")
        logging.info(f"looking at {ob_folder_prefix}_*")
        logging.info(f"no ob folder {os.path.basename(ob_folder_prefix)}_* found!")
    
        # we can reset the list_of_runs_found_in_folder.yaml file
        logging.info(f"reset file {CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER}!")
        with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'r') as stream:
            config_list_of_runs_found = yaml.safe_load(stream)
            config_list_of_runs_found['ob'] = None
            config_list_of_runs_found['projections'] = None
            config_list_of_runs_found['batch_list_of_files_to_process'] = []
            
        with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'w') as outfile:
            yaml.dump(config_list_of_runs_found, outfile, sort_keys=False)
   
        logging.info(f"... exiting move_folders.py!")
        return
  
    logging.info(f"we found at least one folder with the prefix {projections_folder_prefix} or {ob_folder_prefix}")

    # at least one of the output folder was found, so we can continue

    # with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'r') as stream:
    #     config_list_of_runs_found = yaml.safe_load(stream)
    #     previous_list_of_projection_folders = config_list_of_runs_found['projections']
    #     previous_list_of_ob_folders = config_list_of_runs_found['ob']

    # looking at projections and obs already moved

    logging.info(f"looking at projections in reduced folder {os.path.join(OUTPUT_FOLDER_ON_HYPE, projections_folder_prefix) + '*'}")
    list_of_projections_folders_moved = glob.glob(os.path.join(OUTPUT_FOLDER_ON_HYPE, projections_folder_prefix) + "*")
    logging.info(f"{list_of_projections_folders_moved = }")
    logging.info(f"{list_of_projections_folders_source = }")

    if pre_processing_flag:
        logging.info(f"looking at previous obs in {os.path.join(OUTPUT_FOLDER_ON_HYPE, ob_folder_prefix) + '*'}")
        list_of_ob_folders_reduced = glob.glob(os.path.join(OUTPUT_FOLDER_ON_HYPE, ob_folder_prefix) + "*")
        logging.info(f"{list_of_ob_folders_moved = }")
        logging.info(f"{list_of_ob_folders_source =}")

    # will keep record of the new folder that need to be reduced
    list_folders_found = []
  
    logging.info(f"")
    logging.info(f"Looking at runs that were not moved yet!")

    # at least one projection output folder found
    logging.info(f"{list_of_projections_folders_source = }")
    if len(list_of_projections_folders_source) > 0:
        if len(list_of_projections_folders_moved) == 0:
            logging.info(f"new projection(s) folders found: {get_list_basename(list_of_projections_folders_source)}")
            list_folders_found = list_of_projections_folders_source
        else:
            list_folders_found += list_of_projections_folders_source
            # for _folder in list_new_folders_found:
                # if _folder in list_of_projections_folders_reduced:
                #     continue
                # else:
                # list_new_folders_found.append(_folder)
        logging.info(f"{list_folders_found = }")
    else:
        logging.info(f"no list of projection folders found!")
    
    if pre_processing_flag:
        # looking at ob output folder
        logging.info(f"{list_of_ob_folders_source = }")
        if len(list_of_ob_folders_source) > 0:
            if len(list_of_ob_folders_moved) == 0:
                list_folders_found += list_of_ob_folders_source
                logging.info(f"new ob folders found: {get_list_basename(list_of_ob_folders_source)}")
            else:
                list_folders_found += list_of_ob_folders_source
                # for _folder in list_new_folders_found:
                    # if _folder in list_of_ob_folders_reduced:
                    #     continue
                    # else:
                    #     list_new_folders_found.append(_folder)
            logging.info(f"{list_folders_found = }")
        else:
            logging.info(f"no list of ob folders found!")

    # check if we need to move the folders found
    list_folders_moved = []
    if len(list_folders_found) > 0:
        logging.info(f"we need to check if those runs have already been moved!")
        for _folder in list_folders_found:
            _base_name = os.path.basename(_folder)
            if do_we_need_to_move_that_folder(_folder):
                move_that_folder(_folder)
                list_folders_moved.append(_folder)
            else:
                logging.info(f"\tNO need to move {_base_name}!")
  
    # update list of folders found
    current_list_of_projections_folders = glob.glob(projections_folder_prefix + "_*")
    current_list_of_ob_folders = glob.glob(ob_folder_prefix + "_*")
    with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'r') as stream:
        config_list_of_runs_found = yaml.safe_load(stream)
        config_list_of_runs_found['ob'] = current_list_of_ob_folders
        config_list_of_runs_found['projections'] = current_list_of_projections_folders

        batch_list_of_files_to_process = config_list_of_runs_found['batch_list_of_files_to_process']
        if len(batch_list_of_files_to_process) + len(list_folders_moved) >= LAUNCH_SHIMIN_SCRIPT_EVERY_N_FILES:
            # run Shimin's script
            os.system(SHIMIN_CODE)
            config_list_of_runs_found['batch_list_of_files_to_process'] = []
        else:
            config_list_of_runs_found['batch_list_of_files_to_process'] += list_folders_moved

    with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'w') as outfile:
        yaml.dump(config_list_of_runs_found, outfile, sort_keys=False)

            # config['ai_process_paused'] =  False
            # with open(CONFIG_FILE_NAME, 'w') as write_out:
            #     yaml.dump(config, write_out, sort_keys=False)

            # batch_list_of_files_to_process += list_folders_moved
            # config_list_of_runs_found['batch_list_of_files_to_process'] = batch_list_of_files_to_process

    # copy name of projections into config
    # current_list_of_projections_folders

    # with open(CONFIG_FILE_NAME, 'w') as write_out:
    #     yaml.dump(config, write_out, sort_keys=False)

    # if not pre_processing_flag:
    #     # reactivate next cronjob
    #     config['ai_process_paused'] =  False
    #     with open(CONFIG_FILE_NAME, 'w') as write_out:
    #         yaml.dump(config, write_out, sort_keys=False)


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE_NAME,
						filemode='a',  # 'w'
						format="[%(levelname)s] - %(asctime)s - %(message)s",
						level=logging.INFO)
    logging.info("*** Starting checking for new files - version 03/06/2025")
    print(f"check log file at {LOG_FILE_NAME}")
	
    parser = argparse.ArgumentParser(description='Check for new files and move them to the output folder',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--pre_processing', type=bool, default=True, help='Flag to turn on pre-processing')

    args = parser.parse_args()

    pre_processing_flag = args.pre_processing
    if pre_processing_flag:
        logging.info(f"pre-processing is ON!")
        pre_processing()
    else:
        processing()
