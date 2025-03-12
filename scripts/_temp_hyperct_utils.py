import os
import numpy as np
from EICClient import EICClient

def eic_submit_table_scan(ipts_number, eic_token, desc, pv_lst, val_lst, simulate_only=True, print_results=True):
    
    eic_client = EICClient(eic_token=eic_token, ipts_number=ipts_number)

    for des, p_lst, v_lst in zip(desc, pv_lst, val_lst):
        success, scan_id, response_data = eic_client.submit_table_scan(
            parms={'run_mode': 0, 'headers': p_lst, 'rows': v_lst}, desc=des, simulate_only=simulate_only)
        
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