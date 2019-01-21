import datetime
from subprocess import check_output, PIPE, Popen
import subprocess
import shlex
import os
import threading
import sys

proxies = [line.rstrip('\n') for line in open('proxies.txt')]
def sense():
	if not os.path.isdir("test"):
		os.system("mkdir test")
	threading.Timer(60,sense).start()
	for proxy in proxies:
		status = True
		cmd='''curl -x '''+proxy+''':3128 -U david.pinilla:"|Jn 5DJ\\7inbNniK|m@^ja&>C" -m 180 -w %{time_starttransfer},%{time_total},%{http_code} http://ovh.net/files/1Mb.dat -o /dev/null -s'''
		command = Popen(shlex.split(cmd),stdout=PIPE, stderr=PIPE)
	        stdout, stderr = command.communicate()
        	rtt, lat, status = stdout.decode("utf-8").split(',')
		with open("test/"+proxy,'a') as f:
			f.write("{0},{1},{2},{3},{4}\n".format(datetime.datetime.now(),rtt, lat, proxy,status))

sense()
