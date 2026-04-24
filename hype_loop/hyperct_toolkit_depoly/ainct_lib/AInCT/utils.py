import os
import numpy as np
from .EICClient import EICClient
import re

def extract_angle_from_name(folder_name):
    """
    Extract angle information from a folder name using "Ang" as the marker.
    
    Folder name examples:
        - 20251122_Run_15050_Pea1_adj_BioC_Ring_10_000s_0_700AngsMin_Ang_180_000
        - 20251122_Run_132_052_Pea1_XYZ_Ang_132_052
        - 20251122_Run_12_35_Adj_BioC_Angs_Ang_12_35
        - 20251122_Run_15_Pea1_XYZ_Ang_15

    Args:
        folder_name (str): Name of the folder.

    Returns:
        float: Extracted angle value as a floating-point number.
    """
    # Regular expression to locate "Ang_" and extract two numbers separated by "_"
    match = re.search(r"Ang_(\d+)_(\d+)", folder_name)
    if match:
        constant_part = int(match.group(1))  # The constant portion (before decimal)
        fractional_part = int(match.group(2)) / (10 ** len(match.group(2)))  # The decimal portion
        return constant_part + fractional_part
    
    # Case where there's no fractional part for the angle
    match = re.search(r"Ang_(\d+)", folder_name)
    if match:
        return float(match.group(1))  # Return the whole number if no decimal
    
    raise ValueError(f"Unable to extract angle information from folder name: {folder_name}")

def eic_submit_table_scan(ipts_number, eic_token, desc, pv_lst,val_lst, simulate_only=True, print_results=True):
    eic_client = EICClient(eic_token, ipts_number=ipts_number)

    success, scan_id, response_data = eic_client.submit_table_scan(
        parms={'run_mode': 0, 'headers': pv_lst, 'rows': val_lst}, desc=desc, simulate_only=simulate_only)
    
    if print_results:
        if success:
            if simulate_only:
                prefix = f'Simulated Table Scan for:'
            else:
                prefix = f'Submitted Table Scan (Scan ID={scan_id}) for:'
        else:
            if simulate_only:
                prefix = 'FAILED to simulate Table Scan for:'
            else:
                prefix = 'FAILED to submit Table Scan for:'

        print(f'\n{prefix} {desc}:\n\tresponse_data = {response_data}\n')


def generate_gs_angle(angle_index, max_angle=180):
    '''
    Generate a angle based on conventional golden ratio scan
    '''
    phi = 0.5 * (1 + np.sqrt(5))
    if max_angle == 360:
        return np.fmod(int(angle_index) * 360 / phi, int(max_angle)) 
    else:
        return np.fmod(int(angle_index) * phi * 180, int(max_angle))

def dir_check(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return ("created folder : " + path)
    else:
        return (path + ' exists!')

def Enqueue(queue, entry):
    for q, e in zip(queue, entry):
        q.append(e)
    return queue
