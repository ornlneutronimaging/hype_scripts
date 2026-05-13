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


@app.cell
def _(mo):
    hyperct_mode_checked = mo.ui.checkbox(
        value=True,
        label="The instrument has been configure for HyperCT mode (in the DAS console)",
    )
    remote_key_checked = mo.ui.checkbox(
        value=True,
        label="Remote key has been configured by the imaging team (added to config file)",
    )
    cronjob_checked = mo.ui.checkbox(
        value=True,
        label="pre-processing script running (cronjob)",
    )

    checklist_ui = mo.vstack(
        [
            mo.md("### 📋  Starting checklist"),
            hyperct_mode_checked,
            remote_key_checked,
            cronjob_checked,
        ],
        gap=0.5,
    ).style(
        {
            "border": "1px solid #334155",
            "border-radius": "8px",
            "padding": "12px",
            "background": "linear-gradient(180deg, #111827 0%, #0b1220 100%)",
            "color": "#e5e7eb",
            "box-shadow": "0 10px 24px rgba(0, 0, 0, 0.35)",
        }
    )

    checklist_ui
    return hyperct_mode_checked, remote_key_checked, cronjob_checked


@app.cell
def _(cronjob_checked, hyperct_mode_checked, remote_key_checked):
    checklist_ready = bool(
        hyperct_mode_checked.value and remote_key_checked.value and cronjob_checked.value
    )
    return (checklist_ready,)


@app.cell
def _(checklist_ready, get_debug_mode_unlocked, get_live_enabled, mo, set_live_enabled, get_pre_proc_started):
    mo.stop(not checklist_ready)

    _started = get_pre_proc_started()
    _debug_locked = get_debug_mode_unlocked()

    live_w = mo.ui.checkbox(
        value=get_live_enabled(),
        label="live (hyperct code will be executed)",
        on_change=set_live_enabled,
    )
    live_row = mo.vstack([live_w]).style(
        {
            "pointer-events": "none",
            "opacity": "0.45",
        }
    ) if _debug_locked else live_w
    new_experiment_w = mo.ui.checkbox(value=True, label="new experiment")
    ipts_w = mo.ui.text(value="37493", label="IPTS-", disabled=_started)
    required_marker = mo.md("<span style='color: red; font-size: 1.25rem;'>*</span>")
    ipts_row = mo.hstack([ipts_w, required_marker], justify="start", align="end", gap=0.25)
    sample_name_w = mo.ui.text(value="test_sample", label="sample name (10 chars max)", disabled=_started)
    user_conditions_w = mo.ui.text(value="T10K", label="sample conditions (10 chars max)", disabled=_started)
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
    motor_w = mo.ui.number(start=1, stop=6, step=1, value=1, label="motor")
    motor_row = mo.hstack([motor_w], justify="start", widths=[5])
    description_w = mo.ui.text(
        value="testing EIC in May with Shimin and Jean",
        label="description of experiment",
        full_width=True,
        disabled=_started,
    ).style({"width": "700px", "min-width": "700px"})    
    description_row = mo.hstack(
        [description_w, mo.md("<span style='color: #888; font-size: 0.85rem; font-style: italic;'>Optional</span>")],
        justify="start",
        align="end",
        gap=0.5,
        widths=["1fr", "auto"],
    ).style({"width": "100%"})    
    nbr_obs_w = mo.ui.number(start=1, step=1, value=3, label="nbr of open beams")
    nbr_obs_row = mo.hstack([nbr_obs_w], justify="start", widths=[10])
    proton_charge_w = mo.ui.number(start=0.0, step=0.01, value=0.1, label="proton charge (C)")
    proton_charge_row = mo.hstack([proton_charge_w], justify="start", widths=[10])
    n_tiff_w = mo.ui.number(
        start=1,
        step=1,
        value=2628,
        label="number of tiff images for each run",
    )
    n_tiff_row = mo.hstack([n_tiff_w], justify="start", widths=[20])
    first_run_w = mo.ui.text(value="8769", label="first run", disabled=_started)
    first_run_row = mo.hstack(
        [first_run_w, required_marker],
        justify="start",
        align="end",
        gap=0.25,
    )
    initial_angles_w = mo.ui.text(
        value="",
        label="list of initial angles (e.g., 0.0, 90.0, 180.0)",
        disabled=_started,
        full_width=True,
    ).style({"width": "700px", "min-width": "700px"})
    initial_angles_row = mo.hstack(
        [initial_angles_w, mo.md("<span style='color: #888; font-size: 0.85rem; font-style: italic;'>Optional</span>")],
        justify="start",
        align="end",
        gap=0.5,
    )

    controls = mo.vstack(
        [
            mo.md("<div style='border-left: 4px solid #2980b9; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #2980b9;'>⚙️ Runtime parameters</span> <span style='font-size: 0.85rem; font-weight: 400; color: #888; text-transform: none;'>(fields marked with <span style='color: red;'>✱</span> are mandator)</span></div>"),
            live_row,
            new_experiment_w,
            ipts_row,
            sample_name_row,
            user_conditions_row,
            motor_row,
            description_row,
            nbr_obs_row,
            proton_charge_row,
            n_tiff_row,
            first_run_row,
            initial_angles_row,
        ]
    )
    controls

    return (
        ipts_w,
        description_w,
        first_run_w,
        live_w,
        motor_w,
        nbr_obs_w,
        new_experiment_w,
        n_tiff_w,
        proton_charge_w,
        sample_name_w,
        user_conditions_w,
        initial_angles_w,
    )


@app.cell
def _(checklist_ready, ipts_w, mo):
    mo.stop(not checklist_ready)

    _alignment_dir = f"/SNS/VENUS/IPTS-{ipts_w.value}/images/tpx1/alignment"
    sample_alignment_w = mo.ui.file_browser(
        initial_path=_alignment_dir,
        filetypes=[".txt"],
        selection_mode="file",
        multiple=False,
        label="Sample alignment file",
    )
    ob_alignment_w = mo.ui.file_browser(
        initial_path=_alignment_dir,
        filetypes=[".txt"],
        selection_mode="file",
        multiple=False,
        label="Open beam alignment file",
    )

    mo.vstack([sample_alignment_w, ob_alignment_w], gap=0.5)
    return sample_alignment_w, ob_alignment_w


@app.cell
def _(checklist_ready, get_debug_mode_password, get_debug_mode_unlocked, mo):
    mo.stop(not checklist_ready)

    debug_password_w = mo.ui.text(value=get_debug_mode_password(), label="Debug mode password")
    unlock_debug_mode_button = mo.ui.run_button(
        label="Lock debug mode" if get_debug_mode_unlocked() else "Unlock debug mode"
    )
    password_row = mo.hstack([debug_password_w, unlock_debug_mode_button], justify="start", align="end", gap=0.5)

    mo.vstack(
        [
            mo.md("<div style='border-left: 4px solid #888; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #555;'>🔒 Debug mode access</span></div>"),
            password_row,
        ]
    )

    return debug_password_w, unlock_debug_mode_button


@app.cell
def _(mo):
    get_debug_mode_unlocked, set_debug_mode_unlocked = mo.state(False)
    return get_debug_mode_unlocked, set_debug_mode_unlocked


@app.cell
def _(mo):
    get_debug_mode_password, set_debug_mode_password = mo.state("")
    return get_debug_mode_password, set_debug_mode_password


@app.cell
def _(mo):
    get_live_enabled, set_live_enabled = mo.state(True)
    return get_live_enabled, set_live_enabled


@app.cell
def _(checklist_ready, debug_password_w, get_debug_mode_unlocked, mo, set_debug_mode_password, set_debug_mode_unlocked, set_live_enabled, unlock_debug_mode_button):
    mo.stop(not checklist_ready)
    mo.stop(not unlock_debug_mode_button.value)

    if get_debug_mode_unlocked():
        set_debug_mode_unlocked(False)
        set_debug_mode_password("")
        debug = False
        status = mo.callout(
            mo.md("Debug mode locked."),
            kind="warn",
        )
    else:
        is_correct_password = str(debug_password_w.value).strip() == "imaging"
        set_debug_mode_unlocked(is_correct_password)
        set_debug_mode_password("")
        if is_correct_password:
            set_live_enabled(False)
        debug = is_correct_password

        if is_correct_password:
            status = mo.callout(
                mo.md("Debug mode unlocked."),
                kind="success",
            )
        else:
            status = mo.callout(
                mo.md("Incorrect password. Debug mode remains locked."),
                kind="warn",
            )

    return debug, status


@app.cell
def _(mo):
    get_pre_proc_started, set_pre_proc_started = mo.state(False)
    return get_pre_proc_started, set_pre_proc_started


@app.cell
def _(checklist_ready, mo, get_debug_mode_unlocked, get_pre_proc_started):
    mo.stop(not checklist_ready)

    _started = get_pre_proc_started()
    _is_unlocked = get_debug_mode_unlocked()
    _debug_locked = not _is_unlocked

    create_0deg_projection_button = mo.ui.run_button(
        label="Create 0degree projection",
        disabled=_started or _debug_locked,
    )
    create_180deg_projection_button = mo.ui.run_button(
        label="Create 180degrees projection",
        disabled=_started or _debug_locked,
    )
    projection_buttons_row = mo.hstack(
        [create_0deg_projection_button, create_180deg_projection_button],
        justify="start",
    )
    create_ob_1_button = mo.ui.run_button(
        label="Create OB #1",
        disabled=_started or _debug_locked,
    )
    create_ob_2_button = mo.ui.run_button(
        label="Create OB #2",
        disabled=_started or _debug_locked,
    )
    create_ob_3_button = mo.ui.run_button(
        label="Create OB #3",
        disabled=_started or _debug_locked,
    )
    ob_buttons_row = mo.hstack(
        [create_ob_1_button, create_ob_2_button, create_ob_3_button],
        justify="start",
    )

    imaging_controls = mo.vstack(
        [
            mo.md("<div style='border-left: 4px solid #e67e22; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #e67e22;'>🛠 Imaging team controls</span></div>"),
            projection_buttons_row,
            ob_buttons_row,
        ]
    ) if _is_unlocked else mo.md("")

    imaging_controls

    return (
        create_0deg_projection_button,
        create_180deg_projection_button,
        create_ob_1_button,
        create_ob_2_button,
        create_ob_3_button,
    )


@app.cell
def _(checklist_ready, mo, sample_name_w, user_conditions_w, first_run_w, get_pre_proc_started):
    mo.stop(not checklist_ready)

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
    checklist_ready,
    debug,
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
    mo.stop(not checklist_ready)
    mo.stop(not start_pre_processing_button.value)

    # Read widget values at click time so pre-processing uses the latest UI input.
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

    o_ai = AiAutomatedLoop(
        sample_name=sample_name,
        user_conditions=user_conditions,
        new_experiment=new_experiment,
        ipts=IPTS,
        debug=debug,
        description_of_exp=description_of_exp,
        nbr_obs=nbr_obs,
        proton_charge=proton_charge,
        number_of_tiff_for_each_run=number_of_tiff_for_each_run,
        live=live,
        first_run=first_run,
        motor=motor,
    )
    o_ai.launch_pre_processing_step()
    set_pre_proc_started(True)

    return (
        IPTS,
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
        o_ai,
    )


@app.cell
def _(checklist_ready, mo, get_pre_proc_started):
    mo.stop(not checklist_ready)
    mo.stop(not get_pre_proc_started())
    check_pre_process_status_button = mo.ui.run_button(
        label="Check pre-process status",
        full_width=True,
    )
    check_pre_process_status_button
    return (check_pre_process_status_button,)


@app.cell
def _(checklist_ready, mo, check_pre_process_status_button):
    mo.stop(not checklist_ready)
    mo.stop(not check_pre_process_status_button.value)

    import yaml
    from notetooks.code import config_file as _config_file

    with open(_config_file, "r") as _f:
        _cfg = yaml.safe_load(_f)

    if _cfg.get("ai_pre_process_running", False):
        mo.callout(
            mo.md("Pre-processing is **still running** - check back in a few minutes."),
            kind="warn",
        )
        pre_process_is_done = False
    else:
        mo.callout(
            mo.md("Pre-processing is **DONE!** Feel free to move to the next step."),
            kind="success",
        )
        pre_process_is_done = True
    return (pre_process_is_done,)


@app.cell
def _(checklist_ready, mo, pre_process_is_done, o_ai):
    mo.stop(not checklist_ready)
    mo.stop(not pre_process_is_done)

    # we need to calculate the center of rotation
    o_ai.calculate_center_of_rotation()

    # we need to crop
    o_ai.crop_images()

    # we need to define up to 5 TOF ranges
    o_ai.define_tof_ranges()


if __name__ == "__main__":
    app.run()
