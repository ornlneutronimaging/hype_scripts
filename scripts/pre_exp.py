
#%%
from _temp_hyperct_utils import eic_submit_table_scan
import yaml, argparse
# %%

parser = argparse.ArgumentParser(description='Pre-experiment: OB & 0/180˚ projections')
parser.add_argument("--cfg_file", type=str, help='configure file path')
args = parser.parse_args()

# %%
cfg_file = args.cfg_file
#cfg_file = '/SNS/VENUS/IPTS-35790/shared/hype/configs/config.yaml'
cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
#%%
ipts = str(cfg['EIC_vals']['ipts'])
eic_token = cfg['EIC_vals']['eic_token']


# user define
p_charge = cfg['EIC_vals']['proton_charge']
smp_name = cfg['EIC_vals']['sample_name']
user_con = cfg['EIC_vals']['user_con']
ob_num = cfg['EIC_vals']['number_of_obs']
usr_desc = cfg['EIC_vals']['scan_description']
ini_ang_num = cfg['num_ini_ang']
pv_motor_selector = 'BL10:Mot:RotUI:Menu'
motor_number = cfg['EIC_vals']['motor_number']

# %% 
# pvs define # needs to updated based on the new measure mode setup
pv_pos_file_selector = 'BL10:Exp:Align:FileSelector'
pv_move_trig = 'ScanALFileRunNq'
pv_smp_name = 'BL10:Exp:IM:UserSampleName'
pv_user_con = 'BL10:Exp:IM:UserConditions'
pv_num_dataset = 'BL10:Exp:NumDataSets'
pv_scan_type = 'BL10:Exp:IM:ScanType'
pv_aq_type = 'BL10:Exp:IM:AcquireType'
pv_set_p_charge = 'BL10:Exp:AcquirePCharge'
pv_set_time = 'BL10:Exp:IM:AcquireTime'
pv_scan_trig = 'BL10:Exp:IM:ScanNewNq'

pv_ct_rot_type = 'BL10:Mot:RotUI:Menu'
pv_rot_option = 'BL10:Exp:Rot:Options'
pv_ang_fillNum = 'BL10:Exp:Rot:T:AutofillNum'
pv_ang_prefix = 'BL10:Exp:Rot:T:Pos'

print_results= True
simulate_only = False # to test the command
print(f'{ipts=} {eic_token}')

ob_pos_file = '/SNSlocal/data/IPTS-35790/images/alignment/raw/alignment_calibration/20250313_ ai_cali_ob_pos_alignment_smallrot3_12:36:46.csv'
sample_pos_file = '/SNSlocal/data/IPTS-35790/images/alignment/raw/alignment_calibration/20250313_ ai_cali_sampe_pos_alignment_smallrot3_12:33:51.csv'

# %%  move to open beam
desc = f'Move to OB pos'
header = [pv_pos_file_selector, pv_move_trig]
rows =[[ob_pos_file, 0]]
eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results) 
#%% OB command
rows = []
## place holder to check either pcharge or time acquire time
ob_header = [pv_smp_name, pv_user_con, pv_scan_type, pv_aq_type,  pv_set_p_charge, pv_num_dataset, pv_scan_trig]
desc = f'{usr_desc}: MCP TPX {ob_num} OB: {p_charge}'

rows.append([smp_name, user_con, 'Open Beam',  1, p_charge, 1, 0])

eic_submit_table_scan(ipts, eic_token, desc, ob_header, rows, simulate_only, print_results) 

# %%  move up the sample
#"""
desc = f'Sample moving up'
header = [pv_pos_file_selector, pv_move_trig]
rows = [[sample_pos_file, 0]]
eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results) 
#"""
# %% 0-180 command
angles = [0.0, 180.0]
_angle_number = len(angles)
rows = []
ang_pv = [f'{pv_ang_prefix}{i+1}' for i in range(_angle_number)]
desc = f'MCP TPX {len(angles)} Radiographs: {angles}' 

header_ = [pv_smp_name, pv_user_con, pv_scan_type, pv_motor_selector, pv_rot_option, pv_ang_fillNum]
_header = [pv_aq_type,  pv_set_p_charge, pv_num_dataset, pv_scan_trig]

header = header_ + ang_pv + _header

row_ = [smp_name, user_con, '3D CT', motor_number, 3, _angle_number] 
_row = [1, p_charge, 1, 0]

rows = row_ + angles + _row

# send out 0-180 scans
eic_submit_table_scan(ipts, eic_token, desc, header, rows, simulate_only, print_results)
    
#%%
# update config file
cfg['ai_pre_process_running'] = True
yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
#"""

