from AInCT import *
from AIRobo import *
import argparse 

parser = argparse.ArgumentParser(description='Set wavelength to be processed')
parser.add_argument("--wav_idx", type=int, default=100)
parser.add_argument("--mode", type=str, default='recon')
parser.add_argument("--angle_mode", type=str, default='golden')



# config file
cfg_file = '/home/gxt/Projects/hype_ipts_33531/configs/config.yaml'
#'/SNS/VENUS/IPTS-33531/shared/ai_output/configs/config_debug_shimin.yaml'
#'/home/gxt/Projects/AIloop_hype_cluster/codes/config.yaml'
args = parser.parse_args()

wavIdx = args.wav_idx
mode = args.mode
ang_mode = args.angle_mode

run = AIRobo(cfg_file, mode, wavIdx, ang_mode)

