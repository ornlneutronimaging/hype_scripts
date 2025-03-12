
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
ipts = cfg['EIC_vals']['ipts']
eic_token = cfg['EIC_vals']['eic_token']


# user define
p_charge = cfg['EIC_vals']['proton_charge']
exp_name = cfg['EIC_vals']['experiment_title']
ob_num = cfg['EIC_vals']['number_of_obs']
usr_desc = cfg['EIC_vals']['scan_description']

# %% 
# pvs define
pv_file_name = 'BL10:Exp:IM:FileName'
pv_sub_dir = 'BL10:Exp:IM:SubDir'
pv_num_dataset = 'BL10:Exp:NumDataSets'
pv_set_p_charge = 'BL10:Exp:AcquirePCharge'
pv_scan_trig = 'ScanRDRunNq'
pv_motor = 'BL10:Mot:rot3'

print_results= True
simulate_only = False # to test the command
#%% OB command
desc, rows = [], []

ob_header = [[pv_file_name, pv_sub_dir, pv_num_dataset, pv_set_p_charge, pv_scan_trig]]
p_charge_1, p_charge_2 = str(p_charge).split('.')
_ob_file_name = f'OB_{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C'

for i in range(ob_num):
    desc.append([f'MCP TPX OB #{i+1}: {_ob_file_name}'])
    _fl_name = f'{_ob_file_name}_Dset{i}'
    #E:\\data\\IPTS-{ipts}\\{_ob_folder_name}\\
    rows.append([[_fl_name, _fl_name, 1,  p_charge, 0]])
eic_submit_table_scan(ipts, eic_token, desc, ob_header, rows, simulate_only, print_results) 

# %%  move up the sample
#"""
sample_pos_file = '/SNSlocal/data/IPTS-34969/images/alignment/raw/alignment_calibration/20250307_March_7_2025_Ni_Position_alignment_smallrot3_15:49:06.csv'

desc = [[f'Sample moving up']]
header = [['BL10:Exp:Align:FileSelector','ScanALFileRunNq']]
rows = [[[sample_pos_file, 1]]]
eic_submit_table_scan(desc, header, rows, simulate_only, print_results) 

# %% 0-180 command
angles = [0.0, 180.0]

desc, rows = [], []

header = [[pv_motor, pv_file_name, pv_sub_dir, pv_num_dataset, pv_set_p_charge, pv_scan_trig]]
cnt = 1
for ang in angles:
    _ang_1, _ang_2 = str(ang).split('.')
    _name = f'{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
    desc.append([f'MCP TPX Radiograph #{cnt}: {_name}'])  
    rows.append([[[ang, _name, _name, 1, p_charge, 0]]])
    cnt +=1
# send out 0-180 scans
eic_submit_table_scan(desc, header, rows, simulate_only, print_results)
    
#%%
# update config file
cfg['ai_pre_process_running'] = True
yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
#"""

