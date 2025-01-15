HyperCT loop algorithm
==========================
Using CTQA and AInCT packages to realized the real-time hyperspectral neutron CT reconstruction, quality evaluation and scannning angles propse.

*This version of code aims to deploy the HyperCT on the VENUS hype cluster (with multiple computing CPU/GPU nodes)*

Instruction 
--------------------------
0. Clone or download the repository and get inside:

```
	git clone https://github.com/ornlneutronimaging/hype_ipts_33531.git 
	cd hype_ipts_33531/scripts/hyperct_ai
```

1. Generate the scripts for individual experiment with different log path, output log name, angle propose mode and number of wavelength bands interested.

```
cd run
./create_shell.sh </log/path> <log_name> <angle_propose_mode> <wave_idx1> <wave_idx2> ... <wave_idxN>
```
- *log path*
    - file location where output log will be saved
- *log name*
    - customized name for output and error log files (no file type needed)
- *angle_propose_mode*: 
    - preset: fixed angles arrangement
    - golden: golden ration angles
    - edge: adaptive edge alignment method
- *wave_idx*:
    - wavelength index, intergers from 1

2. run AI loop 
```
run ./run_ai_loop.sh
```

