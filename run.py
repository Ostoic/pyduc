import sys
import pyduc.cli
from pyduc import Pyduc

args = pyduc.cli.args
pyduc = Pyduc(
	username = args.username,
	hostnames = args.hostnames,
	pw_path = args.pw_path, 
	poll_sleep_duration = args.poll_sleep,
)

print(pyduc)
pyduc.start()
