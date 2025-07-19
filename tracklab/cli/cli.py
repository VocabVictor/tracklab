import asyncio
import configparser
import datetime
import getpass
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import traceback
from functools import wraps
from typing import Any, Dict, Optional

import click
import yaml
from click.exceptions import ClickException

import tracklab
import tracklab.env
import tracklab.errors
import tracklab.sdk.verify.verify as wandb_verify
from tracklab import Config, Error, env, util, tracklab_sdk
from tracklab.apis import InternalApi, PublicApi
from tracklab.errors.links import url_registry
from tracklab.sdk import setup
from tracklab.sdk.internal.internal_api import Api as SDKInternalApi
from tracklab.sdk.lib import filesystem

from .beta import beta
from .ui import ui

# Send cli logs to tracklab/debug-cli.<username>.log by default and fallback to a temp dir.
_wandb_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
if not os.path.exists(_wandb_dir):
    os.makedirs(_wandb_dir, exist_ok=True)

try:
    _username = getpass.getuser()
except KeyError:
    # chroot jails or docker containers. Return user id in these cases.
    _username = str(os.getuid())

_wandb_log_path = os.path.join(_wandb_dir, f"debug-cli.{_username}.log")

logging.basicConfig(
    filename=_wandb_log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wandb")

_HAS_DOCKER = bool(shutil.which("docker"))
_HAS_NVIDIA_DOCKER = bool(shutil.which("nvidia-docker"))

# Click Contexts
CONTEXT = {"default_map": {}}
RUN_CONTEXT = {
    "default_map": {},
    "allow_extra_args": True,
    "ignore_unknown_options": True,
}


def cli_unsupported(argument):
    tracklab.termerror(f"Unsupported argument `{argument}`")
    sys.exit(1)


class ClickWandbException(ClickException):
    def format_message(self):
        orig_type = f"{self.orig_type.__module__}.{self.orig_type.__name__}"
        if issubclass(self.orig_type, Error):
            return click.style(str(self.message), fg="red")
        else:
            return (
                f"An Exception was raised, see {_wandb_log_path} for full"
                " traceback.\n"
                f"{orig_type}: {self.message}"
            )


def display_error(func):
    """Function decorator for catching common errors and re-raising as tracklab.Error."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except tracklab.Error as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            logger.exception("".join(lines))
            tracklab.termerror(f"Find detailed error logs at: {_wandb_log_path}")
            click_exc = ClickWandbException(e)
            click_exc.orig_type = exc_type
            raise click_exc.with_traceback(sys.exc_info()[2])

    return wrapper


_api = None  # caching api instance allows patching from unit tests


def _get_cling_api(reset=None):
    """Get a reference to the internal api with cling settings."""
    global _api
    if reset:
        _api = None
        tracklab.teardown()
    if _api is None:
        # only override the necessary setting
        setup.singleton().settings.x_cli_only_mode = True
        _api = InternalApi()
    return _api


def prompt_for_project(ctx, entity):
    """Ask the user for a project, creating one if necessary."""
    result = ctx.invoke(projects, entity=entity, display=False)
    api = _get_cling_api()
    try:
        if len(result) == 0:
            project = click.prompt("Enter a name for your first project")
            project = api.upsert_project(project, entity=entity)["name"]
        else:
            project_names = [project["name"] for project in result] + ["Create New"]
            tracklab.termlog("Which project should we use?")
            result = util.prompt_choices(project_names)
            if result:
                project = result
            else:
                project = "Create New"
            # TODO: check with the server if the project exists
            if project == "Create New":
                project = click.prompt(
                    "Enter a name for your new project", value_proc=api.format_project
                )
                project = api.upsert_project(project, entity=entity)["name"]

    except tracklab.errors.CommError as e:
        raise ClickException(str(e))

    return project


class RunGroup(click.Group):
    @display_error
    def get_command(self, ctx, cmd_name):
        # TODO: check if cmd_name is a file in the current dir and not require `run`?
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        return None


@click.command(cls=RunGroup, invoke_without_command=True)
@click.version_option(version=tracklab.__version__)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(context_settings=CONTEXT, help="List projects", hidden=True)
@click.option(
    "--entity",
    "-e",
    default=None,
    envvar=env.ENTITY,
    help="The entity to scope the listing to.",
)
@display_error
def projects(entity, display=True):
    api = _get_cling_api()
    projects = api.list_projects(entity=entity)
    if len(projects) == 0:
        message = f"No projects found for {entity}"
    else:
        message = f'Latest projects for "{entity}"'
    if display:
        click.echo(click.style(message, bold=True))
        for project in projects:
            click.echo(
                "".join(
                    (
                        click.style(project["name"], fg="blue", bold=True),
                        " - ",
                        str(project["description"] or "").split("\n")[0],
                    )
                )
            )
    return projects




@cli.command(
    context_settings=CONTEXT, help="Configure a directory with Weights & Biases"
)
@click.option("--project", "-p", help="The project to use.")
@click.option("--entity", "-e", help="The entity to scope the project to.")
@click.option("--reset", is_flag=True, help="Reset settings")
@click.option(
    "--mode",
    "-m",
    help=' Can be "online", "offline" or "disabled". Defaults to online.',
)
@click.pass_context
@display_error
def init(ctx, project, entity, reset, mode):
    from tracklab.old.core import __stage_dir__, _set_stage_dir, wandb_dir

    if __stage_dir__ is None:
        _set_stage_dir("wandb")

    # non-interactive init
    if reset or project or entity or mode:
        api = InternalApi()
        if reset:
            api.clear_setting("entity", persist=True)
            api.clear_setting("project", persist=True)
            api.clear_setting("mode", persist=True)
        if entity:
            api.set_setting("entity", entity, persist=True)
        if project:
            api.set_setting("project", project, persist=True)
        if mode:
            api.set_setting("mode", mode, persist=True)
        return

    if os.path.isdir(wandb_dir()) and os.path.exists(
        os.path.join(wandb_dir(), "settings")
    ):
        click.confirm(
            click.style(
                "This directory has been configured previously, should we re-configure it?",
                bold=True,
            ),
            abort=True,
        )
    else:
        click.echo(
            click.style("Let's setup this directory for W&B!", fg="green", bold=True)
        )
    api = _get_cling_api()
    # TrackLab runs in local-only mode, no login required

    viewer = api.viewer()

    # Viewer can be `None` in case your API information became invalid, or
    # in testing if you switch hosts.
    if not viewer:
        click.echo(
            click.style(
                "Your login information seems to be invalid: can you log in again please?",
                fg="red",
                bold=True,
            )
        )
        # TrackLab runs in local-only mode, no login required
        pass

    # This shouldn't happen.
    viewer = api.viewer()
    if not viewer:
        click.echo(
            click.style(
                "We're sorry, there was a problem logging you in. "
                "Please send us a note at support@tracklab.com and tell us how this happened.",
                fg="red",
                bold=True,
            )
        )
        sys.exit(1)

    # At this point we should be logged in successfully.
    if len(viewer["teams"]["edges"]) > 1:
        team_names = [e["node"]["name"] for e in viewer["teams"]["edges"]] + [
            "Manual entry"
        ]
        tracklab.termlog(
            "Which team should we use?",
        )
        result = util.prompt_choices(team_names)
        # result can be empty on click
        if result:
            entity = result
        else:
            entity = "Manual Entry"
        if entity == "Manual Entry":
            entity = click.prompt("Enter the name of the team you want to use")
    else:
        entity = viewer.get("entity") or click.prompt(
            "What username or team should we use?"
        )

    # TODO: this error handling sucks and the output isn't pretty
    try:
        project = prompt_for_project(ctx, entity)
    except ClickWandbException:
        raise ClickException(f"Could not find team: {entity}")

    api.set_setting("entity", entity, persist=True)
    api.set_setting("project", project, persist=True)
    api.set_setting("base_url", api.settings().get("base_url"), persist=True)

    filesystem.mkdir_exists_ok(wandb_dir())
    with open(os.path.join(wandb_dir(), ".gitignore"), "w") as file:
        file.write("*\n!settings")

    click.echo(
        click.style("This directory is configured!  Next, track a run:\n", fg="green")
        + textwrap.dedent(
            """\
        * In your training script:
            {code1}
            {code2}
        * then `{run}`.
        """
        ).format(
            code1=click.style("import tracklab", bold=True),
            code2=click.style(f'tracklab.init(project="{project}")', bold=True),
            run=click.style("python <train.py>", bold=True),
        )
    )



@cli.command(
    context_settings=CONTEXT,
    help="Initialize a hyperparameter sweep. Search for hyperparameters that optimizes a cost function of a machine learning model by testing various combinations.",
)
@click.option(
    "--project",
    "-p",
    default=None,
    help="""The name of the project where W&B runs created from the sweep are sent to. If the project is not specified, the run is sent to a project labeled Uncategorized.""",
)
@click.option(
    "--entity",
    "-e",
    default=None,
    help="""The username or team name where you want to send W&B runs created by the sweep to. Ensure that the entity you specify already exists. If you don't specify an entity, the run will be sent to your default entity, which is usually your username.""",
)
@click.option("--controller", is_flag=True, default=False, help="Run local controller")
@click.option("--verbose", is_flag=True, default=False, help="Display verbose output")
@click.option(
    "--name",
    default=None,
    help="The name of the sweep. The sweep ID is used if no name is specified.",
)
@click.option("--program", default=None, help="Set sweep program")
@click.option("--settings", default=None, help="Set sweep settings", hidden=True)
@click.option("--update", default=None, help="Update pending sweep")
@click.option(
    "--stop",
    is_flag=True,
    default=False,
    help="Finish a sweep to stop running new runs and let currently running runs finish.",
)
@click.option(
    "--cancel",
    is_flag=True,
    default=False,
    help="Cancel a sweep to kill all running runs and stop running new runs.",
)
@click.option(
    "--pause",
    is_flag=True,
    default=False,
    help="Pause a sweep to temporarily stop running new runs.",
)
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Resume a sweep to continue running new runs.",
)
@click.option(
    "--prior_run",
    "-R",
    "prior_runs",
    multiple=True,
    default=None,
    help="ID of an existing run to add to this sweep",
)
@click.argument("config_yaml_or_sweep_id")
@click.pass_context
@display_error
def sweep(
    ctx,
    project,
    entity,
    controller,
    verbose,
    name,
    program,
    settings,
    update,
    stop,
    cancel,
    pause,
    resume,
    prior_runs,
    config_yaml_or_sweep_id,
):
    state_args = "stop", "cancel", "pause", "resume"
    lcls = locals()
    is_state_change_command = sum(lcls[k] for k in state_args)
    if is_state_change_command > 1:
        raise Exception("Only one state flag (stop/cancel/pause/resume) is allowed.")
    elif is_state_change_command == 1:
        sweep_id = config_yaml_or_sweep_id
        api = _get_cling_api()
        # TrackLab runs in local-only mode, no authentication required
        if not sweep_id:
            tracklab.termerror("Sweep ID is required")
            return
        entity = parts.get("entity") or entity
        project = parts.get("project") or project
        sweep_id = parts.get("name") or sweep_id
        state = [s for s in state_args if lcls[s]][0]
        ings = {
            "stop": "Stopping",
            "cancel": "Cancelling",
            "pause": "Pausing",
            "resume": "Resuming",
        }
        tracklab.termlog(f"{ings[state]} sweep {entity}/{project}/{sweep_id}")
        getattr(api, f"{state}_sweep")(sweep_id, entity=entity, project=project)
        tracklab.termlog("Done.")
        return
    else:
        config_yaml = config_yaml_or_sweep_id

    def _parse_settings(settings):
        """Parse settings from json or comma separated assignments."""
        ret = {}
        if settings.find("=") > 0:
            for item in settings.split(","):
                kv = item.split("=")
                if len(kv) != 2:
                    tracklab.termwarn(
                        "Unable to parse sweep settings key value pair", repeat=False
                    )
                ret.update(dict([kv]))
            return ret
        tracklab.termwarn("Unable to parse settings parameter", repeat=False)
        return ret

    api = _get_cling_api()
    # TrackLab runs in local-only mode, no authentication required

    sweep_obj_id = None
    if update:
        if not update:
            tracklab.termerror("Update ID is required")
            return
        entity = parts.get("entity") or entity
        project = parts.get("project") or project
        sweep_id = parts.get("name") or update

        has_project = (project or api.settings("project")) is not None
        has_entity = (entity or api.settings("entity")) is not None

        termerror_msg = (
            "Sweep lookup requires a valid %s, and none was specified. \n"
            "Either set a default %s in wandb/settings, or, if invoking \n`wandb sweep` "
            "from the command line, specify the full sweep path via: \n\n"
            "    wandb sweep {username}/{projectname}/{sweepid}\n\n"
        )

        if not has_entity:
            tracklab.termerror(termerror_msg % (("entity",) * 2))
            return

        if not has_project:
            tracklab.termerror(termerror_msg % (("project",) * 2))
            return

        found = api.sweep(sweep_id, "{}", entity=entity, project=project)
        if not found:
            tracklab.termerror(f"Could not find sweep {entity}/{project}/{sweep_id}")
            return
        sweep_obj_id = found["id"]

    action = "Updating" if sweep_obj_id else "Creating"
    tracklab.termlog(f"{action} sweep from: {config_yaml}")
    # Load sweep config directly
    with open(config_yaml, 'r') as f:
        config = yaml.safe_load(f)

    # Set or override parameters
    if name:
        config["name"] = name
    if program:
        config["program"] = program
    if settings:
        settings = _parse_settings(settings)
        if settings:
            config.setdefault("settings", {})
            config["settings"].update(settings)
    if controller:
        config.setdefault("controller", {})
        config["controller"]["type"] = "local"

    is_local = config.get("controller", {}).get("type") == "local"
    if is_local:
        from tracklab import controller as wandb_controller

        tuner = wandb_controller()
        err = tuner._validate(config)
        if err:
            tracklab.termerror(f"Error in sweep file: {err}")
            return

    env = os.environ
    entity = (
        entity
        or env.get("TRACKLAB_ENTITY")
        or config.get("entity")
        or api.settings("entity")
    )
    project = (
        project
        or env.get("TRACKLAB_PROJECT")
        or config.get("project")
        or api.settings("project")
        or util.auto_project_name(config.get("program"))
    )

    sweep_id, warnings = api.upsert_sweep(
        config,
        project=project,
        entity=entity,
        obj_id=sweep_obj_id,
        prior_runs=prior_runs,
    )
    # Handle warnings
    if warnings:
        for warning in warnings:
            tracklab.termwarn(f"Sweep config warning: {warning}")

    # Log nicely formatted sweep information
    styled_id = click.style(sweep_id, fg="yellow")
    tracklab.termlog(f"{action} sweep with ID: {styled_id}")

    sweep_url = tracklab_sdk.tracklab_sweep._get_sweep_url(api, sweep_id)
    if sweep_url:
        styled_url = click.style(sweep_url, underline=True, fg="blue")
        tracklab.termlog(f"View sweep at: {styled_url}")

    # re-probe entity and project if it was auto-detected by upsert_sweep
    entity = entity or env.get("TRACKLAB_ENTITY")
    project = project or env.get("TRACKLAB_PROJECT")

    if entity and project:
        sweep_path = f"{entity}/{project}/{sweep_id}"
    elif project:
        sweep_path = f"{project}/{sweep_id}"
    else:
        sweep_path = sweep_id

    if sweep_path.find(" ") >= 0:
        sweep_path = f"{sweep_path!r}"

    styled_path = click.style(f"wandb agent {sweep_path}", fg="yellow")
    tracklab.termlog(f"Run sweep agent with: {styled_path}")
    if controller:
        tracklab.termlog("Starting wandb controller...")
        from tracklab import controller as wandb_controller

        tuner = wandb_controller(sweep_id)
        tuner.run(verbose=verbose)


@cli.command(
    context_settings=CONTEXT,
    no_args_is_help=True,
    help="Run a W&B launch sweep (Experimental).",
)
@click.option(
    "--queue",
    "-q",
    default=None,
    help="The name of a queue to push the sweep to",
)
@click.option(
    "--project",
    "-p",
    default=None,
    help="Name of the project which the agent will watch. "
    "If passed in, will override the project value passed in using a config file",
)
@click.option(
    "--entity",
    "-e",
    default=None,
    help="The entity to use. Defaults to current logged-in user",
)
@click.option(
    "--resume_id",
    "-r",
    default=None,
    help="Resume a launch sweep by passing an 8-char sweep id. Queue required",
)
@click.option(
    "--prior_run",
    "-R",
    "prior_runs",
    multiple=True,
    default=None,
    help="ID of an existing run to add to this sweep",
)
@click.argument("config", required=False, type=click.Path(exists=True))
@click.pass_context
@display_error




@cli.command(context_settings=CONTEXT, help="Run the W&B local sweep controller")
@click.option("--verbose", is_flag=True, default=False, help="Display verbose output")
@click.argument("sweep_id")
@display_error
def controller(verbose, sweep_id):
    click.echo("Starting wandb controller...")
    from tracklab import controller as wandb_controller

    tuner = wandb_controller(sweep_id)
    tuner.run(verbose=verbose)










@cli.command(context_settings=CONTEXT, help="Pull files from Weights & Biases")
@click.argument("run", envvar=env.RUN_ID)
@click.option(
    "--project", "-p", envvar=env.PROJECT, help="The project you want to download."
)
@click.option(
    "--entity",
    "-e",
    default="models",
    envvar=env.ENTITY,
    help="The entity to scope the listing to.",
)
@display_error
def pull(run, project, entity):
    api = InternalApi()
    project, run = api.parse_slug(run, project=project)
    urls = api.download_urls(project, run=run, entity=entity)
    if len(urls) == 0:
        raise ClickException("Run has no files")
    click.echo(f"Downloading: {click.style(project, bold=True)}/{run}")

    for name in urls:
        if api.file_current(name, urls[name]["md5"]):
            click.echo(f"File {name} is up to date")
        else:
            length, response = api.download_file(urls[name]["url"])
            # TODO: I had to add this because some versions in CI broke click.progressbar
            sys.stdout.write(f"File {name}\r")
            dirname = os.path.dirname(name)
            if dirname != "":
                filesystem.mkdir_exists_ok(dirname)
            with click.progressbar(
                length=length,
                label=f"File {name}",
                fill_char=click.style("&", fg="green"),
            ) as bar:
                with open(name, "wb") as f:
                    for data in response.iter_content(chunk_size=4096):
                        f.write(data)
                        bar.update(len(data))


@cli.command(
    context_settings=CONTEXT, help="Restore code and config state for a run"
)
@click.pass_context
@click.argument("run", envvar=env.RUN_ID)
@click.option("--no-git", is_flag=True, default=False, help="Don't restore git state")
@click.option(
    "--branch/--no-branch",
    default=True,
    help="Whether to create a branch or checkout detached",
)
@click.option(
    "--project", "-p", envvar=env.PROJECT, help="The project you wish to upload to."
)
@click.option(
    "--entity", "-e", envvar=env.ENTITY, help="The entity to scope the listing to."
)
@display_error
def restore(ctx, run, no_git, branch, project, entity):
    from tracklab.old.core import tracklab_dir

    api = _get_cling_api()
    if ":" in run:
        if "/" in run:
            entity, rest = run.split("/", 1)
        else:
            rest = run
        project, run = rest.split(":", 1)
    elif run.count("/") > 1:
        entity, run = run.split("/", 1)

    project, run = api.parse_slug(run, project=project)
    commit, json_config, patch_content, metadata = api.run_config(
        project, run=run, entity=entity
    )
    repo = metadata.get("git", {}).get("repo")
    image = metadata.get("docker")
    restore_message = f"""`wandb restore` needs to be run from the same git repository as the original run.
Run `git clone {repo}` and restore from there or pass the --no-git flag."""
    if no_git:
        commit = None
    elif not api.git.enabled:
        if repo:
            raise ClickException(restore_message)
        elif image:
            tracklab.termlog(
                "Original run has no git history.  Just restoring config and docker"
            )

    if commit and api.git.enabled:
        tracklab.termlog(f"Fetching origin and finding commit: {commit}")
        subprocess.check_call(["git", "fetch", "--all"])
        try:
            api.git.repo.commit(commit)
        except ValueError:
            tracklab.termlog(f"Couldn't find original commit: {commit}")
            commit = None
            files = api.download_urls(project, run=run, entity=entity)
            for filename in files:
                if filename.startswith("upstream_diff_") and filename.endswith(
                    ".patch"
                ):
                    commit = filename[len("upstream_diff_") : -len(".patch")]
                    try:
                        api.git.repo.commit(commit)
                    except ValueError:
                        commit = None
                    else:
                        break

            if commit:
                tracklab.termlog(f"Falling back to upstream commit: {commit}")
                patch_path, _ = api.download_write_file(files[filename])
            else:
                raise ClickException(restore_message)
        else:
            if patch_content:
                patch_path = os.path.join(wandb_dir(), "diff.patch")
                with open(patch_path, "w") as f:
                    f.write(patch_content)
            else:
                patch_path = None

        branch_name = f"wandb/{run}"
        if branch and branch_name not in api.git.repo.branches:
            api.git.repo.git.checkout(commit, b=branch_name)
            tracklab.termlog(f"Created branch {click.style(branch_name, bold=True)}")
        elif branch:
            tracklab.termlog(
                f"Using existing branch, run `git branch -D {branch_name}` from master for a clean checkout"
            )
            api.git.repo.git.checkout(branch_name)
        else:
            tracklab.termlog(f"Checking out {commit} in detached mode")
            api.git.repo.git.checkout(commit)

        if patch_path:
            # we apply the patch from the repository root so git doesn't exclude
            # things outside the current directory
            root = api.git.root
            patch_rel_path = os.path.relpath(patch_path, start=root)
            # --reject is necessary or else this fails any time a binary file
            # occurs in the diff
            exit_code = subprocess.call(
                ["git", "apply", "--reject", patch_rel_path], cwd=root
            )
            if exit_code == 0:
                tracklab.termlog("Applied patch")
            else:
                tracklab.termerror(
                    "Failed to apply patch, try un-staging any un-committed changes"
                )

    filesystem.mkdir_exists_ok(wandb_dir())
    config_path = os.path.join(wandb_dir(), "config.yaml")
    config = Config()
    for k, v in json_config.items():
        if k not in ("_wandb", "wandb_version"):
            config[k] = v
    s = b"wandb_version: 1"
    s += b"\n\n" + yaml.dump(
        config._as_dict(),
        Dumper=yaml.SafeDumper,
        default_flow_style=False,
        allow_unicode=True,
        encoding="utf-8",
    )
    s = s.decode("utf-8")
    with open(config_path, "w") as f:
        f.write(s)

    tracklab.termlog(f"Restored config variables to {config_path}")

    return commit, json_config, patch_content, repo, metadata




@cli.command("status", help="Show configuration settings")
@click.option(
    "--settings/--no-settings", help="Show the current settings", default=True
)
def status(settings):
    api = _get_cling_api()
    if settings:
        click.echo(click.style("Current Settings", bold=True))
        settings = api.settings()
        click.echo(
            json.dumps(settings, sort_keys=True, indent=2, separators=(",", ": "))
        )




@cli.command(context_settings=CONTEXT, help="Verify your local instance")
@click.option("--host", default=None, help="Test a specific instance of W&B")
def verify(host):
    # TODO: (kdg) Build this all into a WandbVerify object, and clean this up.
    os.environ["TRACKLAB_SILENT"] = "true"
    os.environ["TRACKLAB_PROJECT"] = "verify"
    api = _get_cling_api()
    reinit = False
    if host is None:
        host = api.settings("base_url")
        tracklab.termlog(f"Default host selected: {host}")
    elif host != api.settings("base_url"):
        reinit = True

    tmp_dir = tempfile.mkdtemp()
    tracklab.termlog(
        "Find detailed logs for this test at: {}".format(os.path.join(tmp_dir, "wandb"))
    )
    os.chdir(tmp_dir)
    os.environ["TRACKLAB_BASE_URL"] = host
    tracklab.login(host=host)
    if reinit:
        api = _get_cling_api(reset=True)
    if not wandb_verify.check_host(host):
        sys.exit(1)
    if not wandb_verify.check_logged_in(api, host):
        sys.exit(1)
    url_success, url = wandb_verify.check_graphql_put(api, host)
    large_post_success = wandb_verify.check_large_post()
    wandb_verify.check_secure_requests(
        api.settings("base_url"),
        "Checking requests to base url",
        "Connections are not made over https. SSL required for secure communications.",
    )
    if url:
        wandb_verify.check_secure_requests(
            url,
            "Checking requests made over signed URLs",
            "Signed URL requests not made over https. SSL is required for secure communications.",
        )
        wandb_verify.check_cors_configuration(url, host)
    wandb_verify.check_wandb_version(api)
    check_run_success = wandb_verify.check_run(api)
    check_artifacts_success = wandb_verify.check_artifacts()
    check_sweeps_success = wandb_verify.check_sweeps(api)
    if not (
        check_artifacts_success
        and check_run_success
        and large_post_success
        and url_success
        and check_sweeps_success
    ):
        sys.exit(1)


cli.add_command(beta)
cli.add_command(ui)


if __name__ == "__main__":
    cli()
