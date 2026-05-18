
#%%
import sys
sys.path.insert(0, "/data/VENUS/shared/software/hype_scripts/scripts")
from _temp_hyperct_utils import eic_submit_table_scan
import yaml, argparse
# %%

parser = argparse.ArgumentParser(description='Pre-experiment: OB & 0/180˚ projections')
parser.add_argument("--cfg_file", type=str, help='configure file path')
args = parser.parse_args()

# %%
#cfg_file = args.cfg_file
cfg_file = '/data/VENUS/shared/software/hype_scripts/configs/config.yaml'
cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
#%%
ipts = str(cfg['EIC_vals']['ipts'])
eic_token = cfg['EIC_vals']['eic_token']

# user define
smp_name = cfg['EIC_vals']['sample_name']
user_con = cfg['EIC_vals']['user_conditions']
ob_num = cfg['EIC_vals']['number_of_obs']
usr_desc = cfg['EIC_vals']['scan_description']
ini_ang_num = cfg['num_ini_ang']
motor_number = cfg['EIC_vals']['motor_number']
aq_type = cfg['EIC_vals']['acquire_type']
# %% 
# pvs define # needs to updated based on the new measure mode setup
pv_pos_file_selector = 'BL10:Exp:Align:FileSelector'
pv_move_trig = 'ScanALFileRunNq'
pv_smp_name = 'BL10:Exp:IM:UserSampleName'
pv_user_con = 'BL10:Exp:IM:UserConditions'
pv_num_dataset = 'BL10:Exp:NumDataSets'
pv_scan_type = 'BL10:Exp:IM:ScanType'
pv_aq_type = 'BL10:Exp:IM:AcquireType'

pv_scan_trig = 'BL10:Exp:IM:ScanNewNq'
pv_motor_selector = 'BL10:Mot:RotUI:Menu'
pv_rot_option = 'BL10:Exp:Rot:Options'
pv_ang_fillNum = 'BL10:Exp:Rot:T:AutofillNum'
pv_ang_prefix = 'BL10:Exp:Rot:T:Pos'
# create position file for open beam and sample
pos_path = f'/SNSlocal/data/{ipts}/images/tpx1/alignment'
ob_pos_file = f'{pos_path}/{cfg["EIC_vals"]["ob_position_file_name"]}'
sample_pos_file = f'{pos_path}/{cfg["EIC_vals"]["smp_position_file_name"]}'
# set up acquire type and unit
if aq_type == 'pCharge':
    pv_set_aq_type = 'BL10:Exp:AcquirePCharge'
    aq_type_value = 1
    aq_length = cfg['EIC_vals']['proton_charge']
    unit = 'C'
else:
    pv_set_aq_type = 'BL10:Exp:IM:AcquireTime'
    aq_type_value = 0 
    aq_length = cfg['EIC_vals']['time_s']
    unit = 's'
# set up EIC
print_results= True
simulate_only = True # to test the command
print_only = True # only print the command without sending to EIC
print(f'{ipts=} {eic_token}')
# %%  move to open beam
desc = f'Move to OB pos'
header = [pv_pos_file_selector, pv_move_trig]
rows =[[ob_pos_file, 0]]
if print_only:
    print(header, "\n", rows)
else:
    eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results) 
#%% OB command
## place holder to check either pcharge or time acquire time
ob_header = [pv_smp_name, pv_user_con, pv_scan_type, pv_aq_type, pv_set_aq_type, pv_num_dataset, pv_scan_trig]
desc = f'{usr_desc}: MCP TPX1 {ob_num} OB: {aq_length} {unit}'

rows =[[smp_name, user_con, 'Open Beam', aq_type_value, aq_length, ob_num, 0]]
if print_only:
    print(ob_header, "\n", rows)
else:
    eic_submit_table_scan(ipts, eic_token, desc, ob_header, rows, simulate_only, print_results)
# %%  move up the sample
desc = f'Sample moving up'
header = [pv_pos_file_selector, pv_move_trig]
rows = [[sample_pos_file, 0]]

if print_only:
    print(header, "\n", rows)
else:
    eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results)

# %% 0-180 command
angles = [0.0, 180.0]
_angle_number = len(angles)
rows = []
ang_pv = [f'{pv_ang_prefix}{i+1}' for i in range(_angle_number)]
desc = f'MCP TPX1 {len(angles)} Radiographs: {angles}, {aq_length} {unit}' 

header_ = [pv_smp_name, pv_user_con, pv_scan_type, pv_motor_selector, pv_rot_option, pv_ang_fillNum]
_header = [pv_aq_type,  pv_set_aq_type, pv_num_dataset, pv_scan_trig]

header = header_ + ang_pv + _header

row_ = [smp_name, user_con, '3D CT', motor_number, 3, _angle_number] 
_row = [aq_type_value, aq_length, 1, 0]

rows = row_ + angles + _row

# send out 0-180 scans
if print_only:
    print(header, "\n", rows)
else:
    eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results)
    
#%%
# update config file
cfg['ai_pre_process_running'] = True
yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
#"""

