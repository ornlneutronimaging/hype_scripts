# %%
from _temp_hyperct_utils import generate_gs_angle, eic_submit_table_scan
import argparse, yaml
import shutil
# %%
parser = argparse.ArgumentParser(description='Pre-experiment: OB & 0/180˚ projections')
parser.add_argument("--cfg_file", type=str, help='configure file path')

"""
parser = argparse.ArgumentParser(description='Set PV values to init an experiment')
parser.add_argument("--folder_name", type=str, help='Set the data saving folder name')
parser.add_argument("--file_prefix", type=str, default=None, help='Set the data saving prefix inside of the folder')
parser.add_argument("--p_charge", type=float, help='pCharge value needed')
parser.add_argument("--init_angle_num", type=int, default=6, help='number of the init angle')
parser.add_argument("--usr_desc", type=str, default='HyperCT', help='add a description of your experiment')
"""
# %%
# config file
args = parser.parse_args()
#cfg_file = '/SNS/VENUS/IPTS-33531/shared/ai_output/configs/config_debug_shimin.yaml'
cfg_file = args.cfg_file
cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
#shutil.copy(cfg_file, "/storage/VENUS/IPTS-33531/shared/ai")

#%%
ipts = cfg['ipts']
p_charge = cfg['proton_charge']
exp_name = cfg['experiment_title']
init_ang_num = 6 #cfg['init_ang_num']
usr_desc = cfg['scan_description']

# %%
# pvs define
trig_pv = 'BL10:Exp:Scan:ForceTrig'
pixelman_status_pv = 'BL10:Det:PIXELMAN:STATUS'
motor_pv = 'BL10:Mot:rot1'

simulate_only = False  # to test the command
print_results= True

angles = [generate_gs_angle(i) for i in range(init_ang_num)] # using golden ratio initate angles
""" if need preset angles
[7.71082381, 242.5702746, 360, 15.42080578, 237.9102855, 355.3400109, 
20.08079488, 230.2003035, 347.6300289, 27.79077685, 217.8303325, 342.9700398, 
40.16074792, 210.1203505, 335.2600579, 47.87072989, 205.4603614, 327.5500759, 
52.530719, 197.7503794, 322.8900868, 60.24070097, 190.0403974, 315.1801048, 
67.95068294, 185.3804083, 302.8101337, 72.61067204, 177.6704264, 295.1001518, 
80.32065401, 165.3004553, 290.4401627, 92.69062509, 157.5904733, 282.7301807, 
100.4006071, 152.9304842, 275.0201987, 105.0605962, 145.2205023, 270.3602096, 
112.7705781, 137.5105203, 262.6502277, 120.4805601, 132.8505312, 257.9902385, 
125.1405492, 250.2802566]
"""
desc, rows = [], []

header = [['MCPFile', motor_pv, 'Delay', 'MCPAcquire', 'Wait For', 'Value', 'MCPAcquire', trig_pv, 'Delay']]

p_charge_1, p_charge_2 = str(p_charge).split('.')
cnt = 1
for ang in angles:
    _ang_1, _ang_2 =f'{ang:.3f}'.split('.')
    _name = f'{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
    _mcp_path =(f'E:\\data\\IPTS-{ipts}\\{_name}\\{_name}')    
    _row = [[[_mcp_path, ang, 15, 1, 'pCharge', p_charge, 0, 1, 20]]]
    desc =[f'MCP TPX Radiphraph: {_name}']
    # send out init scans
    eic_submit_table_scan(desc, header, _row, simulate_only, print_results)
    cnt +=1

# update flag in config
cfg['ai_process_running'] = True
yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
# %%
