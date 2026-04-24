import subprocess
from pathlib import Path
import yaml

cfg_file = "/data/VENUS/shared/software/hype_scripts/configs/config.yaml"

with open(cfg_file, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

ipts = cfg["EIC_vals"]["ipts"]
exp_name = f'{cfg["EIC_vals"]["sample_name"]}_{cfg["EIC_vals"]["user_con"]}'

src_root = Path(f"/data/VENUS/IPTS-{ipts}/shared/{exp_name}")
dst_root = Path(f"/SNS/VENUS/IPTS-37493/shared/hyperct_output/{exp_name}")

if not src_root.exists():
    raise FileNotFoundError(f"Source folder does not exist: {src_root}")

dst_root.mkdir(exist_ok=True)

cmd = [
    "rsync",
    "-av",
    "--exclude=*.nxs",
    f"{src_root}/",
    f"{dst_root}/",
]

print("Running:", " ".join(cmd))
subprocess.run(cmd, check=True)
print("Sync completed.")