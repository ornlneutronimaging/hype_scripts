import yaml, os

cfg_file = '/data/VENUS/shared/software/hype_scripts/configs/config.yaml'

cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))

ipts = cfg['EIC_vals']['ipts']
num_rec_jobs = len(cfg['wav_idx_start'])
cmd = f'/data/VENUS/shared/software/hype_scripts/hype_loop/hyperct_toolkit_depoly/hyperct_loop_autogen/create_shell.sh {ipts} {num_rec_jobs}'
os.system(cmd)

"""cmd = f'mkdir /data/VENUS/IPTS-{ipts}'
os.system(cmd)

flds = ['images', 'shared']
for fld in flds:
    cmd = f'mkdir /data/VENUS/IPTS-{ipts}/{fld}'
    os.system(cmd)"""