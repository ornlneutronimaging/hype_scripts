import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    """Bootstrap: import marimo, locate the repo root via pixi.toml and add it to sys.path."""
    import marimo as mo
    from pathlib import Path
    import sys
    import numpy as np

    # Find project root by looking for pixi.toml.
    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents]
    repo_root = next((p for p in candidates if (p / "pixi.toml").exists()), cwd)
    venus_source_detector_distance_m = 25.0  # hardcoded for now; will eventually be read from config file

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Import only after repo_root is on sys.path. Note: the package is
    # `notebooks.code`, not `code` (which shadows the stdlib `code` module).
    from notebooks.code.ai_automated_loop import AiAutomatedLoop

    return AiAutomatedLoop, Path, mo, np, venus_source_detector_distance_m


@app.cell
def _(get_experiment_mode, mo):
    new_exp_mode_button = mo.ui.run_button(
        label="\U0001f195 New experiment",
        tooltip="Start fresh \u2014 form fields will be cleared",
    )
    continue_exp_mode_button = mo.ui.run_button(
        label="\u25b6\ufe0f Continue experiment",
        tooltip="Reload settings from the selected config file",
    )
    _panel = mo.vstack(
        [
            mo.md("<div style='border-left: 4px solid #16a34a; padding: 4px 12px; margin-bottom: 8px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #16a34a;'>\U0001f9ea What would you like to do?</span></div>"),
            mo.hstack([new_exp_mode_button, continue_exp_mode_button], justify="start", align="center", gap=1),
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
    ) if get_experiment_mode() is None else mo.md("")
    _panel
    return continue_exp_mode_button, new_exp_mode_button


@app.cell
def _(
    get_reset_counter,
    mo,
    new_exp_mode_button,
    set_experiment_mode,
    set_ob_alignment_selection,
    set_reset_counter,
    set_sample_alignment_selection,
):
    mo.stop(not new_exp_mode_button.value)
    set_experiment_mode("new")
    set_reset_counter(get_reset_counter() + 1)
    set_sample_alignment_selection([])
    set_ob_alignment_selection([])
    return


@app.cell
def _(continue_exp_mode_button, mo, set_experiment_mode):
    mo.stop(not continue_exp_mode_button.value)
    set_experiment_mode("continue")
    return


@app.cell
def _(
    Path,
    get_active_config_file_option,
    get_admin_password,
    get_admin_unlocked,
    get_config_preview_shown,
    get_full_loop_cronjob_enabled,
    get_pre_proc_cronjob_enabled,
    get_preview_shown,
    mo,
    set_active_config_file_option,
    set_full_loop_cronjob_enabled,
    set_pre_proc_cronjob_enabled,
):
    import yaml as _yaml

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
    _full_loop_cronjob_w = mo.ui.checkbox(
        value=get_full_loop_cronjob_enabled(),
        label="Run full loop cronjob",
        on_change=set_full_loop_cronjob_enabled,
    )
    _config_file_w = mo.ui.dropdown(
        options={
            "config": "config",
            "config_debug_jean": "config_debug_jean",
        },
        value=get_active_config_file_option(),
        label="config file",
        on_change=set_active_config_file_option,
    )
    _cronjob_toggles = mo.hstack([_pre_proc_cronjob_w, _full_loop_cronjob_w], justify="start", align="center", gap=1)
    _cronjob_row = _cronjob_toggles if get_admin_unlocked() else mo.vstack([_cronjob_toggles]).style(
        {"pointer-events": "none", "opacity": "0.45"}
    )
    _config_file_row = _config_file_w if get_admin_unlocked() else mo.vstack([_config_file_w]).style(
        {"pointer-events": "none", "opacity": "0.45"}
    )

    # EIC token row
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_eic = _yaml.safe_load(_f) or {}
        _current_token = str(_cfg_eic.get("EIC_vals", {}).get("eic_token", ""))
    except OSError:
        _current_token = ""
    eic_token_w = mo.ui.text(
        value=_current_token,
        label="EIC token",
        full_width=True,
        disabled=not get_admin_unlocked(),
    )
    save_eic_token_button = mo.ui.run_button(
        label="\U0001f4be Save EIC token",
        disabled=not get_admin_unlocked(),
    )
    _eic_token_row = mo.vstack([
        eic_token_w,
        mo.hstack([save_eic_token_button], justify="end"),
    ], gap=0.25)
    _eic_token_row_styled = _eic_token_row if get_admin_unlocked() else mo.vstack([_eic_token_row]).style(
        {"pointer-events": "none", "opacity": "0.45"}
    )

    _admin_body = mo.vstack([admin_password_row, _cronjob_row, _config_file_row, _eic_token_row_styled], gap=0.5)

    preview_cron_logs_button = mo.ui.run_button(
        label="\U0001f648 Hide preview" if get_preview_shown() else "\U0001f441\ufe0f Preview Cronjob",
        tooltip="Hide preview" if get_preview_shown() else "Show last 20 lines of cron_jobs.txt",
        disabled=not get_admin_unlocked(),
    )
    preview_config_button = mo.ui.run_button(
        label="\U0001f648 Hide config" if get_config_preview_shown() else "\U0001f441\ufe0f Preview Config",
        tooltip="Hide config" if get_config_preview_shown() else f"Show {get_active_config_file_option()}.yaml",
        disabled=not get_admin_unlocked(),
    )
    clear_log_button = mo.ui.run_button(
        label="\U0001f5d1\ufe0f Clear log",
        tooltip="Clear the pre-processing log file",
        disabled=not get_admin_unlocked(),
    )
    _header_row = mo.hstack(
        [
            mo.md("<div style='border-left: 4px solid #7c3aed; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #7c3aed;'>\U0001f510 Admin</span></div>"),
            mo.hstack([preview_cron_logs_button, preview_config_button, clear_log_button ], justify="end", align="center", gap=0.5),
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
    return (
        admin_password_w,
        clear_log_button,
        eic_token_w,
        preview_config_button,
        preview_cron_logs_button,
        save_eic_token_button,
        unlock_admin_button,
    )


@app.cell
def _(Path, clear_log_button, ipts_w, mo):
    mo.stop(not clear_log_button.value)
    _log_file = Path(__file__).parent.parent / "logs" / f"ai_processing_loop_{ipts_w.value}.log"
    if _log_file.exists():
        _log_file.write_text("")
    return


@app.cell
def _(
    Path,
    eic_token_w,
    get_active_config_file_option,
    mo,
    save_eic_token_button,
):
    import re as _re
    mo.stop(not save_eic_token_button.value)
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        _content = _cfg_path.read_text()
        _new_token = str(eic_token_w.value).strip()
        _content = _re.sub(
            r"^(\s+eic_token:\s*).*$",
            lambda m: f"{m.group(1)}{_new_token}",
            _content,
            flags=_re.MULTILINE,
        )
        _cfg_path.write_text(_content)
    except OSError:
        pass
    return


@app.cell
def _(Path, mo):
    _code_init_file = Path(__file__).parent / "code" / "__init__.py"
    _config_line = 'config_file = _top_path / "configs" / "config.yaml"'
    _debug_line = 'config_file = _top_path / "configs" / "config_debug_jean.yaml"'

    def _normalize_line(line: str) -> str:
        _stripped = line.lstrip()
        if _stripped.startswith("#"):
            _stripped = _stripped[1:].lstrip()
        return _stripped.strip()

    def _read_active_config_file_option() -> str:
        try:
            _lines = _code_init_file.read_text().splitlines()
        except OSError:
            return "config_debug_jean"

        for _line in _lines:
            _normalized = _normalize_line(_line)
            if _normalized.startswith("config_file") and not _line.lstrip().startswith("#"):
                if "config_debug_jean.yaml" in _normalized:
                    return "config_debug_jean"
                if "config.yaml" in _normalized:
                    return "config"

        return "config_debug_jean"
    get_active_config_file_option, _set_active_config_file_option = mo.state(
        _read_active_config_file_option()
    )

    def set_active_config_file_option(option: str) -> None:
        if option not in {"config", "config_debug_jean"}:
            return

        try:
            _lines = _code_init_file.read_text().splitlines(keepends=True)
        except OSError:
            return

        _updated_lines = []
        for _line in _lines:
            _line_ending = "\n" if _line.endswith("\n") else ""
            _content = _line[:-1] if _line_ending else _line
            _indent = _content[: len(_content) - len(_content.lstrip())]
            _normalized = _normalize_line(_content)

            if _normalized == _config_line:
                if option == "config":
                    _updated_lines.append(f"{_indent}{_config_line}{_line_ending}")
                else:
                    _updated_lines.append(f"{_indent}# {_config_line}{_line_ending}")
            elif _normalized == _debug_line:
                if option == "config_debug_jean":
                    _updated_lines.append(f"{_indent}{_debug_line}{_line_ending}")
                else:
                    _updated_lines.append(f"{_indent}# {_debug_line}{_line_ending}")
            else:
                _updated_lines.append(_line)

        try:
            _code_init_file.write_text("".join(_updated_lines))
        except OSError:
            return

        _set_active_config_file_option(option)

    return get_active_config_file_option, set_active_config_file_option


@app.cell
def _(Path, get_active_config_file_option):
    import yaml as _yaml

    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"

    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}

    def _normalize_alignment_value(raw_value):
        if isinstance(raw_value, list):
            return [str(_path) for _path in raw_value if _path]
        if isinstance(raw_value, str) and raw_value and raw_value != "XXXXX.csv":
            return [raw_value]
        return []

    config_widget_defaults = {
        "sample_alignment": _normalize_alignment_value(
            _cfg_data.get("sample_alignment_file", [])
        ),
        "ob_alignment": _normalize_alignment_value(
            _cfg_data.get("ob_alignment_file", [])
        ),
    }
    return


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
            mo.Html("<script>window.scrollTo(0, document.body.scrollHeight);</script>"),
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
def _(
    get_config_preview_shown,
    mo,
    preview_config_button,
    set_config_preview_shown,
):
    mo.stop(not preview_config_button.value)
    set_config_preview_shown(not get_config_preview_shown())
    return


@app.cell
def _(mo):
    refresh_config_button = mo.ui.run_button(
        label="\U0001f504",
        tooltip="Refresh \u2014 reload config file",
    )
    return (refresh_config_button,)


@app.cell
def _(
    Path,
    get_active_config_file_option,
    get_config_preview_shown,
    mo,
    refresh_config_button,
):
    import html as _html_cfg
    mo.stop(not get_config_preview_shown())
    _cfg_name = get_active_config_file_option()
    _cfg_file_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    if _cfg_file_path.exists():
        _cfg_content = _html_cfg.escape(_cfg_file_path.read_text())
    else:
        _cfg_content = f"\u26a0\ufe0f  File not found: configs/{_cfg_name}.yaml"
    mo.vstack(
        [
            mo.Html("<script>window.scrollTo(0, document.body.scrollHeight);</script>"),
            mo.hstack(
                [
                    mo.md(f"<span style='color: #9d7fe8; font-size: 0.85rem; font-weight: 600;'>\U0001f441\ufe0f  {_cfg_name}.yaml</span>"),
                    refresh_config_button,
                ],
                justify="space-between",
                align="center",
            ),
            mo.Html(
                f"<pre id='cfg-preview-box' style='overflow-y: auto; max-height: 400px; margin: 0; padding: 8px; "
                f"background: #0d1117; color: #6b7280; font-size: 0.78rem; "
                f"border-radius: 4px; white-space: pre-wrap; word-break: break-all;'>{_cfg_content}</pre>"
                f"<script>(function(){{var e=document.getElementById('cfg-preview-box');if(e)e.scrollTop=e.scrollHeight;}})();</script>"
            ),
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
def _(Path, get_full_loop_cronjob_enabled, get_pre_proc_cronjob_enabled):

    _cronjobs_dir = Path(__file__).parent.parent / "cronjobs"
    _pre_proc_flag_file = _cronjobs_dir / "pre_processing_job.enabled"
    _full_loop_flag_file = _cronjobs_dir / "full_loop_job.enabled"

    if get_pre_proc_cronjob_enabled():
        _pre_proc_flag_file.parent.mkdir(parents=True, exist_ok=True)
        _pre_proc_flag_file.touch()
    else:
        if _pre_proc_flag_file.exists():
            _pre_proc_flag_file.unlink()

    if get_full_loop_cronjob_enabled():
        _full_loop_flag_file.parent.mkdir(parents=True, exist_ok=True)
        _full_loop_flag_file.touch()
    else:
        if _full_loop_flag_file.exists():
            _full_loop_flag_file.unlink()
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
    return hyperct_mode_checked, remote_key_checked


@app.cell
def _(hyperct_mode_checked, remote_key_checked):
    """Derive checklist_ready: True only when the two manual checklist boxes are ticked.
    The cronjob checkbox is a read-only status indicator and no longer gates the UI."""
    checklist_ready = bool(
        hyperct_mode_checked.value and remote_key_checked.value
    )
    return (checklist_ready,)


@app.cell
def _(
    Path,
    checklist_ready,
    get_active_config_file_option,
    get_debug_mode_unlocked,
    get_experiment_mode,
    get_live_enabled,
    get_pre_proc_started,
    get_reset_counter,
    mo,
    set_live_enabled,
):
    import yaml as _yaml
    mo.stop(not checklist_ready)
    mo.stop(get_experiment_mode() is None)

    _started = get_pre_proc_started()
    _debug_locked = get_debug_mode_unlocked()
    _is_reset = get_reset_counter() > 0

    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}
    _eic = _cfg_data.get("EIC_vals", {})
    _angles_list = _cfg_data.get("list_of_initial_angles", []) or []
    _angles_str = ", ".join(str(_a) for _a in _angles_list) if _angles_list else ""

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
    new_experiment_button = mo.ui.run_button(
        label="New experiment",
        tooltip="Reset form fields for a new experiment",
    )
    ipts_w = mo.ui.text(value=str(_eic.get("ipts", "")), label="IPTS-", disabled=_started)
    required_marker = mo.md("<span style='color: red; font-size: 1.25rem;'>*</span>")
    ipts_row = mo.hstack([ipts_w, required_marker], justify="start", align="end", gap=0.25)
    sample_name_w = mo.ui.text(value="" if _is_reset else str(_eic.get("sample_name", "test_sample")), label="sample name (10 chars max)", disabled=_started)
    user_conditions_w = mo.ui.text(value="" if _is_reset else str(_eic.get("user_con", _eic.get("user_conditions", "T10K"))), label="sample conditions (10 chars max)", disabled=_started)
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
    motor_w = mo.ui.number(start=1, stop=6, step=1, value=int(_eic.get("motor_number", 1)), label="motor")
    motor_row = mo.hstack([motor_w], justify="start", widths=[5])
    description_w = mo.ui.text(
        value="" if _is_reset else str(_eic.get("scan_description", "testing EIC in May with Shimin and Jean")),
        label="description of experiment",
        full_width=True,
        disabled=_started,
    )
    description_w_style = description_w.style({"width": "700px", "min-width": "700px"})    
    description_row = mo.hstack(
        [description_w_style, mo.md("<span style='color: #888; font-size: 0.85rem; font-style: italic;'>Optional</span>")],
        justify="start",
        align="end",
        gap=0.5,
        widths=["1fr", "auto"],
    ).style({"width": "100%"})    
    nbr_obs_w = mo.ui.number(start=1, step=1, value=int(_eic.get("number_of_obs", 3)), label="nbr of open beams")
    nbr_obs_row = mo.hstack([nbr_obs_w], justify="start", widths=[10])
    nbr_proj_w = mo.ui.number(start=1, stop=10, step=1, value=int(_eic.get("number_of_projections_at_each_angle", 1)), label="number of projections at each angle", disabled=True)
    nbr_proj_row = mo.hstack([nbr_proj_w], justify="start", widths=[10])
    proton_charge_w = mo.ui.number(start=0.0, step=0.01, value=float(_eic.get("proton_charge", 0.1)), label="proton charge (C)")
    proton_charge_row = mo.hstack([proton_charge_w], justify="start", widths=[10])
    initial_angles_w = mo.ui.text(
        value="" if _is_reset else _angles_str,
        label="list of initial angles (e.g., 0.0, 90.0, 180.0)",
        disabled=_started,
        full_width=True,
    )
    initial_angles_w_style = initial_angles_w.style({"width": "700px", "min-width": "700px"})
    initial_angles_row = mo.hstack(
        [initial_angles_w_style, mo.md("<span style='color: #888; font-size: 0.85rem; font-style: italic;'>Optional</span>")],
        justify="start",
        align="end",
        gap=0.5,
    )

    controls = mo.vstack(
        [
            mo.md("<div style='border-left: 4px solid #2980b9; padding: 4px 12px; margin-bottom: 4px;'><span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #2980b9;'>⚙️ Runtime parameters</span> <span style='font-size: 0.85rem; font-weight: 400; color: #888; text-transform: none;'>(fields marked with <span style='color: red;'>✱</span> are mandatory)</span></div>"),
            new_experiment_button,
            mo.md("<hr style='border: none; border-top: 1px solid #334155; margin: 4px 0;'>"),
            live_row,
            ipts_row,
            sample_name_row,
            user_conditions_row,
            motor_row,
            description_row,
            nbr_obs_row,
            nbr_proj_row,
            proton_charge_row,
            initial_angles_row,
        ]
    )
    controls
    return (
        description_w,
        initial_angles_w,
        ipts_w,
        live_w,
        motor_w,
        nbr_obs_w,
        nbr_proj_w,
        new_experiment_button,
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
        # _ob_files = [_name for _name in _csv_files if "_OB_" in _name]
        _ob_files = [_name for _name in _csv_files if "_OB_" not in _name]

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
def _(
    Path,
    get_pre_proc_started,
    get_reset_counter,
    ipts_w,
    mo,
    new_experiment_button,
    set_experiment_mode,
    set_ob_alignment_selection,
    set_pre_proc_started,
    set_reset_counter,
    set_sample_alignment_selection,
):
    mo.stop(not new_experiment_button.value)
    set_experiment_mode("new")
    set_reset_counter(get_reset_counter() + 1)
    if get_pre_proc_started():
        set_pre_proc_started(False)
    set_sample_alignment_selection([])
    set_ob_alignment_selection([])
    _log_file = Path(__file__).parent.parent / "logs" / f"ai_processing_loop_{ipts_w.value}.log"
    if _log_file.exists():
        _log_file.write_text("")
    return


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
def _(Path, get_active_config_file_option, mo):
    """State: persisted sample alignment file path (as a list) so selection survives cell reruns."""
    import yaml as _yaml
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _init_cfg = _yaml.safe_load(_f) or {}
        _raw = _init_cfg.get("sample_alignment_file", [])
        if isinstance(_raw, list):
            _initial_sample = [str(_p) for _p in _raw if _p]
        elif isinstance(_raw, str) and _raw and _raw != "XXXXX.csv":
            _initial_sample = [_raw]
        else:
            _initial_sample = []
    except OSError:
        _initial_sample = []
    get_sample_alignment_selection, set_sample_alignment_selection = mo.state(_initial_sample)
    return get_sample_alignment_selection, set_sample_alignment_selection


@app.cell
def _(Path, get_active_config_file_option, mo):
    """State: persisted open-beam alignment file path (as a list) so selection survives cell reruns."""
    import yaml as _yaml
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _init_cfg = _yaml.safe_load(_f) or {}
        _raw = _init_cfg.get("ob_alignment_file", [])
        if isinstance(_raw, list):
            _initial_ob = [str(_p) for _p in _raw if _p]
        elif isinstance(_raw, str) and _raw and _raw != "XXXXX.csv":
            _initial_ob = [_raw]
        else:
            _initial_ob = []
    except OSError:
        _initial_ob = []
    get_ob_alignment_selection, set_ob_alignment_selection = mo.state(_initial_ob)
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
def _(Path, mo):
    _flag_file = Path(__file__).parent.parent / "cronjobs" / "full_loop_job.enabled"
    get_full_loop_cronjob_enabled, set_full_loop_cronjob_enabled = mo.state(_flag_file.exists())
    return get_full_loop_cronjob_enabled, set_full_loop_cronjob_enabled


@app.cell
def _(mo):
    get_preview_shown, set_preview_shown = mo.state(False)
    return get_preview_shown, set_preview_shown


@app.cell
def _(mo):
    get_config_preview_shown, set_config_preview_shown = mo.state(False)
    return get_config_preview_shown, set_config_preview_shown


@app.cell
def _(mo):
    get_reset_counter, set_reset_counter = mo.state(0)
    return get_reset_counter, set_reset_counter


@app.cell
def _(mo):
    get_experiment_mode, set_experiment_mode = mo.state(None)
    return get_experiment_mode, set_experiment_mode


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
def _(Path, get_active_config_file_option, mo):
    """State: whether the pre-processing step has been launched.
    Initialised to True on startup when the pre_processing_table in the config is non-empty."""
    import yaml as _yaml
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}
    _table = _cfg_data.get("marimo", {}).get("pre_processing_table", {})
    _already_started = bool(
        _table.get("raw") or _table.get("corrected") or _table.get("final")
    )
    get_pre_proc_started, set_pre_proc_started = mo.state(_already_started)
    return get_pre_proc_started, set_pre_proc_started


@app.cell
def _(mo):
    get_log_preview_shown, set_log_preview_shown = mo.state(False)
    return get_log_preview_shown, set_log_preview_shown


@app.cell
def _(Path, get_active_config_file_option, mo):
    """State: run numbers that have passed each processing stage; pre-populated from config on startup."""
    import yaml as _yaml
    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}
    _table = _cfg_data.get("marimo", {}).get("pre_processing_table", {})
    _initial = {
        "raw": list(_table.get("raw") or []),
        "corrected": list(_table.get("corrected") or []),
        "final": list(_table.get("final") or []),
    }
    get_marimo_table_data, set_marimo_table_data = mo.state(_initial)
    return get_marimo_table_data, set_marimo_table_data


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
    get_ob_alignment_selection,
    get_pre_proc_cronjob_enabled,
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
    both alignment files) and shows a warning list if any are missing.
    The start button is also disabled when the pre-processing cronjob is not enabled."""
    mo.stop(not checklist_ready)

    _started = get_pre_proc_started()
    _cronjob_enabled = get_pre_proc_cronjob_enabled()
    _missing_parameters = []
    if not str(ipts_w.value).strip():
        _missing_parameters.append("IPTS")
    if not str(sample_name_w.value).strip():
        _missing_parameters.append("sample name")
    if not str(user_conditions_w.value).strip():
        _missing_parameters.append("sample conditions")
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
        label="Start open beams, 0° and 180° projections",
        full_width=True,
        disabled=_started or not _mandatory_fields_filled or not _cronjob_enabled,
    )

    if _started:
        validation_panel = mo.md("")
    else:
        validation_panel = mo.vstack([missing_parameters_box, start_pre_processing_button], gap=0.5)
    validation_panel
    return (start_pre_processing_button,)


@app.cell
def _(
    AiAutomatedLoop,
    checklist_ready,
    description_w,
    get_ob_alignment_selection,
    get_sample_alignment_selection,
    initial_angles_w,
    ipts_w,
    live_w,
    mo,
    motor_w,
    nbr_obs_w,
    nbr_proj_w,
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

    # Read widget values at click time so pre-processing uses the latest UI input.
    live = bool(live_w.value)
    new_experiment = True
    IPTS = int(ipts_w.value)
    sample_name = str(sample_name_w.value)
    user_conditions = str(user_conditions_w.value)
    motor = int(motor_w.value)
    description_of_exp = str(description_w.value)
    nbr_obs = int(nbr_obs_w.value)
    number_of_projections_at_each_angle = int(nbr_proj_w.value)
    proton_charge = float(proton_charge_w.value)

    # _cfg_name = get_active_config_file_option()
    # _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    # try:
    #     with open(_cfg_path, "r") as _f:
    #         _cfg_data = _yaml.safe_load(_f) or {}
    # except OSError:
    #     _cfg_data = {}

    # Keep last selected alignments available even when debug-mode toggles rebuild widgets.
    sample_alignment = get_sample_alignment_selection()
    ob_alignment = get_ob_alignment_selection()

    raw_angles = str(initial_angles_w.value).strip()
    if raw_angles:
        list_of_initial_angles = [float(v.strip()) for v in raw_angles.split(",") if v.strip()]
    else:
        list_of_initial_angles = None

    o_ai = AiAutomatedLoop(
        sample_name=sample_name,
        user_conditions=user_conditions,
        new_experiment=new_experiment,
        ipts=IPTS,
        description_of_exp=description_of_exp,
        nbr_obs=nbr_obs,
        number_of_projections_at_each_angle=number_of_projections_at_each_angle,
        proton_charge=proton_charge,
        live=live,
        motor=motor,
        sample_alignment=sample_alignment,
        ob_alignment=ob_alignment,
        list_of_initial_angles=list_of_initial_angles,
    )
    o_ai.launch_pre_processing_step()
    set_pre_proc_started(True)
    return


@app.cell
def _(
    Path,
    checklist_ready,
    get_active_config_file_option,
    get_marimo_table_data,
    get_pre_proc_started,
    mo,
    nbr_obs_w,
):
    """Show a table of planned runs as soon as pre-processing is started.
    Rows are built from list_of_obs_expected (OBs) and list_of_0_and_180_expected (0°/180°)
    read directly from the config, falling back to deriving them from starting_run_number
    + nbr_obs_w when those lists are absent."""
    mo.stop(not checklist_ready)
    mo.stop(not get_pre_proc_started())

    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        import yaml as _yaml

        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}

    _obs_expected = list(_cfg_data.get("list_of_obs_expected") or [])
    _zero_180_expected = list(_cfg_data.get("list_of_0_and_180_expected") or [])

    # Fall back to deriving from starting_run_number + nbr_obs when lists are absent.
    if not _obs_expected and not _zero_180_expected:
        _first_run = int(_cfg_data.get("starting_run_number", 8769))
        _nbr_obs = int(nbr_obs_w.value)
        _obs_expected = list(range(_first_run, _first_run + _nbr_obs))
        _zero_180_expected = [_first_run + _nbr_obs, _first_run + _nbr_obs + 1]

    _table_data = get_marimo_table_data()
    _raw_done = set(_table_data.get("raw", []))
    _corrected_done = set(_table_data.get("corrected", []))
    _final_done = set(_table_data.get("final", []))

    _DONE = "✅"
    _ACQUIRING = "📡 acquiring"
    _MISSING = "❌"
    _DONE_STATE = "✅ done"

    def _state_for_run(run_number: int) -> str:
        _all_complete = (
            run_number in _raw_done
            and run_number in _corrected_done
            and run_number in _final_done
        )
        return _DONE_STATE if _all_complete else _ACQUIRING

    _rows = []
    for _run_num in _obs_expected:
        _rows.append({
            "run number": _run_num,
            "type": "OB",
            "raw": _DONE if _run_num in _raw_done else _MISSING,
            "corrected": _DONE if _run_num in _corrected_done else _MISSING,
            "final": _DONE if _run_num in _final_done else _MISSING,
            "state": _state_for_run(_run_num),
        })
    _angle_labels = ["0°", "180°"]
    for _idx, _run_num in enumerate(_zero_180_expected):
        _label = _angle_labels[_idx] if _idx < len(_angle_labels) else f"{_idx * 180}°"
        _rows.append({
            "run number": _run_num,
            "type": _label,
            "raw": _DONE if _run_num in _raw_done else _MISSING,
            "corrected": _DONE if _run_num in _corrected_done else _MISSING,
            "final": _DONE if _run_num in _final_done else _MISSING,
            "state": _state_for_run(_run_num),
        })

    mo.ui.table(_rows, selection=None)
    return


@app.cell
def _(
    all_pre_proc_table_complete,
    checklist_ready,
    get_log_preview_shown,
    get_pre_proc_started,
    mo,
):
    mo.stop(not checklist_ready)
    mo.stop(not get_pre_proc_started())
    check_pre_process_status_button = mo.ui.run_button(
        label="Refresh table",
        disabled=all_pre_proc_table_complete,
    )
    preview_log_button = mo.ui.run_button(
        label="\U0001f648 Hide log" if get_log_preview_shown() else "\U0001f441\ufe0f Preview pre-processing log",
        tooltip="Hide log" if get_log_preview_shown() else "Show ai_processing_loop log",
    )
    mo.hstack(
        [check_pre_process_status_button, preview_log_button],
        justify="space-between",
        align="center",
    )
    return check_pre_process_status_button, preview_log_button


@app.cell
def _(get_log_preview_shown, mo, preview_log_button, set_log_preview_shown):
    mo.stop(not preview_log_button.value)
    set_log_preview_shown(not get_log_preview_shown())
    return


@app.cell
def _(mo):
    refresh_log_button = mo.ui.run_button(
        label="\U0001f504",
        tooltip="Refresh \u2014 reload log file",
    )
    return (refresh_log_button,)


@app.cell
def _(Path, get_log_preview_shown, ipts_w, mo, refresh_log_button):
    import html as _html
    mo.stop(not get_log_preview_shown())
    _log_file = Path(__file__).parent.parent / "logs" / f"ai_processing_loop_{ipts_w.value}.log"
    if _log_file.exists():
        _content = _html.escape(_log_file.read_text())
    else:
        _content = f"\u26a0\ufe0f  File not found: logs/ai_processing_loop_{ipts_w.value}.log"
    mo.vstack(
        [
            mo.Html("<script>window.scrollTo(0, document.body.scrollHeight);</script>"),
            mo.hstack(
                [
                    mo.md(f"<span style='color: #9d7fe8; font-size: 0.85rem; font-weight: 600;'>\U0001f441\ufe0f  ai_processing_loop_{ipts_w.value}.log</span>"),
                    refresh_log_button,
                ],
                justify="space-between",
                align="center",
            ),
            mo.Html(
                f"<pre id='log-preview-box' style='overflow-y: auto; max-height: 400px; margin: 0; padding: 8px; "
                f"background: #0d1117; color: #e5e7eb; font-size: 0.78rem; "
                f"border-radius: 4px; white-space: pre-wrap; word-break: break-all;'>{_content}</pre>"
                f"<script>(function(){{var e=document.getElementById('log-preview-box');if(e)e.scrollTop=e.scrollHeight;}})();</script>"
            ),
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
def _(
    check_pre_process_status_button,
    checklist_ready,
    mo,
    set_marimo_table_data,
):
    mo.stop(not checklist_ready)
    mo.stop(not check_pre_process_status_button.value)

    import yaml
    from notebooks.code import config_file as _config_file

    with open(_config_file, "r") as _f:
        _cfg = yaml.safe_load(_f)

    # Sync run-status lists from the marimo section of the config.
    _marimo_section = _cfg.get("marimo", {}).get("pre_processing_table", {})
    set_marimo_table_data({
        "raw": list(_marimo_section.get("raw", [])),
        "corrected": list(_marimo_section.get("corrected", [])),
        "final": list(_marimo_section.get("final", [])),
    })

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
    return


@app.cell
def _(
    Path,
    checklist_ready,
    get_active_config_file_option,
    get_marimo_table_data,
    mo,
):
    """Compute whether every expected pre-processing run (OBs + 0°/180°) is present in
    the 'final' column of the marimo table, making the Center-of-rotation section visible."""
    mo.stop(not checklist_ready)

    import yaml as _yaml

    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}

    _obs_expected = list(_cfg_data.get("list_of_obs_expected") or [])
    _zero_180_expected = list(_cfg_data.get("list_of_0_and_180_expected") or [])
    _all_expected = _obs_expected + _zero_180_expected

    _final_done = set(get_marimo_table_data().get("final", []))
    all_pre_proc_table_complete = bool(_all_expected) and all(r in _final_done for r in _all_expected)
    return (all_pre_proc_table_complete,)


@app.cell
def _(
    Path,
    all_pre_proc_table_complete,
    checklist_ready,
    get_active_config_file_option,
    get_pre_proc_started,
    ipts_w,
    mo,
    np,
):
    """Load 0° and 180° images, sum them, and compute the center of rotation. Runs once."""
    import glob as _glob
    import os as _os

    import h5py as _h5py
    import tifffile as _tifffile
    import yaml as _yaml

    mo.stop(not checklist_ready)
    mo.stop(not get_pre_proc_started())
    mo.stop(not all_pre_proc_table_complete)

    _cfg_name = get_active_config_file_option()
    _cfg_path = Path(__file__).parent.parent / "configs" / f"{_cfg_name}.yaml"
    try:
        with open(_cfg_path, "r") as _f:
            _cfg_data = _yaml.safe_load(_f) or {}
    except OSError:
        _cfg_data = {}

    _ipts = str(ipts_w.value).strip()
    _nexus_folder = _cfg_data.get("nexus_folder", f"/SNS/VENUS/IPTS-{_ipts}/nexus")
    _mcp_folder = _os.path.join(f"/SNS/VENUS/IPTS-{_ipts}", "shared/autoreduce/")
    _zero_180_expected = list(_cfg_data.get("list_of_0_and_180_expected") or [])

    def _resolve_image_folder(run_number):
        _nexus_file = _os.path.join(_nexus_folder, f"VENUS_{run_number}.nxs.h5")
        if not _os.path.exists(_nexus_file):
            return None, f"NeXus not found: {_nexus_file}"
        try:
            with _h5py.File(_nexus_file, "r") as _f:
                try:
                    _sub = _f["entry"]["DASlogs"]["BL10:Exp:IM:ImageFilePath"]["value"][-1][0].decode("utf-8")
                except KeyError:
                    _sub = _f["entry"]["DASlogs"]["BL10:Exp:IM:ConfigTpxFilePath"]["value"][0][0].decode("utf-8")
            return _os.path.join(_mcp_folder, _sub.strip()), None
        except Exception as _e:
            return None, f"Run {run_number}: {_e}"

    _angle_labels = ["0\u00b0", "180\u00b0"]
    cor_section_rows = []
    _image_folders = []
    spectra_ascii_file = None
    config_file = None
    for _idx, _run_num in enumerate(_zero_180_expected):
        _label = _angle_labels[_idx] if _idx < len(_angle_labels) else f"{_idx * 180}\u00b0"
        _folder, _err = _resolve_image_folder(_run_num)
        if _err:
            cor_section_rows.append(mo.callout(mo.md(f"**{_label}**: {_err}"), kind="danger"))
        else:
            spectra_ascii_file = _glob.glob(f"{_folder}/*Spectra*.txt")
            config_file = _glob.glob(f"{_folder}/summary.json") if config_file is None else config_file
            _tiffs = sorted(_glob.glob(f"{_folder}/*.tif*"))
            _image_folders.append((_run_num, _label, _folder, _tiffs))

    _tiffs_by_label = {lbl: tiffs for _, lbl, _, tiffs in _image_folders}
    _tiffs_0 = _tiffs_by_label.get("0\u00b0", [])
    _tiffs_180 = _tiffs_by_label.get("180\u00b0", [])

    if not _tiffs_0 or not _tiffs_180:
        cor_sum_0 = None
        cor_sum_180 = None
        profile_0 = None
        spectra_array = None
        detector_offset_us = 0.0
        cor_ny = 0
        cor_nx = 0
        cor_center_of_rotation = 0.0
        cor_section_rows.append(mo.callout(mo.md("No images found for 0\u00b0 or 180\u00b0."), kind="warn"))
    else:
        def _load(tiff_list):
            return np.array([_tifffile.imread(_p).astype(np.float32) for _p in tiff_list])
        def _load_spectra_ascii(spectra_file):
            # retrieve the first column of this tab-delimited file, skipping the header row
            return np.loadtxt(spectra_file, delimiter=",", skiprows=1, usecols=0)
        def _retrieve_detector_offset_us(json_cfg_file):
            # retrieve the detector offset from the JSON under the key detector_offset, value (in micros)
            import json as _json
            try:
                with open(json_cfg_file, "r") as _f:
                    _cfg = _json.load(_f)
                return float(_cfg["detector_offset"]["value"])
            except Exception:
                return 0.0

        _n_total = len(_tiffs_0) + len(_tiffs_180)
        with mo.status.spinner(title=f"Loading {_n_total} images\u2026"):
            _cor_sum_0_array = _load(_tiffs_0)
            cor_sum_0 = np.sum(_cor_sum_0_array, axis=0)
            profile_0 = np.sum(_cor_sum_0_array, axis=(1,2))
            _cor_sum_180_array = _load(_tiffs_180)
            cor_sum_180 = np.sum(_cor_sum_180_array, axis=0)

        spectra_array = _load_spectra_ascii(spectra_ascii_file[0]) if spectra_ascii_file else None
        detector_offset_us = _retrieve_detector_offset_us(config_file[0]) if config_file else 0.0

        cor_ny, cor_nx = cor_sum_0.shape
        from tomopy.recon.rotation import find_center_pc
        cor_center_of_rotation = float(find_center_pc(cor_sum_0, cor_sum_180))
    return (
        cor_center_of_rotation,
        cor_nx,
        cor_ny,
        cor_section_rows,
        cor_sum_0,
        cor_sum_180,
        detector_offset_us,
        profile_0,
        spectra_array,
    )


@app.cell
def _(cor_center_of_rotation, cor_nx, cor_ny, get_pre_proc_started, mo):
    """Crop and COR controls — separate cell so they stay reactive without re-loading images."""
    mo.stop(not get_pre_proc_started())
    _nx = max(1, cor_nx)
    _ny = max(1, cor_ny)
    _cor = cor_center_of_rotation if cor_center_of_rotation > 0 else _nx / 2.0
    crop_panel_height_px = 640
    _slice_cap = min(100, _ny)

    cor_crop_lr_w = mo.ui.range_slider(
        start=0,
        stop=_nx,
        step=1,
        value=[0, _nx],
        label="Crop left / right (px)",
        show_value=True,
        full_width=True,
    )

    def _position_value_for_top(_top_index):
        return max(0, min(_ny - 1, _ny - 1 - _top_index))

    cor_crop_region_enabled_1 = mo.ui.checkbox(value=True, label="Use")
    cor_crop_region_position_w_1 = mo.ui.slider(
        start=0,
        stop=max(0, _ny - 1),
        step=1,
        value=_position_value_for_top(0),
        label="Position",
        show_value=True,
        orientation="vertical",
    )
    cor_crop_region_size_w_1 = mo.ui.slider(
        start=1,
        stop=_slice_cap,
        step=1,
        value=_slice_cap,
        label="Nbr of slices",
        show_value=True,
        orientation="vertical",
    )

    _region_2_start = min(_slice_cap, max(0, _ny - 1))
    cor_crop_region_enabled_2 = mo.ui.checkbox(value=False, label="Use")
    cor_crop_region_position_w_2 = mo.ui.slider(
        start=0,
        stop=max(0, _ny - 1),
        step=1,
        value=_position_value_for_top(_region_2_start),
        label="Position",
        show_value=True,
        orientation="vertical",
    )
    cor_crop_region_size_w_2 = mo.ui.slider(
        start=1,
        stop=_slice_cap,
        step=1,
        value=_slice_cap,
        label="Nbr of slices",
        show_value=True,
        orientation="vertical",
    )

    _region_3_start = min(_slice_cap * 2, max(0, _ny - 1))
    cor_crop_region_enabled_3 = mo.ui.checkbox(value=False, label="Use")
    cor_crop_region_position_w_3 = mo.ui.slider(
        start=0,
        stop=max(0, _ny - 1),
        step=1,
        value=_position_value_for_top(_region_3_start),
        label="Position",
        show_value=True,
        orientation="vertical",
    )
    cor_crop_region_size_w_3 = mo.ui.slider(
        start=1,
        stop=_slice_cap,
        step=1,
        value=_slice_cap,
        label="Nbr of slices",
        show_value=True,
        orientation="vertical",
    )

    def _region_control(_label, _checkbox, _position_slider, _size_slider, _accent):
        return mo.vstack(
            [
                mo.hstack(
                    [
                        _checkbox,
                        mo.md(f"<span style='font-weight: 600; color: {_accent};'>{_label}</span>"),
                    ],
                    align="center",
                    gap=0.2,
                ),
                mo.hstack(
                    [
                        _position_slider.style(
                            {
                                "height": "240px",
                                "min-height": "240px",
                                "width": "88px",
                            }
                        ),
                        _size_slider.style(
                            {
                                "height": "240px",
                                "min-height": "240px",
                                "width": "88px",
                            }
                        ),
                    ],
                    align="start",
                    gap=0.1,
                ),
            ],
            gap=0.25,
        ).style(
            {
                "width": "fit-content",
                "display": "inline-flex",
            }
        )

    cor_crop_regions_view = mo.vstack(
        [
            mo.md("<span style='font-size: 0.9rem; font-weight: 600; color: #cbd5e1;'>Slice regions (max 100 each)</span>"),
            mo.hstack(
                [
                    _region_control("Region 1", cor_crop_region_enabled_1, cor_crop_region_position_w_1, cor_crop_region_size_w_1, "#22c55e"),
                    _region_control("Region 2", cor_crop_region_enabled_2, cor_crop_region_position_w_2, cor_crop_region_size_w_2, "#f59e0b"),
                    _region_control("Region 3", cor_crop_region_enabled_3, cor_crop_region_position_w_3, cor_crop_region_size_w_3, "#ef4444"),
                ],
                align="start",
                gap=0.45,
            ),
        ],
        gap=0.5,
    )

    cor_adjust_w = mo.ui.slider(
        start=max(0.0, _cor - 100.0),
        stop=min(float(_nx), _cor + 100.0),
        step=0.5,
        value=_cor,
        label=f"Center of rotation \u2014 auto: {_cor:.1f} px",
        show_value=True,
        full_width=True,
    )
    return (
        cor_adjust_w,
        cor_crop_lr_w,
        cor_crop_region_enabled_1,
        cor_crop_region_enabled_2,
        cor_crop_region_enabled_3,
        cor_crop_region_position_w_1,
        cor_crop_region_position_w_2,
        cor_crop_region_position_w_3,
        cor_crop_region_size_w_1,
        cor_crop_region_size_w_2,
        cor_crop_region_size_w_3,
        cor_crop_regions_view,
        crop_panel_height_px,
    )


@app.cell
def _(
    cor_adjust_w,
    cor_crop_lr_w,
    cor_crop_region_enabled_1,
    cor_crop_region_enabled_2,
    cor_crop_region_enabled_3,
    cor_crop_region_position_w_1,
    cor_crop_region_position_w_2,
    cor_crop_region_position_w_3,
    cor_crop_region_size_w_1,
    cor_crop_region_size_w_2,
    cor_crop_region_size_w_3,
    cor_crop_regions_view,
    cor_nx,
    cor_ny,
    cor_section_rows,
    cor_sum_0,
    cor_sum_180,
    crop_panel_height_px,
    get_pre_proc_started,
    mo,
    np,
):
    """Render the Crop & Center of rotation section. Re-runs on every slider change."""
    mo.stop(not get_pre_proc_started())
    import plotly.graph_objects as _go

    if cor_sum_0 is None or cor_sum_180 is None or cor_nx == 0:
        _plot_element = mo.md("")
        _selection_note = None
    else:
        _combined = cor_sum_0 + cor_sum_180
        _x0, _x1 = int(cor_crop_lr_w.value[0]), int(cor_crop_lr_w.value[1])
        _slice_cap = min(100, cor_ny)

        def _normalize_region(_position_value, _size_value):
            _size = max(1, min(int(_size_value), _slice_cap))
            _top = max(0, min(cor_ny - 1, cor_ny - 1 - int(_position_value)))
            _start = max(0, min(_top, max(0, cor_ny - _size)))
            _stop = min(cor_ny, _start + _size)
            if _stop <= _start:
                _stop = min(cor_ny, _start + 1)
            return _start, _stop

        _region_widgets = [
            ("#22c55e", "Region 1", cor_crop_region_enabled_1, cor_crop_region_position_w_1, cor_crop_region_size_w_1),
            ("#f59e0b", "Region 2", cor_crop_region_enabled_2, cor_crop_region_position_w_2, cor_crop_region_size_w_2),
            ("#ef4444", "Region 3", cor_crop_region_enabled_3, cor_crop_region_position_w_3, cor_crop_region_size_w_3),
        ]
        _active_regions = [
            (_color, _label, *_normalize_region(_position_slider.value, _size_slider.value))
            for _color, _label, _enabled, _position_slider, _size_slider in _region_widgets
            if _enabled.value
        ]
        _selection_note = None
        if not _active_regions:
            _start, _stop = _normalize_region(cor_crop_region_position_w_1.value, cor_crop_region_size_w_1.value)
            _active_regions = [("#22c55e", "Region 1", _start, _stop)]
            _selection_note = mo.callout(
                mo.md("At least one slice region must be selected. Showing Region 1."),
                kind="warn",
            )

        _cropped = _combined[:, _x0:_x1]

        if _cropped.size == 0:
            _plot_element = mo.callout(mo.md("Crop region is empty — adjust the sliders."), kind="warn")
        else:
            _cropped_ny, _cropped_nx = _cropped.shape
            _adjusted_cor = float(cor_adjust_w.value) - _x0
            _z_lo, _z_hi = np.percentile(_cropped, [2, 98])

            _fig = _go.Figure(data=_go.Heatmap(
                z=_cropped,
                colorscale="Viridis",
                showscale=True,
                zmin=_z_lo,
                zmax=_z_hi,
            ))
            _fig.add_trace(_go.Scatter(
                x=[_adjusted_cor, _adjusted_cor],
                y=[0, _cropped_ny - 1],
                mode="lines",
                line=dict(color="#3b82f6", width=2, dash="dash"),
                name=f"Center of rotation: {float(cor_adjust_w.value):.1f} px",
            ))
            for _color, _label, _y0, _y1 in _active_regions:
                _y_stop = max(_y0, _y1 - 1)
                _fig.add_hrect(
                    y0=_y0,
                    y1=_y_stop,
                    fillcolor=_color,
                    opacity=0.2,
                    line_width=0,
                    annotation_text=f"{_label}: {_y0}-{_y1}",
                    annotation_position="top left",
                )
                _fig.add_trace(_go.Scatter(
                    x=[0, _cropped_nx - 1, _cropped_nx - 1, 0, 0],
                    y=[_y0, _y0, _y_stop, _y_stop, _y0],
                    mode="lines",
                    line=dict(color=_color, width=1),
                    name=f"{_label}: {_y0}-{_y1}",
                    showlegend=True,
                ))
            _fig.update_layout(
                height=crop_panel_height_px,
                showlegend=True,
                legend=dict(
                    x=0.01, y=0.99,
                    xanchor="left", yanchor="top",
                    bgcolor="rgba(17,24,39,0.8)",
                    bordercolor="#334155",
                    borderwidth=1,
                    font=dict(color="#e5e7eb"),
                ),
                xaxis=dict(title="x (pixels)", color="#9ca3af", constrain="domain"),
                yaxis=dict(title="y (pixels)", color="#9ca3af", autorange="reversed", scaleanchor="x", scaleratio=1, constraintoward="top"),
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#e5e7eb"),
                margin=dict(l=60, r=20, t=30, b=60),
            )
            _plot_element = mo.ui.plotly(_fig)

    mo.vstack(
        [
            mo.md(
                "<div style='border-left: 4px solid #16a34a; padding: 4px 12px; margin-bottom: 4px;'>"
                "<span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; "
                "text-transform: uppercase; color: #16a34a;'>\U0001f3af Crop & Center of rotation</span></div>"
            ),
            *cor_section_rows,
            *([_selection_note] if _selection_note is not None else []),
            cor_crop_lr_w,
            _plot_element,
            cor_crop_regions_view,
            cor_adjust_w,
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
    return


@app.cell
def _(get_pre_proc_started, mo, profile_0):
    """TOF selection controls for up to five highlighted profile ranges."""
    mo.stop(not get_pre_proc_started())
    _profile_len = int(len(profile_0)) if profile_0 is not None else 1
    _slider_stop = max(1, _profile_len - 1)
    _default_ranges = [
        [0, _slider_stop],
        [0, _slider_stop],
        [0, _slider_stop],
        [0, _slider_stop],
        [0, _slider_stop],
    ]

    tof_range_enabled_1 = mo.ui.checkbox(value=False, label="")
    tof_range_slider_1 = mo.ui.range_slider(
        start=0,
        stop=_slider_stop,
        step=1,
        value=_default_ranges[0],
        label="Range 1",
        show_value=True,
        full_width=True,
    )
    tof_range_enabled_2 = mo.ui.checkbox(value=False, label="")
    tof_range_slider_2 = mo.ui.range_slider(
        start=0,
        stop=_slider_stop,
        step=1,
        value=_default_ranges[1],
        label="Range 2",
        show_value=True,
        full_width=True,
    )
    tof_range_enabled_3 = mo.ui.checkbox(value=False, label="")
    tof_range_slider_3 = mo.ui.range_slider(
        start=0,
        stop=_slider_stop,
        step=1,
        value=_default_ranges[2],
        label="Range 3",
        show_value=True,
        full_width=True,
    )
    tof_range_enabled_4 = mo.ui.checkbox(value=False, label="")
    tof_range_slider_4 = mo.ui.range_slider(
        start=0,
        stop=_slider_stop,
        step=1,
        value=_default_ranges[3],
        label="Range 4",
        show_value=True,
        full_width=True,
    )
    tof_range_enabled_5 = mo.ui.checkbox(value=False, label="")
    tof_range_slider_5 = mo.ui.range_slider(
        start=0,
        stop=_slider_stop,
        step=1,
        value=_default_ranges[4],
        label="Range 5",
        show_value=True,
        full_width=True,
    )
    return (
        tof_range_enabled_1,
        tof_range_enabled_2,
        tof_range_enabled_3,
        tof_range_enabled_4,
        tof_range_enabled_5,
        tof_range_slider_1,
        tof_range_slider_2,
        tof_range_slider_3,
        tof_range_slider_4,
        tof_range_slider_5,
    )


@app.cell
def _(
    detector_offset_us,
    get_pre_proc_started,
    mo,
    np,
    profile_0,
    spectra_array,
    tof_range_enabled_1,
    tof_range_enabled_2,
    tof_range_enabled_3,
    tof_range_enabled_4,
    tof_range_enabled_5,
    tof_range_slider_1,
    tof_range_slider_2,
    tof_range_slider_3,
    tof_range_slider_4,
    tof_range_slider_5,
    venus_source_detector_distance_m,
):
    """Render the TOF selection section with vertical profile overlays."""
    mo.stop(not get_pre_proc_started())
    import plotly.graph_objects as _go

    _rows = [
        ("#3b82f6", tof_range_enabled_1, tof_range_slider_1),
        ("#22c55e", tof_range_enabled_2, tof_range_slider_2),
        ("#f59e0b", tof_range_enabled_3, tof_range_slider_3),
        ("#ef4444", tof_range_enabled_4, tof_range_slider_4),
        ("#a855f7", tof_range_enabled_5, tof_range_slider_5),
    ]

    _x2 = None
    if profile_0 is None or len(profile_0) == 0:
        _plot = mo.callout(mo.md("No TOF profile available yet."), kind="warn")
    else:
        # *1e6 to convert from seconds to microseconds for better x-axis labeling. Only applies if spectra_array is available, otherwise we just use index values.
        _x = spectra_array*1e6 if spectra_array is not None else np.arange(len(profile_0))
        if spectra_array is not None:
            # convert tof axis to lambda using the formula: lambda = (h / m_n) * (tof / L), where h is Planck's constant, m_n is neutron mass, tof is time-of-flight in seconds, and L is source-to-detector distance in meters. We also apply a correction for the detector offset.
            h = 6.62607015e-34  # Planck's constant in J*s
            m_n = 1.67492749804e-27  # neutron mass in kg
            L = venus_source_detector_distance_m  # source-to-detector distance in meters
            tof_seconds = _x*1e-6 + detector_offset_us*1e-6  # convert microseconds back to seconds and apply detector offset correction
            lambda_values = (h / m_n) * (tof_seconds / L)  # calculate lambda in meters
            # convert to lambda in Angstroms for better readability
            _x2 = lambda_values*1e10

        _fig = _go.Figure()
        _fig.add_trace(
            _go.Scatter(
                x=_x,
                y=profile_0,
                mode="lines",
                line=dict(color="#e5e7eb", width=2),
                name="profile_0",
            )
        )
        if _x2 is not None:
            _fig.add_trace(
                _go.Scatter(
                    x=_x2,
                    y=profile_0,
                    mode="lines",
                    xaxis="x2",
                    yaxis="y",
                    line=dict(color="rgba(0,0,0,0)", width=0),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
        for _idx, (_color, _enabled, _slider) in enumerate(_rows, start=1):
            if not _enabled.value:
                continue
            _start, _stop = sorted((int(_slider.value[0]), int(_slider.value[1])))
            _x_start = float(_x[_start])
            _x_stop = float(_x[_stop])
            _fig.add_vrect(
                x0=_x_start,
                x1=_x_stop,
                fillcolor=_color,
                opacity=0.2,
                line_width=0,
                annotation_text=f"Range {_idx}",
                annotation_position="top left",
            )
            _fig.add_trace(
                _go.Scatter(
                    x=[_x_start, _x_start, _x_stop, _x_stop],
                    y=[float(min(profile_0)), float(max(profile_0)), float(max(profile_0)), float(min(profile_0))],
                    mode="lines",
                    line=dict(color=_color, width=1),
                    name=f"Range {_idx}: {_start}-{_stop}",
                    showlegend=True,
                )
            )

        _layout = dict(
            height=420,
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(17,24,39,0.8)",
                bordercolor="#334155",
                borderwidth=1,
                font=dict(color="#e5e7eb"),
            ),
            xaxis=dict(title="TOF (μs)", color="#9ca3af"),
            yaxis=dict(title="Total counts of full 0° projection", color="#9ca3af"),
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#e5e7eb"),
            margin=dict(l=60, r=20, t=60, b=60),
        )

        if _x2 is not None:
            _layout["xaxis2"] = dict(
                title="Wavelength (Å)",
                color="#9ca3af",
                overlaying="x",
                side="top",
                range=[float(np.min(_x2)), float(np.max(_x2))],
                showgrid=False,
                zeroline=False,
            )

        _fig.update_layout(**_layout)
        _plot = mo.ui.plotly(_fig)

    _controls = [
        mo.hstack([_enabled, _slider], align="center", gap=0.75)
        for _, _enabled, _slider in _rows
    ]

    mo.vstack(
        [
            mo.md(
                "<div style='border-left: 4px solid #0ea5e9; padding: 4px 12px; margin-bottom: 4px;'>"
                "<span style='font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em; "
                "text-transform: uppercase; color: #0ea5e9;'>⏱ TOF selection</span></div>"
            ),
            _plot,
            *_controls,
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
    return


if __name__ == "__main__":
    app.run()
