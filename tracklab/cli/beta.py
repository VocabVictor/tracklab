"""Beta versions of wandb CLI commands.

These commands are experimental and may change or be removed in future versions.
"""

from __future__ import annotations

import pathlib
import sys

import click

import tracklab
from tracklab.errors import WandbCoreNotAvailableError
from tracklab.util import get_core_path


@click.group()
def beta():
    """Beta versions of wandb CLI commands. Requires wandb-core."""
    # this is the future that requires wandb-core!
    import tracklab.env

    # Analytics configured for beta context

    try:
        get_core_path()
    except WandbCoreNotAvailableError as e:
        # Beta command exception logged locally
        click.secho(
            (e),
            fg="red",
            err=True,
        )


