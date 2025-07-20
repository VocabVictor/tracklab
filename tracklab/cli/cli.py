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
# APIs removed - using local-only mode
from tracklab.errors.links import url_registry
from tracklab.sdk import setup
from tracklab.config_manager import config_manager
from tracklab.sdk.lib import filesystem

# from .beta import beta  # Temporarily disabled - missing get_core_path
from .ui import ui

# Send cli logs to tracklab/debug-cli.<username>.log by default and fallback to a temp dir.
_tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
if not os.path.exists(_tracklab_dir):
    os.makedirs(_tracklab_dir, exist_ok=True)

try:
    _username = getpass.getuser()
except KeyError:
    # chroot jails or docker containers. Return user id in these cases.
    _username = str(os.getuid())

_tracklab_log_path = os.path.join(_tracklab_dir, f"debug-cli.{_username}.log")

logging.basicConfig(
    filename=_tracklab_log_path,
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
    """Get a reference to the internal api with cling settings (local-only mode)."""
    global _api
    if reset:
        _api = None
        tracklab.teardown()
    if _api is None:
        # Local-only mode - use config_manager instead of API
        from tracklab.config_manager import config_manager
        _api = config_manager
    return _api


def prompt_for_project(ctx, entity):
    """Ask the user for a project (simplified for local-only mode)."""
    # In local mode, we use research/experiment names instead of projects
    research_name = click.prompt("Enter a research/paper name", default="default-research")
    return research_name


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


# Projects command disabled for local-only mode
# @cli.command(context_settings=CONTEXT, help="List projects", hidden=True)
# @click.option(
#     "--entity",
#     "-e",
#     default=None,
#     envvar=env.ENTITY,
#     help="The entity to scope the listing to.",
# )
# @display_error
# def projects(entity, display=True):
#     api = _get_cling_api()
#     projects = api.list_projects(entity=entity)
#     if len(projects) == 0:
#         message = f"No projects found for {entity}"
#     else:
#         message = f'Latest projects for "{entity}"'
#     if display:
#         click.echo(click.style(message, bold=True))
#         for project in projects:
#             click.echo(
#                 "".join(
#                     (
#                         click.style(project["name"], fg="blue", bold=True),
#                         " - ",
#                         str(project["description"] or "").split("\n")[0],
#                     )
#                 )
#             )
#     return projects




@cli.command(
    context_settings=CONTEXT, help="Configure a directory with TrackLab"
)
@click.option("--project", "-p", help="The project to use.")
@click.option("--entity", "-e", help="The entity to scope the project to.")
@click.option("--reset", is_flag=True, help="Reset settings")
@click.option(
    "--mode",
    "-m",
    help=' Can be "online", "offline" or "disabled". Defaults to offline.',
)
@click.pass_context
@display_error
def init(ctx, project, entity, reset, mode):
    # Simplified init for local-only TrackLab
    from tracklab.config_manager import config_manager
    
    # non-interactive init
    if reset or project or entity or mode:
        if reset:
            config_manager.delete("entity")
            config_manager.delete("project")
            config_manager.delete("mode")
        if entity:
            config_manager.set("entity", entity)
        if project:
            config_manager.set("project", project)
        if mode:
            config_manager.set("mode", mode or "offline")
        return

    tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
    if os.path.isdir(tracklab_dir) and os.path.exists(
        os.path.join(tracklab_dir, "settings")
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
            click.style("Let's setup this directory for TrackLab!", fg="green", bold=True)
        )
    
    # TrackLab runs in local-only mode, no complex authentication needed
    if not entity:
        entity = click.prompt("What username or team should we use?", default="local")
    
    if not project:
        project = click.prompt("What project should we use?", default="my-project")
    
    if not mode:
        mode = "offline"  # Default to offline for local-only mode
    
    config_manager.set("entity", entity)
    config_manager.set("project", project)
    config_manager.set("mode", mode)

    tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
    filesystem.mkdir_exists_ok(tracklab_dir)
    with open(os.path.join(tracklab_dir, ".gitignore"), "w") as file:
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




# Pull command disabled for local-only mode
# @cli.command(context_settings=CONTEXT, help="Pull files from Weights & Biases")
# @click.argument("run", envvar=env.RUN_ID)
# @click.option(
#     "--project", "-p", envvar=env.PROJECT, help="The project you want to download."
# )
# @click.option(
#     "--entity",
#     "-e",
#     default="models",
#     envvar=env.ENTITY,
#     help="The entity to scope the listing to.",
# )
# @display_error
# def pull(run, project, entity):
#     api = InternalApi()
#     project, run = api.parse_slug(run, project=project)
#     urls = api.download_urls(project, run=run, entity=entity)
#     if len(urls) == 0:
#         raise ClickException("Run has no files")
#     click.echo(f"Downloading: {click.style(project, bold=True)}/{run}")
# 
#     for name in urls:
#         if api.file_current(name, urls[name]["md5"]):
#             click.echo(f"File {name} is up to date")
#         else:
#             length, response = api.download_file(urls[name]["url"])
#             # TODO: I had to add this because some versions in CI broke click.progressbar
#             sys.stdout.write(f"File {name}\r")
#             dirname = os.path.dirname(name)
#             if dirname != "":
#                 filesystem.mkdir_exists_ok(dirname)
#             with click.progressbar(
#                 length=length,
#                 label=f"File {name}",
#                 fill_char=click.style("&", fg="green"),
#             ) as bar:
#                 with open(name, "wb") as f:
#                     for data in response.iter_content(chunk_size=4096):
#                         f.write(data)
#                         bar.update(len(data))


# Restore command disabled for local-only mode
# @cli.command(
#     context_settings=CONTEXT, help="Restore code and config state for a run"
# )
# @click.pass_context
# @click.argument("run", envvar=env.RUN_ID)
# @click.option("--no-git", is_flag=True, default=False, help="Don't restore git state")
# @click.option(
#     "--branch/--no-branch",
#     default=True,
#     help="Whether to create a branch or checkout detached",
# )
# @click.option(
#     "--project", "-p", envvar=env.PROJECT, help="The project you wish to upload to."
# )
# @click.option(
#     "--entity", "-e", envvar=env.ENTITY, help="The entity to scope the listing to."
# )
# @display_error
# def restore(ctx, run, no_git, branch, project, entity):
#     # from tracklab.old.core import tracklab_dir
#     tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")

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
                tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
                patch_path = os.path.join(tracklab_dir, "diff.patch")
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

    tracklab_dir = env.get_dir() or os.path.expanduser("~/.tracklab")
    filesystem.mkdir_exists_ok(tracklab_dir)
    config_path = os.path.join(tracklab_dir, "config.yaml")
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

#     tracklab.termlog(f"Restored config variables to {config_path}")
# 
#     return commit, json_config, patch_content, repo, metadata




@cli.command("status", help="Show configuration settings")
@click.option(
    "--settings/--no-settings", help="Show the current settings", default=True
)
def status(settings):
    config_manager = _get_cling_api()
    if settings:
        click.echo(click.style("Current Settings", bold=True))
        # Get all settings from config_manager
        all_settings = {}
        for key in ["entity", "project", "mode", "base_url"]:
            value = config_manager.get(key)
            if value:
                all_settings[key] = value
        click.echo(
            json.dumps(all_settings, sort_keys=True, indent=2, separators=(",", ": "))
        )




# Verify command disabled for local-only mode
# @cli.command(context_settings=CONTEXT, help="Verify your local instance")
# @click.option("--host", default=None, help="Test a specific instance of W&B")
# def verify(host):
#     # TODO: (kdg) Build this all into a WandbVerify object, and clean this up.
#     os.environ["TRACKLAB_SILENT"] = "true"
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
    
#     if not (
#         check_artifacts_success
#         and check_run_success
#         and large_post_success
#         and url_success
# 
#     ):
#         sys.exit(1)


# cli.add_command(beta)  # Temporarily disabled - missing get_core_path
cli.add_command(ui)


if __name__ == "__main__":
    cli()
