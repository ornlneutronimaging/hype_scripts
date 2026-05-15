from pathlib import Path
_top_path = Path(__file__).parent.parent.parent

list_of_runs_found_file = _top_path / "logs" / "list_of_runs_found_in_folder.yaml"
#config_file = "/SNS/VENUS/shared/software/git/hype_scripts/configs/config.yaml"
# config_file = _top_path / "configs" / "config.yaml"
config_file = _top_path / "configs" / "config_debug_jean.yaml"

script1_path = _top_path / "scripts" / "pre_exp.py"
script2_path = _top_path / "scripts" / "init_exp.py"

LAST_RUN_NUMBER_PV = "BL10:CS:RunControl:LastRunNumber"

from .ai_automated_loop import AiAutomatedLoop

__all__ = [
	"AiAutomatedLoop",
	"list_of_runs_found_file",
	"config_file",
	"script1_path",
	"script2_path",
	"LAST_RUN_NUMBER_PV",
]
