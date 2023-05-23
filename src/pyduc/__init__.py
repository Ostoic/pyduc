from . import config
from .pyduc import Pyduc

try:
    import click

    from .cli import cli
except ImportError:
    pass
