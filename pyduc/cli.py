import argparse
import sys
import re
from datetime import timedelta as duration

__duration_regex = {
	'seconds': re.compile(r'([0-9]+)[ \t]*se?c?s?o?n?d?s?'),
	'minutes': re.compile(r'([0-9]+)[ \t]*minu?t?e?s?'),
	'hours': re.compile(r'([0-9]+)[ \t]*ho?u?rs?')
}
		
def __flatten_list(x):
	if x == []:
		return 0
	
	return int(x[0])

def __parse_duration(string):
	seconds = __flatten_list(__duration_regex['seconds'].findall(string))
	minutes = __flatten_list(__duration_regex['minutes'].findall(string))
	hours = __flatten_list(__duration_regex['hours'].findall(string))
		
	if seconds == 0 and minutes == 0 and hours == 0:
		return duration(minutes = 5)
		
	else:
		return duration(seconds=seconds, minutes=minutes, hours=hours)	

__parser = argparse.ArgumentParser()
__parser.add_argument(
	'-u',
	'--username',
	type = str,
	help = 'The username for your no-ip account',
	required = True
)

__parser.add_argument(
	'-n',
	'--hostnames',
	nargs = '+',
	type = lambda str: str.strip(' ,'),
	help = 'The list of no-ip hostnames to update',
	required = True
)

__parser.add_argument(
	'-p',
	'--password-path', 
	type = str,
	default = './pw',
	help = 'The path to the file that holds your no-ip account password'
)

__parser.add_argument(
	'-s',
	'--poll-sleep',
	type = __parse_duration,
	default = '30 seconds',
	help = 'How often to check for ip updates'
)

__parser.add_argument(
	'-v',
	'--verbose',
	action = 'store_true',
	help = 'Enable verbose logging'
)

# Parse CLI arguments
args = __parser.parse_args()

args.pw_path = args.password_path

# Handle CLI arguments
if not args.hostnames:
	__parser.print_help()
	print('Error: Hostnames required')
	sys.exit()
	
if not args.username:
	__parser.print_help()
	print('Error: Username required')
	sys.exit()
	
if not args.verbose:
	args.verbose = False
else:
	args.verbose = True
		