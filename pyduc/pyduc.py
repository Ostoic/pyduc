import re
import base64
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from time import sleep

verbose = False

noip_error_messages = {
	# In the event that it allowed us to change our ip
	'good': lambda new_ip, hostname, response, duc=None: 
		'[noip-response] "{}": Ip address changed to "{}" for hostname "{}"'.format(
			response.text.strip('\r\n '), 
			new_ip, 
			hostname
		),
		
	'nochg': lambda response=None, duc=None, new_ip=None, hostname=None: 
		'[noip-response] "{}": No change needed'.format(response.text.strip('\r\n ')),
		
	# In the event that our host does not exist
	'nohost': lambda duc, hostname, response, new_ip=None:
		'[noip-response] "{}": Hostname "{}" is not associated with account "{}"'.format(
			response.text.strip('\r\n '), 
			hostname, 
			duc.username
		),
		
	# In the event that our username or password are incorrect
	'badauth': lambda response, duc=None, new_ip=None, hostname=None:
		'[noip-response] "{}": Invalid username or password'.format(response.text.strip('\r\n ')),
		
	# In the event that our user-agent field was invalid
	'badagent': lambda response, duc=None, new_ip=None, hostname=None:
		'[noip-response] "{}": Invalid user agent'.format(response.text.strip('\r\n ')),
		
	# In the event that no-ip has rate limited us
	'abuse': lambda response, duc=None, new_ip=None, hostname=None:
		'[noip-response] "{}": Abuse detected'.format(response.text.strip('\r\n ')),
		
	# In the event that a fatal error occured from no-ip's side
	'911': lambda response, duc=None, new_ip=None, hostname=None:
		'[noip-response] "{}": No-ip fatal error occured'.format(response.text.strip('\r\n '))
}

def error_code(response):
	response = response.text.strip('\r\n ')
	if verbose:
		print('[pyduc.error_code] Response: "{}"'.format(response))
	for error in noip_error_messages:
		if error in response:
			if verbose:
				print('[pyduc.error_code] Match found: "{}" in "{}"'.format(error, response))

			return error
			
	raise ValueError('No-ip error code for "{}" not found'.format(response))
	
def get_public_ip():
	response = requests.get('https://api.ipify.org', timeout=10).text.strip('\r\n ')
	if verbose:
		print('[pyduc.get_public_ip] Response: "{}"'.format(response))
		
	return response
	
class Pyduc:
	def __init__(self, username, hostnames, pw_path='./pw', poll_sleep_duration='30 seconds'):
		self.poll_sleep_duration =  poll_sleep_duration
		
		self.pw_path = pw_path
		if len(self.pw_path) == 0:
			raise ValueError('Invalid password path')
			
		self.username = username
		if len(self.username) == 0:
			raise ValueError('Invalid username')
		
		self.hostnames = hostnames
		if len(self.hostnames) == 0:
			raise ValueError('No hostnames provided')
		
		if len(self.__load_password()) == 0:
			raise ValueError('Invalid password')
			
		try:
			self.public_ip = get_public_ip()
			self.__last_public_ip = self.public_ip
		except:
			pass
			
		self.__headers = self.__make_http_headers()
		self.__needs_update = True
		
	def start(self, callback=None):
		print('Running dynamic update client')
			
		while True:
			# Call user-defined callback if there is one
			if callback:
				callback(self)
					
			# Dynamic ip update
			if self.needs_update():
				self.update_hostnames(new_ip = self.public_ip)
			else:
				sleep(self.poll_sleep_duration.total_seconds())
				try:
					# Get our public ip again in the case that it's changed
					self.update_public_ip()		
				except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError) as e:
					self.__needs_update = False
					pass
		
	def update_hostnames(self, new_ip=None):			
		if not new_ip:
			self.__needs_update = False
			return
		else:
			new_ip = self.public_ip
			
		if verbose:
			print('[pyduc.Pyduc.update_hostnames] Updating hostnames with ip: "{}"'.format(new_ip))
			
		for hostname in self.hostnames:
			if verbose:
				print('[pyduc.Pyduc.update_hostnames] Checking hostname: "{}"'.format(hostname))
			# Send HTTP get to noip update host
			try:
				response = self.__send_noip_request(ip = new_ip, hostname = hostname)
			except e:
				print('Error with noip request. Check Pyduc.error_log() for more info')
				self.__error_log.append(e)
				self.__needs_update = False
				return
			
			self.__handle_response(new_ip, hostname, response)
			self.__needs_update = False
		
	def needs_update(self):
		if verbose:
			print('[pyduc.Pyduc.needs_update] __needs_update: {}'.format(self.__needs_update))
			
		return self.__needs_update
		
	def update_public_ip(self):
		self.public_ip = get_public_ip()
		if self.public_ip != self.__last_public_ip:
			self.__last_public_ip = self.public_ip
			self.__needs_update = True
		else:
			self.__needs_update = False
		
					
	def __send_noip_request(self, hostname, ip):
		if verbose:
			print('[pyduc.Pyduc.__send_noip_request] Sending noip request...')
			
		response = requests.get(
			'https://{}:{}@dynupdate.no-ip.com/nic/update?hostname={}&myip={}'.format(
				self.username, self.__load_password(), 
				hostname, ip
			),
			headers=self.__headers
		)
		
		if verbose:
			print('[pyduc.Pyduc.__send_noip_request] Got response: "{}"'.format(response.text.strip('\r\n ')))
			
		return response
		
	def __handle_response(self, new_ip, hostname, response):
		print(noip_error_messages[error_code(response)](
			duc = self, 
			hostname = hostname, 
			new_ip = new_ip, 
			response = response
		))
			
	def __load_password(self):
		file = open(self.pw_path, 'r')
		password = file.read()
		file.close()
		return password
		
	def __make_http_headers(self):
		return {
			'host': 'dynupdate.no-ip.com',
			'authorization': self.__make_auth_key(),
			'user-agent': 'Company Device-Model/Firmware contact-me@email.com'
		}
		
	def __make_auth_key(self):
		return base64.b64encode('{}:{}'.format(self.username, self.__load_password()).encode('utf-8'))
	
	def __str__(self):
		return 'Username: "{}"\r\nPassword file: "{}"\r\nHostnames: {}\r\nPublic ip: "{}"\r\nPoll sleep duration: "{}"\r\nVerbose: {}\r\n'.format(
			self.username, self.pw_path, self.hostnames, get_public_ip(), self.poll_sleep_duration, verbose
		)
		
	def error_log(self):
		if verbose:
			print('[pyduc.Pyduc.error_log] Error log: {}'.format(self.__error_log))
		return self.__error_log
		
	hostnames = None
	username = None
	pw_path = None
	poll_sleep_duration = None
	
	public_ip = None

	__last_public_ip = None
	__headers = None
	__needs_update = None
	__error_log = []