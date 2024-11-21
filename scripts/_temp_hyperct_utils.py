import os
import numpy as np
from EICClient import EICClient

def eic_submit_table_scan(desc, pv_lst, val_lst, simulate_only=True, print_results=True):
    eic_token = "gAAAAABnH91UqxmAH4CmO1zxe8uWd7FjhCCzb7JHg5VnhM_OI3fe0AJItAa6LUA1z82Wy_-cBtu1m9wdVG4fkbu44b55aOzpaFi92WGnhakUlYfATZipqqlckUlUx0zfX1OVq2I6Hie_v7-Z97gjPe3E4ucsES_JAlWwHSTW9GeJ5d-SsqeXJnPcJf0zMmCXtSV6vvB_-0l6-R6I6MO836QiguVrirTQzA36hXtrV1mdHn4iwzuUvejcjzHEuxgaxyNwbz1WDqpdOsXGaMNV7YDkqk51Z-g_ubxlmkY0NrqiEa_DsJEWaJHa_lwNB9Owm970f3JDK5FzLuHCsF3GScDxDuaBxYj-o19UQyVDg_xhfW3gwY1fbKtlZs-LhXQmz0CcKTzYy8mYQguin8iep2DO8vw0-7_sEOEU7KtFyJgVytOgd7ku3mqhayTsTwClkQtmIS297vNoLT6U330jVARabDqY03Zj6oeVzO_8fpYZDh_Gdy99z2iWhBoiSWaAZVXQt7T6ACLXGGEwyppOkbwMufUbE0iYjQfq18WAJVE8lzM1fYiRJFM0YO1eqv6JGinwpECo3iaELL4Z81s4wGZEACMOcze1rQs2xElDmfvayInOL9z-vBtUBAHolI4TUL2BqreISMS5L5Af0cAMsng3O096CjHR1PB6prdj9IMow9TNMNtIL8IE4XkKnvU7BgV-3buB6zh9LtsSRmtN37lqWaMsXSfLyupymJRISUWlcsOJngQSvNfi6GkQJHLfUmitkAZwiT_L"
    ipts_number = "33531"

    eic_client = EICClient(eic_token, ipts_number=ipts_number)

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