AInCT
====

Python code for the HyperCT AI loop, including reconstruction, evaluation, and angle proposal. Current package version: 0.0.3.


This directory integrates the AInCT framework from:

https://github.com/ornlneutronimaging/AInCT

- Branch used: `clean_version`
- Integrated via `git subtree --squash`
- AInCT main branch is NOT used


Installing
----------

- **Python**: 3.8+
- **Prerequisite**: Install `ctqa` first (AInCT relies on it for the evaluator module).
- **Runtime deps** (installed automatically): numpy, pandas, dxchange, h5py, svmbir, scikit-image, requests, requests-oauthlib, oauthlib, cryptography, urllib3

**Install prerequisite `ctqa`**

```bash
pip install git+https://github.com/ornlneutronimaging/ctqa.git
```

**From source (pip)**

```bash
git clone https://github.com/ornlneutronimaging/AInCT.git
cd AInCT
pip install .
```

**Using a pixi environment**

If you manage your environment with pixi, install the package inside the pixi shell:

```bash
pixi shell
pip install .
```

Uninstalling
------------

```bash
pip uninstall ainct
rm -rf AInCT.egg-info build dist
```

Deprecated modules
------------------

- `dataload_utils` has been removed; use `AInCT.data_handler.DataHandler` for loading and preprocessing.
- `AInCT.Calibrator` is deprecated and now raises an ImportError. The archived implementation is in `__old_version/Calibrator_old.py` for legacy needs.

Quick start (DataHandler)
-------------------------

```python
from AInCT import DataHandler

config = {
    "out_path": "./outputs",
    "ob_list": ["/path/to/OB_0", "/path/to/OB_1"],
    "proj_path": "/path/to/projections",
    # optional tuning
    "use_clean_data": False,
    "num_workers": 4,
    "correct_radius": 3,
    "x_offset": 0,
    "y_offset": 0,
}

handler = DataHandler(config)
ob = handler.process_ob(wav_start=0, wav_end=512)
norm_data, angles_deg = handler.process_projections(wav_start=0, wav_end=512, ob_data=ob)
```
