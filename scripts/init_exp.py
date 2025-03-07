# %%
from _temp_hyperct_utils import generate_gs_angle, eic_submit_table_scan
import argparse, yaml
# %%
parser = argparse.ArgumentParser(description='Start AI experiment')
parser.add_argument("--cfg_file", type=str, help='configure file path')
args = parser.parse_args()
# %%
# config file
#cfg_file = args.cfg_file
cfg_file = '/SNS/VENUS/IPTS-35790/shared/hype/configs/config.yaml'
cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))

#%%
# load needed settings
ipts = cfg['ipts']
eic_token = cfg['eic_token']

# user define
p_charge = cfg['proton_charge']
exp_name = cfg['experiment_title']
ob_num = cfg['number_of_obs']
usr_desc = cfg['scan_description']
ang_lst = cfg['provided_ang_list']
ini_ang_num = cfg['num_ini_ang']

# %%
# pvs define
pv_file_name = 'BL10:Exp:IM:FileName'
pv_sub_dir = 'BL10:Exp:IM:SubDir'
pv_set_p_charge = 'BL10:Exp:AcquirePCharge'
pv_scan_trig = 'ScanRDRunNq'
pv_motor = 'BL10:Mot:rot1'

print_results= True
simulate_only = True  # to test the command

# get the scan angle list
if ang_lst == []:
    ang_lst = [generate_gs_angle(i) for i in range(ini_ang_num)]
# %%
desc, rows = [], []

header = [[pv_motor, pv_file_name, pv_sub_dir, pv_set_p_charge, pv_scan_trig]]

p_charge_1, p_charge_2 = str(p_charge).split('.')
cnt = 1
for ang in ang_lst:
    _ang_1, _ang_2 = str(ang).split('.')
    _name = f'{exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
    desc.append([f'MCP TPX Radiograph #{cnt}: {_name}'])  
    rows.append([[[ang, _name, _name, p_charge, 0]]])
    cnt +=1
    # send out init scans
eic_submit_table_scan(desc, header, rows, simulate_only, print_results)

# update flag in config
#cfg['ai_process_running'] = True
#yaml.dump(cfg, open(cfg_file, "w", encoding = 'utf-8'), sort_keys=False)
# %%
