import logging
import os
import yaml
import glob
import shutil
import subprocess

LOG_FILE_MAX_LINES_NUMBER = 1000

OUTPUT_ROOT_FOLDER = '/SNS/VENUS/IPTS-33531/images/mcp/'
# REDUCED_FOLDER = '/SNS/VENUS/IPTS-33531/shared/autoreduce/mcp/'

DEBUG_MCP_FOLDER = '/SNS/VENUS/IPTS-33531/shared/debugging_ai/images/mcp'
MCP_FOLDER = '/SNS/VENUS/IPTS-33531/images/mcp/'

OUTPUT_FOLDER_ON_HYPE = "/data/VENUS/IPTS-35790/images/mcp/2025_03_07"

PROJECT_ROOT_FOLDER = "/SNS/VENUS/IPTS-33531/shared/ai_output"

file_name, ext = os.path.splitext(os.path.basename(__file__))
LOG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/logs/{file_name}.log"

CLUSTER_CONFIG_FOLDER = "/storage/VENUS/IPTS-33531/shared/ai"

cmd = 'mcp_detector_correction.py --skipimg '

CONFIG_FILE_NAME = f"{PROJECT_ROOT_FOLDER}/configs/config.yaml"
with open(CONFIG_FILE_NAME, 'r') as stream:
    config = yaml.safe_load(stream)

debugging_flag = config['debugging']

if debugging_flag:
    MCP_FOLDER = DEBUG_MCP_FOLDER

CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER = f"{PROJECT_ROOT_FOLDER}/logs/list_of_runs_found_in_folder.yaml"


def get_list_basename(list_full_folder_name):
    return [os.path.basename(_folder) for _folder in list_full_folder_name]


def we_need_to_reduce_that_folder(folder_name):
    """this checks if the folder exists and if there are tif* files in it """
    
    logging.info(f"checking if we need to reduce {folder_name}:")

    if not os.path.exists(folder_name):
        logging.info(f"\tdoes not exist, we need to reduce it!")
        return True
    
    # check that they are as many runs on the raw and reduce sides
    basename = os.path.basename(folder_name)
    full_name_raw_side = os.path.join(OUTPUT_ROOT_FOLDER, basename)
    full_name_reduced_side = os.path.join(REDUCED_FOLDER, basename)
    
    list_runs_raw_side = glob.glob(os.path.join(full_name_raw_side, "Run_*"))
    list_runs_reduced_side = glob.glob(os.path.join(full_name_reduced_side, "Run_*"))

    # different number of runs between raw and reduced
    if len(list_runs_reduced_side) != len(list_runs_raw_side):
        logging.info(f"\tdifferent number of runs between reduced and raw, we need to reduce it!")
        return True

    # no runs found in reduced side
    if len(list_runs_reduced_side) == 0:
        logging.info(f"\tno runs found in folder, we need to reduce it!")
        return True

    # same number of runs but maybe some folders are empty
    for _run in list_runs_reduced_side:
        list_tiff = glob.glob(os.path.join(_run, "*.tif*"))
        logging.info(f"\tchecking number of tiff images in {_run}")
        if len(list_tiff) == 0:
            logging.info(f"\t\t0 tiff found, we need to reduce it!")
            return True

    logging.info(f"\tno need to reduce it!")
    return False


def main():

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

    # flag is ON, keep going

    # check if any of the output folders (ob and projections) has been created yet
    projections_folder_prefix = os.path.join(MCP_FOLDER, config['experiment_title'])
    ob_folder_prefix = os.path.join(MCP_FOLDER, f"OB_{config['experiment_title']}")

    list_of_projections_folders_raw = glob.glob(projections_folder_prefix + "_*")
    list_of_ob_folders_raw = glob.glob(ob_folder_prefix + "_*")

    # no folder starting with those prefixes was found
    if (len(list_of_projections_folders_raw) == 0) and (len(list_of_ob_folders_raw) == 0):
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
            config['list_of_runs_reduced'] = []
            
        with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'w') as outfile:
            yaml.dump(config_list_of_runs_found, outfile, sort_keys=False)
   
        logging.info(f"... exiting the run_autoreduction_and_move_folders.py!")
        return
  
    logging.info(f"we found at least one folder with the prefix {projections_folder_prefix} or {ob_folder_prefix}")

    # at least one of the output folder was found, so we can continue

    # with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'r') as stream:
    #     config_list_of_runs_found = yaml.safe_load(stream)
    #     previous_list_of_projection_folders = config_list_of_runs_found['projections']
    #     previous_list_of_ob_folders = config_list_of_runs_found['ob']

    logging.info(f"looking at projections in reduced folder {os.path.join(REDUCED_FOLDER, projections_folder_prefix) + '*'}")
    list_of_projections_folders_reduced = glob.glob(os.path.join(REDUCED_FOLDER, projections_folder_prefix) + "*")
    logging.info(f"{list_of_projections_folders_reduced = }")
    logging.info(f"{list_of_projections_folders_raw = }")

    logging.info(f"looking at previous obs in {os.path.join(REDUCED_FOLDER, ob_folder_prefix) + '*'}")
    list_of_ob_folders_reduced = glob.glob(os.path.join(REDUCED_FOLDER, ob_folder_prefix) + "*")
    logging.info(f"{list_of_ob_folders_reduced = }")
    logging.info(f"{list_of_ob_folders_raw =}")

    # will keep record of the new folder that need to be reduced
    list_folders_found = []
  
    logging.info(f"")
    logging.info(f"Looking at runs that were not reduced yet!")

    # at least one projection output folder found
    logging.info(f"{list_of_projections_folders_raw = }")
    if len(list_of_projections_folders_raw) > 0:
        if len(list_of_projections_folders_reduced) == 0:
            logging.info(f"new projection(s) folders found: {get_list_basename(list_of_projections_folders_raw)}")
            list_folders_found = list_of_projections_folders_raw
        else:
            list_folders_found += list_of_projections_folders_raw
            # for _folder in list_new_folders_found:
                # if _folder in list_of_projections_folders_reduced:
                #     continue
                # else:
                # list_new_folders_found.append(_folder)
        logging.info(f"{list_folders_found = }")
    else:
        logging.info(f"no list of projection folders found!")
    
    # looking at ob output folder
    logging.info(f"{list_of_ob_folders_raw = }")
    if len(list_of_ob_folders_raw) > 0:
        if len(list_of_ob_folders_reduced) == 0:
            list_folders_found += list_of_ob_folders_raw
            logging.info(f"new ob folders found: {get_list_basename(list_of_ob_folders_raw)}")
        else:
            list_folders_found += list_of_ob_folders_raw
            # for _folder in list_new_folders_found:
                # if _folder in list_of_ob_folders_reduced:
                #     continue
                # else:
                #     list_new_folders_found.append(_folder)
        logging.info(f"{list_folders_found = }")
    else:
        logging.info(f"no list of ob folders found!")

    list_new_folders_to_reduce = []
    if len(list_folders_found) > 0:
        logging.info(f"we need to check if those runs have already been reduced!")
        for _folder in list_folders_found:
            _base_name = os.path.basename(_folder)
            _reduced_folder_name = os.path.join(REDUCED_FOLDER, _base_name)
            if we_need_to_reduce_that_folder(_reduced_folder_name):
                list_new_folders_to_reduce.append(_folder)
            else:
                logging.info(f"\tNO need to reduce {_base_name}!")

    logging.info(f"we need to reduce {len(list_new_folders_to_reduce)} folder(s)!")
    for _folder in list_new_folders_to_reduce:
        logging.info(f"\t{os.path.basename(_folder)}")

    # launching auto_reduction of that folder
    for _folder_to_reduce in list_new_folders_to_reduce:

        base_name_folder_to_reduce = os.path.basename(_folder_to_reduce)

        # find run
        list_runs = glob.glob(os.path.join(_folder_to_reduce, "Run_*"))
        for run in list_runs:
            logging.info(f"about to reduce {run}!")
            output_folder = os.path.join(REDUCED_FOLDER, base_name_folder_to_reduce, os.path.basename(run))
            logging.info(f"\t{output_folder = }")
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            input_folder = os.path.join(run, 'tpx')

            full_cmd = f"{cmd} {input_folder} {output_folder}"
            logging.info(f"\t{full_cmd = }")
            proc = subprocess.Popen(full_cmd,
                                    shell=True,
                                    stdin=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True,
                                    cwd=output_folder)
            std_out, std_err = proc.communicate()
            logging.info(f"\t{std_out = }")
            logging.info(f"\t{std_err = }")
            
            if not std_err:
                logging.info(f"reduction done!")
                final_destination = os.path.join(OUTPUT_FOLDER_ON_HYPE, base_name_folder_to_reduce, os.path.basename(run))
                logging.info(f"copying folder {output_folder} to {final_destination} ...")
            
                if os.path.exists(final_destination):
                    shutil.rmtree(final_destination)

                shutil.copytree(output_folder, final_destination)
                logging.info(f"\tdone!")

            else:
                logging.info(f"FAILED!")
                continue

            config['list_of_runs_reduced'].append(os.path.basename(os.path.dirname(run)))

            # update number of runs reduced - this way the notebook will know when to continue
            config['number_of_runs_reduced_and_moved'] += 1

            if config['ai_pre_process_running']:
                if config['number_of_runs_reduced_and_moved'] == (config['number_of_obs'] + 2):
                    config['ai_pre_process_running'] = False
                  
    # update list of folders found
    current_list_of_projections_folders = glob.glob(projections_folder_prefix + "_*")
    current_list_of_ob_folders = glob.glob(ob_folder_prefix + "_*")
    with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'r') as stream:
        config_list_of_runs_found = yaml.safe_load(stream)
        config_list_of_runs_found['ob'] = current_list_of_ob_folders
        config_list_of_runs_found['projections'] = current_list_of_projections_folders
        
    with open(CONFIG_LIST_OF_RUNS_FOUND_IN_FOLDER, 'w') as outfile:
        yaml.dump(config_list_of_runs_found, outfile, sort_keys=False)

    # copy name of projections into config
    # current_list_of_projections_folders

    with open(CONFIG_FILE_NAME, 'w') as write_out:
        yaml.dump(config, write_out, sort_keys=False)

    # copy config file to final destination
    logging.info(f"copying the config file {CONFIG_FILE_NAME} to hype {CLUSTER_CONFIG_FOLDER}")
    shutil.copy(CONFIG_FILE_NAME, CLUSTER_CONFIG_FOLDER)


if __name__ == "__main__":
	logging.basicConfig(filename=LOG_FILE_NAME,
						filemode='a',  # 'w'
						format="[%(levelname)s] - %(asctime)s - %(message)s",
						level=logging.INFO)
	logging.info("*** Starting checking for new files - version 03/06/2025")
	main()
