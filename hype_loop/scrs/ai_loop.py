import argparse
import sys
from pathlib import Path

# Ensure this folder (scrs/) is on sys.path so sibling AIRobo imports anywhere
here = Path(__file__).resolve()
module_dir = here.parent
if str(module_dir) not in sys.path:
	sys.path.append(str(module_dir))

from AIRobo import AIRobo


parser = argparse.ArgumentParser(description='Run AIRobo for a selected wavelength block')
parser.add_argument("--wav_idx", type=int, default=0, help="0-based index into wav_idx_start/end pairs in config")
parser.add_argument("--mode", type=str, default='load', choices=['load', 'recon', 'evaluate', 'angle'], help="Pipeline mode to execute")
parser.add_argument("--cfg", type=Path, required=True, help="Path to YAML config")
args = parser.parse_args()

cfg_file = args.cfg
wavIdx = args.wav_idx
mode = args.mode

run = AIRobo(cfg_file, mode, wavIdx)

