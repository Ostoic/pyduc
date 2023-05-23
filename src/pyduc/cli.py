from logging import getLogger
from pathlib import Path

import click
from stuom import Duration, Minutes

from pyduc.pyduc import create_pyduc_updater
from pyduc.util import CliDurationParam

log = getLogger(__file__)


@click.command()
@click.option(
    "-u",
    "--username",
    type=str,
    required=True,
    help="The hostname to update.",
)
@click.option(
    "-p",
    "--password",
    required=True,
    type=click.Path(exists=True, readable=True, resolve_path=True),
    help="The list of no-ip hostnames to update.",
)
@click.option(
    "-n",
    "--hosts",
    type=str,
    required=True,
    multiple=True,
    help="The list of no-ip hostnames to update.",
)
@click.option(
    "-c",
    "--check-delay",
    type=CliDurationParam(),
    default=Minutes(5),
    help="How often to check for ip updates.",
)
def cli(username: str, password: Path, hosts: list[str], check_delay: Duration):
    log.debug(f"{username=} {password=} {hosts=} {check_delay=}")
    with create_pyduc_updater(username, Path(password), hosts, check_delay) as pyduc:
        pyduc.run()
