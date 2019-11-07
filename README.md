# pyduc
A Python No-IP Dynamic Update Client

Pyduc is for those who need a quick and easy-to-use dynamic update client for their no-ip hostnames. For non-Windows machines, the client No-IP provides requires one to be able to compile it for their target machine. In the situation that setting up a build environment for their device requires great effort (such as on a jailbreak iDevice), this script is a good solution.

No-IP does provide a DUC for linux-like operating systems, but I was unable to cross-compile it for my jailbroken iPad. 

# Requirements
- Python 2.7
- Python requests library
- Openssl >= 0.9.8g

# Usage
```
Pyduc 1.1 No-IP Dynamic Update Client 
usage:
  python pyduc.py -u USERNAME -n HOSTNAMES [HOSTNAMES ...] [-h] [-p PASSWORD_PATH]  [-s POLL_SLEEP]                                                                                                                                                                                    
  
required arguments:
  -u USERNAME, --username USERNAME                 
          The username for your no-ip account
  -n HOSTNAMES [HOSTNAMES ...], --hostnames HOSTNAMES [HOSTNAMES ...] 
          The list of no-ip hostnames to update                      
optional arguments:
  -h, --help                                       
          Show this help message and exit
  -p PASSWORD_PATH, --password-path PASSWORD_PATH  
          The path to the file that holds your no-ip account password                                       
  -s POLL_SLEEP, --poll-sleep POLL_SLEEP 
          How often to check for ip updates
```
If you do provide a path to your password file, it must be a file that contains nothing but your password.

 # Examples
 - python pyduc.py --username user --password-path /var/user/pw.txt --hostnames host1.noip.net, host2.noip.net --poll-sleep "5 minutes, 3 seconds, 1 hour"
 
 - python pyduc.py -u user -n host.noip.net
 
 - python pyduc.py --hostnames host.noip.net -u -s "10 minutes 17 seconds"
 
 - python pyduc.py -u user -n host.noip.net -s 1min
