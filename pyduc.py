import requests
import base64
import time
from datetime import timedelta as duration

# Get our public ip address
def public_ip():
	return requests.get('https://api.ipify.org').text
	
def load_password(path):
	pw_file = open(path, 'r')
	password = pw_file.read()
	pw_file.close()
	return password
	
def make_auth_key(hostname, password):
	return base64.b64encode('{}:{}'.format(username, password).encode('utf-8'))

hostnames = ["other-proxy.ddns.net"]
username = "username"
password = load_password('/var/user/pw')
poll_sleep_duration = duration(minutes=5)

headers = {
	'host': 'dynupdate.no-ip.com',
	'authorization': make_auth_key(username, password),
	'user-agent': 'Company Device-Model/Firmware contact@me.com'
}

print('pyduc 1.0: Python No-IP Dynamic Update Client')
print('Username: {}'.format(username))
print('Hostnames: {}'.format(hostnames))
print('Current public ip address: {}'.format(public_ip()))
print('Poll sleep duration {}'.format(poll_sleep_duration))

while True:
	# Poll dynamic ip update
	for hostname in hostnames:
		# Send HTTP get to noip update host
		response = requests.get(
			'https://{}:{}@dynupdate.no-ip.com/nic/update?hostname={}&myip={}'.format(username, password, hostname, public_ip),
			headers=headers
		)
		
		# In the event that it allowed us to change our ip
		if 'good' in response.text:
			print('[pyduc] ip address changed to {}'.format(public_ip))
			
		# In the event that our host does not exist
		elif not 'nochg' in response.text:
			print('[pyduc] Invalid hostname: {}'.format(response.text))
	
	# Wait before checking again so we don't get rate limited by no-ip
	time.sleep(poll_sleep_duration.total_seconds())
