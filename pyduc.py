import requests
import base64
import time

hostname = "hostname.noip.net"
username = ""
password = "xxxxxxxx"
ip = requests.get('https://api.ipify.org').text

update_request_url = "https://{}:{}@dynupdate.no-ip.com/nic/update?hostname={}&myip={}".format(username, password, hostname, ip)

headers = {
	'host': 'dynupdate.no-ip.com',
	'authorization': base64.b64encode('{}:{}'.format(username, password).encode('utf-8')),
	'user-agent': 'Company Device-Model/Firmware contact@me.com'
}

print('Updating no-ip hostname: {}'.format(hostname))

while True:
	response = requests.get(update_request_url, headers=headers)
	if 'good' in response.text:
		print('IP address changed to {}'.format(ip))
		
	elif not 'nochg' in response.text:
		print('Error changing ip address: {}'.format(response.text))
	
	time.sleep(60*5)