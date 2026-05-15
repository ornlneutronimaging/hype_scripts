import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    """Bootstrap: import marimo, locate the repo root via pixi.toml and add it to sys.path."""
    import marimo as mo
    from pathlib import Path
    import sys

    # Find project root by looking for pixi.toml.
    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents]
    repo_root = next((p for p in candidates if (p / "pixi.toml").exists()), cwd)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return Path, mo


@app.cell
def _(
    get_admin_password,
    get_admin_unlocked,
    get_pre_proc_cronjob_enabled,
    get_preview_shown,
    mo,
    set_pre_proc_cronjob_enabled,
):
    admin_password_w = mo.ui.text(value=get_admin_password(), label="Admin password")
    unlock_admin_button = mo.ui.run_button(
        label="Lock admin" if get_admin_unlocked() else "Unlock admin"
    )
    admin_password_row = mo.hstack([admin_password_w, unlock_admin_button], justify="start", align="end", gap=0.5)

    _pre_proc_cronjob_w = mo.ui.checkbox(
        value=get_pre_proc_cronjob_enabled(),
        label="Run pre-processing cronjob",
        on_change=set_pre_proc_cronjob_enabled,
    )
    _cronjob_row = _pre_proc_cronjob_w if get_admin_unlocked() else mo.vstack([_pre_proc_cronjob_w]).style(
        {"pointer-events": "none", "opacity": "0.45"}
    )
    _admin_body = mo.vstack([admin_password_row, _cronjob_row], gap=0.5)

    preview_cron_logs_button = mo.ui.run_button(
        label="\U0001f648 Hide preview" if get_preview_shown() else "\U0001f441\ufe0f Preview",
        tooltip="Hide preview" if get_preview_shown() else "Show last 20 lines of cron_jobs.txt",
    )
    _header_row = mo.hstack(
        [
            mo.md("<div style='border-left: 4px solid #7c3aed; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #7c3aed;'>\U0001f510 Admin</span></div>"),
            preview_cron_logs_button,
        ],
        justify="space-between",
        align="center",
    )

    mo.vstack(
        [
            _header_row,
            _admin_body,
        ]
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
    return admin_password_w, preview_cron_logs_button, unlock_admin_button


@app.cell
def _(get_preview_shown, mo, preview_cron_logs_button, set_preview_shown):
    mo.stop(not preview_cron_logs_button.value)
    set_preview_shown(not get_preview_shown())
    return


@app.cell
def _(mo):
    refresh_preview_button = mo.ui.run_button(
        label="\U0001f504",
        tooltip="Refresh — reload cron_jobs.txt",
    )
    return (refresh_preview_button,)


@app.cell
def _(Path, get_preview_shown, mo, refresh_preview_button):
    mo.stop(not get_preview_shown())
    _log_file = Path(__file__).parent.parent / "logs" / "cron_jobs.txt"
    if _log_file.exists():
        _lines = _log_file.read_text().splitlines()
        _last_20 = "\n".join(_lines[-20:]) if _lines else "(empty file)"
    else:
        _last_20 = "\u26a0\ufe0f  File not found: logs/cron_jobs.txt"
    mo.vstack(
        [
            mo.hstack(
                [
                    mo.md("<span style='color: #9d7fe8; font-size: 0.85rem; font-weight: 600;'>\U0001f441\ufe0f  cron_jobs.txt \u2014 last 20 lines</span>"),
                    refresh_preview_button,
                ],
                justify="space-between",
                align="center",
            ),
            mo.md(f"```\n{_last_20}\n```"),
        ],
        gap=0.25,
    ).style(
        {
            "background": "#0d1117",
            "border": "1px solid #334155",
            "border-radius": "6px",
            "padding": "10px",
            "margin-top": "6px",
        }
    )
    return


@app.cell
def _(Path, get_pre_proc_cronjob_enabled):

    _cronjobs_dir = Path(__file__).parent.parent / "cronjobs"
    _flag_file = _cronjobs_dir / "pre_processing_job.enabled"
    if get_pre_proc_cronjob_enabled():
        _flag_file.parent.mkdir(parents=True, exist_ok=True)
        _flag_file.touch()
    else:
        if _flag_file.exists():
            _flag_file.unlink()
    return


@app.cell
def _(get_pre_proc_cronjob_enabled, mo):
    hyperct_mode_checked = mo.ui.checkbox(
        value=True,
        label="The instrument has been configure for HyperCT mode (in the DAS console)",
    )
    remote_key_checked = mo.ui.checkbox(
        value=True,
        label="Remote key has been configured by the imaging team (added to config file)",
    )
    cronjob_checked = mo.ui.checkbox(
        value=get_pre_proc_cronjob_enabled(),
        label="pre-processing cronjob running cronjob",
        disabled=True,
    )

    checklist_ui = mo.vstack(
        [
            # mo.md("<span style='color: #90caf9;'>📋  Starting checklist</span>"),
            mo.md("<div style='border-left: 4px solid #2980b9; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #2980b9;'>📋  Starting checklist</span> <span style='font-size: 0.85rem; font-weight: 400; color: #888; text-transform: none;'></span></div>"),
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
    return cronjob_checked, hyperct_mode_checked, remote_key_checked


@app.cell
def _(cronjob_checked, hyperct_mode_checked, remote_key_checked):
    """Derive checklist_ready: True only when all three checklist boxes are ticked."""
    checklist_ready = bool(
        hyperct_mode_checked.value and remote_key_checked.value and cronjob_checked.value
    )
    return (checklist_ready,)


@app.cell
def _(
    checklist_ready,
    get_debug_mode_unlocked,
    get_live_enabled,
    get_pre_proc_started,
    mo,
    set_live_enabled,
):
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
    ipts_w = mo.ui.text(value="36914", label="IPTS-", disabled=_started)
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
            mo.md("<div style='border-left: 4px solid #2980b9; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #2980b9;'>⚙️ Runtime parameters</span> <span style='font-size: 0.85rem; font-weight: 400; color: #888; text-transform: none;'>(fields marked with <span style='color: red;'>✱</span> are mandatory)</span></div>"),
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
        description_w,
        first_run_w,
        initial_angles_w,
        ipts_w,
        live_w,
        motor_w,
        n_tiff_w,
        nbr_obs_w,
        new_experiment_w,
        proton_charge_w,
        sample_name_w,
        user_conditions_w,
    )


@app.cell
def _(
    checklist_ready,
    get_ob_alignment_selection,
    get_sample_alignment_selection,
    ipts_w,
    mo,
    set_ob_alignment_selection,
    set_sample_alignment_selection,
):
    """Alignment file selection: lists CSV files in the IPTS alignment folder, splits them by
    the '_OB_' token (sample files exclude it; OB files require it), and presents two filtered
    dropdowns. Selections are persisted in state so they survive debug-mode cell reruns."""
    import os
    mo.stop(not checklist_ready)

    _alignment_dir = f"/SNS/VENUS/IPTS-{ipts_w.value}/images/tpx1/alignment"
    if not os.path.exists(_alignment_dir):
        sample_alignment_w = None
        ob_alignment_w = None
        alignment_ui = mo.callout(
            mo.md("**Check the IPTS number! Path does not exist!**"),
            kind="danger",
        )
    else:
        _csv_files = sorted(
            [
                _name
                for _name in os.listdir(_alignment_dir)
                if _name.lower().endswith(".csv")
            ]
        )
        _sample_files = [_name for _name in _csv_files if "_OB_" not in _name]
        _ob_files = [_name for _name in _csv_files if "_OB_" in _name]

        _sample_options = {
            _name: os.path.join(_alignment_dir, _name)
            for _name in _sample_files
        }
        _ob_options = {
            _name: os.path.join(_alignment_dir, _name)
            for _name in _ob_files
        }

        _remembered_sample = get_sample_alignment_selection()
        _remembered_ob = get_ob_alignment_selection()

        # remembered selection is stored as a full path; resolve back to key (filename)
        _sample_value = next(
            (k for k, v in _sample_options.items() if _remembered_sample and v == _remembered_sample[0]),
            None,
        )
        _ob_value = next(
            (k for k, v in _ob_options.items() if _remembered_ob and v == _remembered_ob[0]),
            None,
        )

        if _sample_value is None:
            set_sample_alignment_selection([])
        if _ob_value is None:
            set_ob_alignment_selection([])

        def _on_sample_change(_value):
            set_sample_alignment_selection([_value] if _value else [])

        def _on_ob_change(_value):
            set_ob_alignment_selection([_value] if _value else [])

        sample_alignment_w = mo.ui.dropdown(
            options=_sample_options,
            value=_sample_value,
            label="Sample alignment file <span style='color: red;'>✱</span>",
            on_change=_on_sample_change,
            full_width=True,
        )
        ob_alignment_w = mo.ui.dropdown(
            options=_ob_options,
            value=_ob_value,
            label="Open beam alignment file <span style='color: red;'>✱</span>",
            on_change=_on_ob_change,
            full_width=True,
        )

        alignment_ui = mo.vstack([sample_alignment_w, ob_alignment_w], gap=0.5)

    alignment_ui
    return ob_alignment_w, sample_alignment_w


@app.cell
def _(checklist_ready, get_debug_mode_password, get_debug_mode_unlocked, mo):
    """Debug mode access panel: password field and lock/unlock toggle button."""
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
    """State: whether debug mode is currently unlocked (bool)."""
    get_debug_mode_unlocked, set_debug_mode_unlocked = mo.state(False)
    return get_debug_mode_unlocked, set_debug_mode_unlocked


@app.cell
def _(mo):
    """State: transient password string, cleared immediately after each unlock attempt."""
    get_debug_mode_password, set_debug_mode_password = mo.state("")
    return get_debug_mode_password, set_debug_mode_password


@app.cell
def _(mo):
    """State: whether live execution (hyperct code) is enabled; set to False when debug mode is unlocked."""
    get_live_enabled, set_live_enabled = mo.state(True)
    return get_live_enabled, set_live_enabled


@app.cell
def _(mo):
    """State: persisted sample alignment file path (as a list) so selection survives cell reruns."""
    get_sample_alignment_selection, set_sample_alignment_selection = mo.state([])
    return get_sample_alignment_selection, set_sample_alignment_selection


@app.cell
def _(mo):
    """State: persisted open-beam alignment file path (as a list) so selection survives cell reruns."""
    get_ob_alignment_selection, set_ob_alignment_selection = mo.state([])
    return get_ob_alignment_selection, set_ob_alignment_selection


@app.cell
def _(mo):
    get_admin_unlocked, set_admin_unlocked = mo.state(False)
    return get_admin_unlocked, set_admin_unlocked


@app.cell
def _(mo):
    get_admin_password, set_admin_password = mo.state("")
    return get_admin_password, set_admin_password


@app.cell
def _(Path, mo):
    _flag_file = Path(__file__).parent.parent / "cronjobs" / "pre_processing_job.enabled"
    get_pre_proc_cronjob_enabled, set_pre_proc_cronjob_enabled = mo.state(_flag_file.exists())
    return get_pre_proc_cronjob_enabled, set_pre_proc_cronjob_enabled


@app.cell
def _(mo):
    get_preview_shown, set_preview_shown = mo.state(False)
    return get_preview_shown, set_preview_shown


@app.cell
def _(
    admin_password_w,
    get_admin_unlocked,
    mo,
    set_admin_password,
    set_admin_unlocked,
    unlock_admin_button,
):
    mo.stop(not unlock_admin_button.value)

    if get_admin_unlocked():
        set_admin_unlocked(False)
        set_admin_password("")
    else:
        _is_correct = str(admin_password_w.value).strip() == "venus"
        set_admin_unlocked(_is_correct)
        set_admin_password("")
    return


@app.cell
def _(
    checklist_ready,
    debug_password_w,
    get_debug_mode_unlocked,
    mo,
    set_debug_mode_password,
    set_debug_mode_unlocked,
    set_live_enabled,
    unlock_debug_mode_button,
):
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
    return


@app.cell
def _(mo):
    """State: whether the pre-processing step has been launched; disables input fields once True."""
    get_pre_proc_started, set_pre_proc_started = mo.state(False)
    return get_pre_proc_started, set_pre_proc_started


@app.cell
def _(checklist_ready, get_debug_mode_unlocked, get_pre_proc_started, mo):
    mo.stop(not checklist_ready)

    _started = get_pre_proc_started()
    _is_unlocked = get_debug_mode_unlocked()
    _debug_locked = not _is_unlocked

    create_0deg_projection_button = mo.ui.run_button(
        label="Create 0degree projection",
        disabled=_started or _debug_locked,
    )
    create_180deg_projection_button = mo.ui.run_button(
        label="Create 180° projection",
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
    return


@app.cell
def _(
    checklist_ready,
    first_run_w,
    get_ob_alignment_selection,
    get_pre_proc_started,
    get_sample_alignment_selection,
    ipts_w,
    mo,
    ob_alignment_w,
    sample_alignment_w,
    sample_name_w,
    user_conditions_w,
):
    """Validation + start button: checks all mandatory fields (IPTS, sample name, conditions,
    first run, both alignment files) and shows a warning list if any are missing.
    Enables the 'Start open beams, 0 and 180° projections' button only when all are filled."""
    mo.stop(not checklist_ready)

    _started = get_pre_proc_started()
    _missing_parameters = []
    if not str(ipts_w.value).strip():
        _missing_parameters.append("IPTS")
    if not str(sample_name_w.value).strip():
        _missing_parameters.append("sample name")
    if not str(user_conditions_w.value).strip():
        _missing_parameters.append("sample conditions")
    if not str(first_run_w.value).strip():
        _missing_parameters.append("first run")
    _sample_alignment_value = (
        sample_alignment_w.value
        if (sample_alignment_w is not None and sample_alignment_w.value)
        else get_sample_alignment_selection()
    )
    _ob_alignment_value = (
        ob_alignment_w.value
        if (ob_alignment_w is not None and ob_alignment_w.value)
        else get_ob_alignment_selection()
    )

    if not _sample_alignment_value:
        _missing_parameters.append("sample alignment file")
    if not _ob_alignment_value:
        _missing_parameters.append("open beam alignment file")

    _mandatory_fields_filled = not _missing_parameters

    missing_parameters_box = (
        mo.callout(
            mo.md(
                "**Missing parameters:**\n\n"
                + "\n".join(f"- {parameter}" for parameter in _missing_parameters)
            ),
            kind="warn",
        )
        if _missing_parameters
        else mo.md("")
    )

    start_pre_processing_button = mo.ui.run_button(
        label="Start open beams, 0 and 180° projections",
        full_width=True,
        disabled=_started or not _mandatory_fields_filled,
    )

    mo.vstack([missing_parameters_box, start_pre_processing_button], gap=0.5)
    return (start_pre_processing_button,)


@app.cell
def _(
    Path,
    checklist_ready,
    description_w,
    first_run_w,
    get_ob_alignment_selection,
    get_sample_alignment_selection,
    initial_angles_w,
    ipts_w,
    live_w,
    mo,
    motor_w,
    n_tiff_w,
    nbr_obs_w,
    new_experiment_w,
    proton_charge_w,
    sample_name_w,
    set_pre_proc_started,
    start_pre_processing_button,
    user_conditions_w,
):
    """Pre-processing launch: reads all widget values, instantiates AiAutomatedLoop and calls
    launch_pre_processing_step(). Marks pre-processing as started so downstream cells can react."""
    mo.stop(not checklist_ready)
    mo.stop(not start_pre_processing_button.value)
    set_pre_proc_started(True)

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

    # Keep last selected alignments available even when debug-mode toggles rebuild widgets.
    sample_alignment = get_sample_alignment_selection()
    ob_alignment = get_ob_alignment_selection()

    raw_angles = str(initial_angles_w.value).strip()
    if raw_angles:
        list_of_initial_angles = [float(v.strip()) for v in raw_angles.split(",") if v.strip()]
    else:
        list_of_initial_angles = None

    import logging

    _log_file = Path(__file__).parent.parent / "logs" / "ai_automated_loop_marimo.log"
    _log_file.parent.mkdir(parents=True, exist_ok=True)
    _logger = logging.getLogger("ai_automated_loop_marimo")
    if not _logger.handlers:
        _handler = logging.FileHandler(_log_file)
        _handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
        _logger.addHandler(_handler)
        _logger.setLevel(logging.INFO)

    _logger.info(
        "Pre-processing launched | "
        f"live={live} | new_experiment={new_experiment} | IPTS={IPTS} | "
        f"sample_name={sample_name!r} | user_conditions={user_conditions!r} | "
        f"motor={motor} | description={description_of_exp!r} | "
        f"nbr_obs={nbr_obs} | proton_charge={proton_charge} | "
        f"n_tiff={number_of_tiff_for_each_run} | first_run={first_run} | "
        f"sample_alignment={sample_alignment} | ob_alignment={ob_alignment} | "
        f"initial_angles={list_of_initial_angles}"
    )

    # # this is where we start running the pre-processing algo
    # from notetooks.code import AiAutomatedLoop
    # o_ai = AiAutomatedLoop(
    #     sample_name=sample_name,
    #     user_conditions=user_conditions,
    #     new_experiment=new_experiment,
    #     ipts=IPTS,
    #     debug=debug,
    #     description_of_exp=description_of_exp,
    #     nbr_obs=nbr_obs,
    #     proton_charge=proton_charge,
    #     number_of_tiff_for_each_run=number_of_tiff_for_each_run,
    #     live=live,
    #     first_run=first_run,
    #     motor=motor,
    # )
    # o_ai.launch_pre_processing_step()
    # set_pre_proc_started(True)
    # return (o_ai,)
    return


@app.cell
def _(checklist_ready, get_pre_proc_started, mo):
    mo.stop(not checklist_ready)
    mo.stop(not get_pre_proc_started())
    check_pre_process_status_button = mo.ui.run_button(
        label="Check pre-process status",
        full_width=True,
    )
    check_pre_process_status_button
    return (check_pre_process_status_button,)


@app.cell
def _(check_pre_process_status_button, checklist_ready, mo):
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
def _(checklist_ready, mo, o_ai, pre_process_is_done):
    mo.stop(not checklist_ready)
    mo.stop(not pre_process_is_done)

    # we need to calculate the center of rotation
    o_ai.calculate_center_of_rotation()

    # we need to crop
    o_ai.crop_images()

    # we need to define up to 5 TOF ranges
    o_ai.define_tof_ranges()
    return


if __name__ == "__main__":
    app.run()
