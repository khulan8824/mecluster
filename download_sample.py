import random
import sys
sys.path.append(".")
import Client as cl
import Gateway as gt
import ClientManager as cm
import MessageClientProtocol
import MessageServerProtocol as server
import PingTool as pt

from subprocess import check_output, PIPE, Popen
import datetime
import time
import os
import threading
import subprocess
import shlex
from twisted.internet import reactor,protocol

class Random():
    gateways = []
    ping = pt.PingTool()

    def connectRandom(self, size):
        print("Random sampling: ",size)
        threading.Timer(300.0, self.connectRandom,[size]).start()
        gwAddress = []
        gateways = None
        bestGW = None
        while True:
            gwAddress = random.sample(set([x.address for x in self.gateways]), size)
            count = 0
            temp = []
            for gw in gwAddress:
                tempGW = gt.Gateway(gw, 0.5, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
                status = self.ping.pingGateway(tempGW) 
                if status != 0:
                    temp.append(tempGW)
                else:
                    temp = []
                    continue #Skip the loop

            if len(temp) == size: #If they have 2 candidates
                gateways = temp
                break

        #=============AFTER RESULT OF 2 FEASIBLE MEASUREMENT

        for gw in gateways:
            if bestGW == None:
                bestGW = gw
            elif bestGW.latency > gw.latency:
                bestGW = gw

        if bestGW == None:
            return
        count = 0        
#	while count <5:
        cmd='''curl -x '''+bestGW.address+''':3128 -U david.pinilla:"|Jn 5DJ\\7inbNniK|m@^ja&>C" -m 180 -w %{time_starttransfer},%{time_total},%{http_code} http://ovh.net/files/10Mb.dat -o /dev/null -s'''
        command = Popen(shlex.split(cmd),stdout=PIPE, stderr=PIPE)
        stdout, stderr = command.communicate()
        ttfb, lat, status = stdout.decode("utf-8").split(',')
        with open('download_random_'+str(size),'a') as f:
		f.write("{0},{1},{2},{3},{4},{5}\n".format(datetime.datetime.now(),
                                                       bestGW.address,float(ttfb),float(lat),int(status), int(size)))
#        time.sleep(60)
#            count +=1

n1 = gt.Gateway('10.139.39.98', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n2 = gt.Gateway('10.139.37.194', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n3 = gt.Gateway('10.228.192.210', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n4 = gt.Gateway('10.139.7.4', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n5 = gt.Gateway('10.1.33.36', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n6 = gt.Gateway('10.139.40.85', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n7 = gt.Gateway('10.139.40.122', 0.20, datetime.datetime.strptime('2018-02-15 18:20:15', '%Y-%m-%d %H:%M:%S'),False)
n8 = gt.Gateway('10.138.25.67', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n9 = gt.Gateway('10.138.57.2', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n10 = gt.Gateway('10.139.17.4', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n11 = gt.Gateway('10.138.85.130', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n12 = gt.Gateway('10.138.120.66', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n13 = gt.Gateway('10.140.93.35', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n14 = gt.Gateway('10.228.193.210', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
n15 = gt.Gateway('10.228.204.9', 0.15, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)

listActual = [n1,n2,n3,n4,n6,n7,n8,n9,n10,n11,n12,n13,n14,n15]

random1 = Random()
random1.gateways =listActual
random1.connectRandom(3)
