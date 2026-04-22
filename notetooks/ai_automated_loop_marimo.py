import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import sys

    # Find project root by looking for pixi.toml.
    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents]
    repo_root = next((p for p in candidates if (p / "pixi.toml").exists()), cwd)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    return mo


# @app.cell
# def _(mo):
#     mo.md("""
#     # AI Automated Loop

#     Workflow:
#     1. Set parameters.
#     2. Create `AiAutomatedLoop` object.
#     3. Optionally launch pre-processing (OB + 0/180).
#     4. Check pre-processing status.
#     5. Calculate center of rotation.
#     6. Optionally launch AI loop.

#     Safety note:
#     - Side-effect steps are behind explicit boolean toggles.
#     - Keep them `False` until you are ready.
#     """)
#     return


@app.cell
def _(mo, get_pre_proc_started):
    _started = get_pre_proc_started()
    debug_w = mo.ui.checkbox(value=False, label="debug (used by imaging team only)", disabled=_started)
    live_w = mo.ui.checkbox(value=False, label="live (will update the config file)", disabled=_started)
    new_experiment_w = mo.ui.checkbox(value=True, label="new_experiment", disabled=_started)
    ipts_w = mo.ui.text(value="37493", label="IPTS-", disabled=_started)
    ipts_row = mo.hstack([ipts_w], justify="start", widths=[50])
    sample_name_w = mo.ui.text(value="test_sample", label="sample_name (10 chars max)", disabled=_started)
    user_conditions_w = mo.ui.text(value="T10K", label="user_conditions (10 chars max)", disabled=_started)
    required_marker = mo.md("<span style='color: red; font-size: 1.25rem;'>*</span>")
    sample_name_row = mo.hstack(
        [sample_name_w, required_marker],
        justify="start",
        align="end",
        gap=0.25,
    )
    user_conditions_row = mo.hstack(
        [user_conditions_w, required_marker],
        justify="start",
        align="end",
        gap=0.25,
    )
    motor_w = mo.ui.number(start=1, step=1, value=1, label="motor", disabled=_started)
    motor_row = mo.hstack([motor_w], justify="start", widths=[5])
    description_w = mo.ui.text(
        value="testing EIC in May with Shimin and Jean",
        label="description_of_exp",
        full_width=True,
        disabled=_started,
    )
    nbr_obs_w = mo.ui.number(start=1, step=1, value=3, label="nbr_obs", disabled=_started)
    nbr_obs_row = mo.hstack([nbr_obs_w], justify="start", widths=[10])
    proton_charge_w = mo.ui.number(start=0.0, step=0.01, value=0.1, label="proton_charge (C)", disabled=_started)
    proton_charge_row = mo.hstack([proton_charge_w], justify="start", widths=[10])
    n_tiff_w = mo.ui.number(
        start=1,
        step=1,
        value=2628,
        label="number_of_tiff_for_each_run",
        disabled=_started,
    )
    n_tiff_row = mo.hstack([n_tiff_w], justify="start", widths=[20])
    first_run_w = mo.ui.text(value="8769", label="first_run", disabled=_started)
    first_run_row = mo.hstack(
        [first_run_w, required_marker],
        justify="start",
        align="end",
        gap=0.25,
        # widths=[100, 0],
    )
    initial_angles_w = mo.ui.text(
        value="",
        label="list_of_initial_angles (optional, comma-separated)",
        disabled=_started,
    )

    controls = mo.vstack(
        [
            mo.md("## Runtime parameters"),
            debug_w,
            live_w,
            new_experiment_w,
            ipts_row,
            sample_name_row,
            user_conditions_row,
            motor_row,
            description_w,
            nbr_obs_row,
            proton_charge_row,
            n_tiff_row,
            first_run_row,
            initial_angles_w,
        ]
    )
    controls
    
    return (ipts_w, debug_w, description_w, first_run_w, live_w, motor_w, nbr_obs_w, new_experiment_w, n_tiff_w, proton_charge_w, sample_name_w, user_conditions_w, initial_angles_w)


@app.cell
def _(mo):
    get_pre_proc_started, set_pre_proc_started = mo.state(False)
    return get_pre_proc_started, set_pre_proc_started


@app.cell
def _(mo, sample_name_w, user_conditions_w, first_run_w, get_pre_proc_started):
    _started = get_pre_proc_started()
    start_pre_processing_button = mo.ui.run_button(
        label="Start pre-processing",
        full_width=True,
        disabled=_started or not all(
            [
                str(sample_name_w.value).strip(),
                str(user_conditions_w.value).strip(),
                str(first_run_w.value).strip(),
            ]
        ),
    )
    
    
    
    start_pre_processing_button
    return (start_pre_processing_button,)


@app.cell
def _(
    debug_w,
    description_w,
    first_run_w,
    initial_angles_w,
    ipts_w,
    live_w,
    mo,
    motor_w,
    nbr_obs_w,
    new_experiment_w,
    n_tiff_w,
    proton_charge_w,
    sample_name_w,
    set_pre_proc_started,
    start_pre_processing_button,
    user_conditions_w,
):
    mo.stop(not start_pre_processing_button.value)

    # Read widget values at click time so pre-processing uses the latest UI input.
    debug = bool(debug_w.value)
    live = bool(live_w.value)
    new_experiment = bool(new_experiment_w.value)
    IPTS = int(ipts_w.value)
    sample_name = str(sample_name_w.value)
    user_conditions = str(user_conditions_w.value)
    motor = int(motor_w.value)
    description_of_exp = str(description_w.value)
    nbr_obs = int(nbr_obs_w.value)
    proton_charge = float(proton_charge_w.value)
    number_of_tiff_for_each_run = int(n_tiff_w.value)
    raw_first_run = str(first_run_w.value).strip()
    first_run = int(raw_first_run) if raw_first_run else None

    raw_angles = str(initial_angles_w.value).strip()
    if raw_angles:
        list_of_initial_angles = [float(v.strip()) for v in raw_angles.split(",") if v.strip()]
    else:
        list_of_initial_angles = None

    # this is where we start running the pre-processing algo
    from notetooks.code import AiAutomatedLoop
    o_ai = AiAutomatedLoop(sample_name=sample_name,
                       user_conditions=user_conditions,
                       new_experiment=new_experiment,
                       ipts=IPTS,
                       description_of_exp=description_of_exp,
                       nbr_obs=nbr_obs,
                       proton_charge=proton_charge,
                       number_of_tiff_for_each_run=number_of_tiff_for_each_run,
                       live=live,
                       first_run=first_run,
                       motor=motor,
                       debug=debug)
    o_ai.launch_pre_processing_step()
    set_pre_proc_started(True)

    return (
        IPTS,
        debug,
        description_of_exp,
        first_run,
        list_of_initial_angles,
        live,
        motor,
        nbr_obs,
        new_experiment,
        number_of_tiff_for_each_run,
        proton_charge,
        sample_name,
        user_conditions,
    )


@app.cell
def _(mo, get_pre_proc_started):
    mo.stop(not get_pre_proc_started())
    check_pre_process_status_button = mo.ui.run_button(
        label="Check pre-process status",
        full_width=True,
    )
    check_pre_process_status_button
    return (check_pre_process_status_button,)


@app.cell
def _(mo, check_pre_process_status_button):
    mo.stop(not check_pre_process_status_button.value)

    import yaml
    from notetooks.code import config_file as _config_file

    with open(_config_file, "r") as _f:
        _cfg = yaml.safe_load(_f)

    if _cfg.get("ai_pre_process_running", False):
        mo.callout(
            mo.md("Pre-processing is **still running** — check back in a few minutes."),
            kind="warn",
        )
    else:
        mo.callout(
            mo.md("Pre-processing is **DONE!** Feel free to move to the next step."),
            kind="success",
        )


if __name__ == "__main__":
    app.run()
