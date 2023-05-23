import math
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, TypeVar

import click
import stuom
from stuom import Duration


class CliDurationParam(click.ParamType):
    name = "time"

    def convert(self, value, param, ctx) -> Duration:  # type: ignore
        match value:
            case str() as s:
                return stuom.parse.parse_duration(s)

            case Duration() as d:
                return d

            case _:
                raise TypeError(f"Invalid duration type: {type(value)}")


@dataclass(frozen=True, slots=True)
class StoredPassword:
    path: Path


AnyT = TypeVar("AnyT", bound=Any)


@contextmanager
def delete_after(x: AnyT) -> Generator[AnyT, None, None]:
    """Delete an object after being used at the end of the context.

    Args:
        x (AnyT): The object to forcefull garbage collect.

    Yields:
        Generator[AnyT, None, None]: A reference to the object.
    """
    yield x
    del x


@contextmanager
def safe_load_password(stored_pw: StoredPassword) -> Generator[str, None, None]:
    """Load a password from the `StoredPassword` object, which after being used is forcefully
    garbage collected.

    Args:
        stored_pw (StoredPassword): The stored password to load from.

    Yields:
        Generator[str, None, None]: A string containing the password.
    """

    with stored_pw.path.open("r") as pw_file:
        password = pw_file.read()
        yield password
        del password
