import base64
import logging
from contextlib import contextmanager
from pathlib import Path
from time import sleep
from typing import Callable, Generator, Iterable, TypeAlias
from urllib import parse

import requests
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout, Response, Timeout
from stuom import Seconds

from pyduc.util import Duration, StoredPassword, delete_after, safe_load_password

log = logging.getLogger(__file__)


_noip_error_messages = {
    # In the event that it allowed us to change our ip
    "good": lambda new_ip, hostname, response, duc=None: (
        '[noip-response] "{}": Ip address changed to"{}" for hostname "{}"'.format(
            response.text.strip("\r\n "), new_ip, hostname
        )
    ),
    "nochg": lambda hostname, response=None, duc=None, new_ip=None: (
        '[noip-response] "{}": No change needed for "{}"'.format(
            response.text.strip("\r\n "), hostname
        )
    ),
    # In the event that our host does not exist
    "nohost": lambda duc, hostname, response, new_ip=None: (
        '[noip-response] "{}": Hostname "{}" is not associated with account "{}"'.format(
            response.text.strip("\r\n "), hostname, duc.username
        )
    ),
    # In the event that our username or password are incorrect
    "badauth": lambda response, duc=None, new_ip=None, hostname=None: (
        '[noip-response] "{}": Invalid username or password'.format(response.text.strip("\r\n "))
    ),
    # In the event that our user-agent field was invalid
    "badagent": lambda response, duc=None, new_ip=None, hostname=None: (
        '[noip-response] "{}": Invalid user agent'.format(response.text.strip("\r\n "))
    ),
    # In the event that no-ip has rate limited us
    "abuse": lambda response, duc=None, new_ip=None, hostname=None: (
        '[noip-response] "{}": Abuse detected'.format(response.text.strip("\r\n "))
    ),
    # In the event that a fatal error occured from no-ip's side
    "911": lambda response, duc=None, new_ip=None, hostname=None: (
        '[noip-response] "{}": No-ip fatal error occured'.format(response.text.strip("\r\n "))
    ),
}


def _error_code(response: Response):
    response_text = response.text.strip("\r\n ")

    log.debug(f' Response: "{response}"')
    for error in _noip_error_messages:
        if error in response_text:
            log.debug(' Match found: "{}" in "{}"'.format(error, response))

            return error

    raise ValueError(f'No-ip error code for "{response}" not found')


_URLS = [
    "https://icanhazip.com",
    "https://api.ipify.org",
    "http://icanhazip.com",
    "http://api.ipify.org",
]


def _get_public_ip():
    for url in _URLS:
        try:
            response = requests.get(url, timeout=10).text.strip("\r\n ")
            log.info(f'[pyduc.get_public_ip] Response: "{response}"')
            return response

        except (ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError):
            log.exception(
                f"[pyduc.get_public_ip] failed to connect to {url}. Trying another service..."
            )

    raise Timeout()


PyducCallback: TypeAlias = Callable[["Pyduc"], None]


@contextmanager
def create_pyduc_updater(
    username: str,
    pw_path: Path,
    hostnames: Iterable[str],
    check_delay: Duration,
) -> Generator["Pyduc", None, None]:
    public_ip = _get_public_ip()
    stored_pw = StoredPassword(pw_path)
    yield Pyduc(username, stored_pw, hostnames, check_delay, public_ip)


class Pyduc:
    def __init__(
        self,
        username: str,
        stored_pw: StoredPassword,
        hostnames: Iterable[str],
        check_delay: Duration,
        public_ip: str,
    ):
        self.check_delay = check_delay
        self.pw = stored_pw
        self.hostnames = hostnames
        self.username = username

        if len(self.username) == 0:
            raise ValueError("Invalid username")

        with safe_load_password(stored_pw) as password:
            if len(password) == 0:
                raise ValueError("Invalid password")

        self.public_ip = public_ip
        self.__last_public_ip = public_ip

        self.__headers = self._make_http_headers()
        self.__needs_update = True

    def run(self, callback: None | PyducCallback = None):
        log.info("Running dynamic update client")

        while True:
            # Call user-defined callback if there is one
            if callback is not None:
                callback(self)

            # Dynamic ip update
            if self.needs_update():
                self.update_hostnames(new_ip=self.public_ip)

            else:
                sleep(Seconds.from_duration(self.check_delay))

                try:
                    # Get our public ip again in the case that it's changed
                    self.update_public_ip()

                except (
                    ConnectTimeout,
                    HTTPError,
                    ReadTimeout,
                    Timeout,
                    ConnectionError,
                ):
                    self.__needs_update = False

    def update_hostnames(self, new_ip: str | None = None):
        if new_ip is None:
            self.__needs_update = False
            return

        else:
            # new_ip = self.public_ip
            log.info(f'Updating hostnames with ip: "{new_ip}"')

        for hostname in self.hostnames:
            log.info(f'Checking hostname: "{hostname}"')
            # Send HTTP get to noip update host
            try:
                response = self._send_noip_request(hostname=hostname, ip=new_ip)
                log.info(f"Updated hosts to point to {new_ip}.")

            except Exception:
                log.exception("Error with noip request. Check Pyduc.error_log() for more info")
                self.__needs_update = False
                return

            self._handle_response(new_ip, hostname, response)
            self.__needs_update = False

    def needs_update(self) -> bool:
        log.debug(f"__needs_update: {self.__needs_update}")
        return self.__needs_update

    def update_public_ip(self):
        self.public_ip = _get_public_ip()
        if self.public_ip != self.__last_public_ip:
            self.__last_public_ip = self.public_ip
            self.__needs_update = True
        else:
            self.__needs_update = False

    def _send_noip_request(self, hostname: str, ip: str) -> Response:
        log.debug("Sending noip request...")
        with safe_load_password(self.pw) as password:
            with delete_after(parse.quote_plus(password)) as quoted_password:
                with delete_after(
                    f"https://{self.username}:{quoted_password}@dynupdate.no-ip.com/nic/update?hostname={hostname}&myip={ip}"
                    .encode("utf8")
                ) as url:
                    response = requests.get(url, headers=self.__headers)

        log.debug('Got response: "{}"'.format(response.text.strip("\r\n ")))
        return response

    def _handle_response(self, new_ip: str, hostname: str, response: Response):
        log.error(
            _noip_error_messages[_error_code(response)](
                duc=self, hostname=hostname, new_ip=new_ip, response=response
            )
        )

    def _make_http_headers(self):
        return {
            "host": "dynupdate.no-ip.com",
            "authorization": self._make_auth_key(),
            "user-agent": "Company Device-Model/Firmware contact-me@email.com",
        }

    def _make_auth_key(self):
        with safe_load_password(self.pw) as password:
            with delete_after(f"{self.username}:{password}") as formatted:
                with delete_after(formatted.encode("utf-8")) as formatted_bytes:
                    return base64.b64encode(formatted_bytes)

    def __str__(self):
        return (
            f'Username: "{self.username}"\r\nStored password: "{self.pw}"\r\nHostnames:'
            f' {self.hostnames}\r\nPublic ip: "{_get_public_ip()}"\r\nPoll sleep duration:'
            f" {self.check_delay}\r\n"
        )
