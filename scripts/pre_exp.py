# %%
from AInCT.utils import eic_submit_table_scan
import yaml, argparse
# %%

parser = argparse.ArgumentParser(description='Pre-experiment: OB & 0/180˚ projections')
parser.add_argument("--cfg_file", type=str, help='configure file path')
"""
parser.add_argument("--ipts", type=int, help='ipts number (6 digits)')
parser.add_argument("--ob_folder_name", type=str, help='Set the OB saving folder name')
parser.add_argument("--ob_num", type=int, help='open beam dataset number')
parser.add_argument("--folder_name", type=str, help='Set the data saving folder name')
parser.add_argument("--file_prefix", type=str, default=None, help='Set the data saving prefix inside of the folder')
parser.add_argument("--p_charge", type=float, help='pCharge value needed')
parser.add_argument("--usr_desc", type=str, default='HyperCT', help='add a description of your experiment')
"""

# %%
args = parser.parse_args()
cfg_file = args.cfg_file
#'/SNS/VENUS/IPTS-33531/shared/ai_output/configs/config_debug_shimin.yaml'
cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
#%%
ipts = cfg['ipts']
p_charge = cfg['proton_charge']
exp_name = cfg['experiment_title']
ob_num = cfg['number_of_obs']
usr_desc = cfg['scan_description']

# %% 
# pvs define
trig_pv = 'BL10:Exp:Scan:ForceTrig'
pixelman_status_pv = 'BL10:Det:PIXELMAN:STATUS'
motor_pv = 'BL10:Mot:rot1'  

print_results= True
simulate_only = False # to test the command
#%% OB command
desc, rows = [], []

ob_header = [['MCPFile', 'MCPAcquire', 'Wait For', 'Value', 'MCPAcquire',
              trig_pv, 'Delay']]
p_charge_1, p_charge_2 = str(p_charge).split('.')
_ob_folder_name = f'OB_{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C'
for i in range(ob_num):
    desc = [f'MCP TPX OB #{i+1}: {_ob_folder_name}']
    _mcp_path = f'E:\\data\\IPTS-{ipts}\\{_ob_folder_name}\\ob_Dset{i}'
    _row = [[[_mcp_path, 1, 'pCharge', p_charge, 0, 1, 20]]]
    eic_submit_table_scan(desc, ob_header, _row, simulate_only, print_results) 

# %%  move up the sample

pos_x_pv= 'BL10:Mot:SampleX'
pos_x_value = 76
pos_y_pv = 'BL10:Mot:SampleY'
pos_y_value = 160

desc = [f'Sample moving up']
header = [[pos_x_pv, pos_y_pv, 'Delay']]
row = [[[pos_x_value, pos_y_value, 60]]]
eic_submit_table_scan(desc, header, row, simulate_only, print_results) 

# %% 0-180 command

angles = [0.0, 180.0]

desc, rows = [], []

header = [['MCPFile', motor_pv, 'Delay', 'MCPAcquire', 'Wait For', 'Value', 'MCPAcquire', 
trig_pv, 'Delay']]
cnt = 1
for ang in angles:
    _ang_1, _ang_2 = str(ang).split('.')
    _name = f'{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
    desc = [f'MCP TPX Radiograph #{cnt}: {_name}']
    _mcp_path =(f'E:\\data\\IPTS-{ipts}\\{_name}\\{_name}')    
    _row = [[[_mcp_path, ang, 15, 1, 'pCharge', p_charge, 0, 1, 20]]]
    
    # send out 0-180 scans
    eic_submit_table_scan(desc, header, _row, simulate_only, print_results)
    cnt +=1
#%%
# update config file
cfg['ai_pre_process_running'] = True
yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
# %%
