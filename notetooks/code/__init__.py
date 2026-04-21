list_of_runs_found_file = "/SNS/VENUS/shared/software/git/hype_scripts/logs/list_of_runs_found_in_folder.yaml"
config_file = "/SNS/VENUS/shared/software/git/hype_scripts/configs/config.yaml"

script1_path = '/SNS/VENUS/shared/software/git/hype_scripts/scripts/pre_exp.py'
script2_path = '/SNS/VENUS/shared/software/git/hype_scripts/scripts/init_exp.py'

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
