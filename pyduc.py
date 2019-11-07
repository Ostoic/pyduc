import requests
import base64
import argparse
import sys
import re

from time import sleep
from datetime import timedelta as duration

script_name = 'Pyduc 1.1 No-IP Dynamic Update Client'

# Compile duration regex
duration_regex = {
	'seconds': re.compile(r'([0-9]+)[ \t]*se?c?s?o?n?d?s?'),
	'minutes': re.compile(r'([0-9]+)[ \t]*minu?t?e?s?'),
	'hours': re.compile(r'([0-9]+)[ \t]*ho?u?rs?')
}

def flatten_list(x):
	if x == []:
		return 0
	
	return int(x[0])

def parse_duration(string):
	seconds = flatten_list(duration_regex['seconds'].findall(string))
	minutes = flatten_list(duration_regex['minutes'].findall(string))
	hours = flatten_list(duration_regex['hours'].findall(string))
		
	if seconds == 0 and minutes == 0 and hours == 0:
		return duration(minutes = 5)
		
	else:
		return duration(seconds=seconds, minutes=minutes, hours=hours)
		
# Setup a CLI argument parser
parser = argparse.ArgumentParser(prog='python pyduc.py')
parser.add_argument(
	'-u',
	'--username',
	type = str,
	help = 'The username for your no-ip account',
	required = True
)

parser.add_argument(
	'-n',
	'--hostnames',
	nargs = '+',
	type = lambda str: str.strip(' ,'),
	help = 'The list of no-ip hostnames to update',
	required = True
)

parser.add_argument(
	'-p',
	'--password-path', 
	type = str,
	default = '/var/root/duc/pw',
	help = 'The path to the file that holds your no-ip account password'
)

parser.add_argument(
	'-s',
	'--poll-sleep',
	type = parse_duration,
	default = '5 minutes',
	help = 'How often to check for ip updates'
)

# Get our public ip address
def get_public_ip():
	return requests.get('https://api.ipify.org').text
	
def load_password(path):
	pw_file = open(path, 'r')
	password = pw_file.read()
	pw_file.close()
	return password
	
def make_auth_key(hostname, password):
	return base64.b64encode('{}:{}'.format(username, password).encode('utf-8'))

# Parse CLI arguments
args = parser.parse_args()

# Handle CLI arguments
if not args.hostnames:
	parser.print_help()
	print('Error: Hostnames required')
	sys.exit()
	
if not args.username:
	parser.print_help()
	print('Error: Username required')
	sys.exit()

hostnames = args.hostnames
username = args.username
pw_file_path = args.password_path
password = load_password(pw_file_path)
poll_sleep_duration = args.poll_sleep
public_ip = get_public_ip()

headers = {
	'host': 'dynupdate.no-ip.com',
	'authorization': make_auth_key(username, password),
	'user-agent': 'Company Device-Model/Firmware contact@me.com'
}

print('Username: {}'.format(username))
print('Password file path: {}'.format(pw_file_path))
print('Hostnames: {}'.format(hostnames))
print('Public ip: {}'.format(public_ip))
print('Poll sleep duration {} (H:MM:SS)\n'.format(poll_sleep_duration))

while True:
	# Dynamic ip update
	for hostname in hostnames:
		# Send HTTP get to noip update host
		response = requests.get(
			'https://{}:{}@dynupdate.no-ip.com/nic/update?hostname={}&myip={}'.format(username, password, hostname, public_ip),
			headers=headers
		)
		
		# In the event that it allowed us to change our ip
		if 'good' in response.text:
			print('Success [{}]: Ip address changed to >{}< for hostname >{}<'.format(response.text.strip('\r\n '), public_ip, hostname))
			
		# In the event that our host does not exist
		elif 'nohost' in response.text:
			print('Error [{}]: Hostname >{}< is not associated with account >{}<'.format(response.text.strip('\r\n '), hostname, username))
			
		# In the event that our username or password are incorrect
		elif 'badauth' in response.text:
			print('Error [{}]: Invalid username or password'.format(response.text.strip('\r\n ')))
			
		# In the event that our username or password are incorrect
		elif 'badagent' in response.text:
			print('Error [{}]: Invalid user agent'.format(response.text.strip('\r\n ')))
			
		# In the event that no-ip has rate limited us
		elif 'abuse' in response.text:
			print('Error [{}]: Abuse detected'.format(response.text.strip('\r\n ')))
			
		# In the event that a fatal error occured from no-ip's side
		elif '911' in response.text:
			print('Error [{}]: No-ip fatal error occured'.format(response.text.strip('\r\n ')))
	
	# Wait before checking again so we don't get rate limited by no-ip
	sleep(poll_sleep_duration.total_seconds())
	
	# Get our public ip again in the case that it's changed
	public_ip = get_public_ip()
