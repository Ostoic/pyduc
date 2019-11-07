# pyduc
A Python No-IP Dynamic Update Client

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

 # Examples
 - python pyduc.py --username user --password-path /var/user/pw.txt --hostnames host1.noip.net, host2.noip.net --poll-sleep "5 minutes, 3 seconds, 1 hour"
 
 - python pyduc.py -u user -n host.noip.net
 
 - python pyduc.py --hostnames host.noip.net -u -s "10 minutes 17 seconds"
 
 - python pyduc.py -u user -n host.noip.net -s 1min
