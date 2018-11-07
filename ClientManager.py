import random
import datetime
import time
from subprocess import check_output, PIPE, Popen
import subprocess
import shlex
import threading
import os

import sys
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol

import Gateway as gt
import Client as cl
import MessageServerProtocol as server
import MessageClientProtocol as client
import PingTool as pt
import NeighbourManager as neighbour

class ClientManager():    
    client = None
    ping = pt.PingTool()
    neighbourManager = None
    
    gateways = []
    gatewayTable = []
    actualGateways = []
    updatedGateways = []
    round = 0
    connectRound = 0
    clientCount = 0
    proxyCount = 0
    receivedCount = 0
    rttLimit = 8
    
    
    # Used for connection section
    connectTime = None
    connectTimeRandom = None
    defaultGateway = None
    defaultGatewayRandom = None
    

    def __init__(self, client, neighbours, gateways):
        self.client = client
        self.gateways = gateways
        self.ping = pt.PingTool()
        self.neighbourManager = neighbour.NeighbourManager(self, neighbours)
	for gw in self.gateways:
	    gw.sender = self.client
    
    def addGateway(self, gateway):
        self.gateways.append(gateway)
    
    def removeGateway(self, gateway):
        for gw in self.gateways:
            if gw.address == gateway.address:
                self.gateways.remove(gw)

    def getRecentGateways(self):
	return [x for x in self.gatewayTable if (datetime.datetime.now() - x.ts).seconds <= (self.client.senseLatency+10)]

    def getRecentGatewaysOwn(self):
        return [x for x in self.gatewayTable if x.status == True and (datetime.datetime.now() - x.ts).seconds <= self.client.senseLatency and x.sender.address == self.client.address]

    def checkGatewayExists(self, gateway):
        for gw in self.gateways:
            if gw.address == gateway.address:
                return True
        return False

    #Selects the best gw from the last measurement period 
    def selectBestGateway(self):
        best = None
        for gw in self.getRecentGateways():  
            if best == None:
                best = gw
            if  best.latency > gw.latency:
                best = gw
        return best

    #SAMPLE 2 RANDOM GATEWAYS
    def select2Random(self):
        status = True
        if len(self.gateways)>2:               
            return random.sample(set(self.gateways), 2)
        else:
            return self.gateways

    def isUnique(self, gw):
	status = True
	for gwTemp in self.gatewayTable:
	    if(gwTemp == gw):
		status = False
		break
	return status

    def senseGateways(self):
        self.round +=1
        threading.Timer(self.client.senseLatency, self.senseGateways).start()
        status = False
	gws = self.select2Random()
	for gw in gws:
            status = self.ping.pingGateway(gw)
            if status == 0:
		self.removeGateway(gw)
	    else:
	        gw.actualLatency = gw.latency
            	self.setCategory(gw)
	        if(self.isUnique(gw)):
                    self.gatewayTable.append(gw)
#	self.printGatewayTable()
	self.neighbourManager.sendNeighbour(gws)
	self.printSimilarity()
	
    def printGatewayTable(self):
	gateways = self.getRecentGateways()
	for gw in gateways:
	   print(gw.ts,':',gw.address,':',gw.latency,':',gw.actualLatency,':',gw.sender.address)

    def senseAllGateways(self):
        #self.round +=1
        threading.Timer(self.client.senseLatency, self.senseAllGateways).start()
        
        for gw in self.actualGateways:
            status = self.ping.pingGateway(gw) 
            if status == 0:
                self.removeGateway(gw)
            else:
                self.setCategory(gw)
                
        self.gateways.sort(key=lambda x: (x.latency, x.ts), reverse=False)
        self.printSelectedGateway()
        
        
    def printSelectedGateway(self):
        gw = [x for x in self.gateways if x.address == '10.139.40.122']
        with open('selected_gw','a') as f:
            f.write("{0},{1},{2}\n".format(datetime.datetime.now(), gw[0].latency, gw[0].actualLatency))
        
    def printSimilarity(self):
        
        total = 0
        count1 = 0
        recent = self.getRecentGateways()
        print("=======================SIMILARITY MEASUREMENT================")
        for gw in recent:
            if gw.latency > gw.actualLatency:
                total += float(gw.actualLatency/gw.latency)
            else:
                total += float(gw.latency/gw.actualLatency)
            print(gw.address,':',gw.latency,":",gw.actualLatency,":", gw.ts)
        print('Total recent measurement sim:',':',float(total/len(recent)))
	recent_good = [x for x in recent if x.status == True]
        with open('nsimilar_measure20','a') as f:
                f.write("{0},{1},{2},{3}\n".format(datetime.datetime.now(),total/len(recent),len(recent_good), len(recent)))

    def updateGateways(self, gateways):
#	print("Updating info:",len(gateways))
	for gw in gateways:
	    self.setCategory(gw)
	    self.gatewayTable.append(gw)
	    #print("Updating:", gw.address, ':', gw.latency, ':', gw.actualLatency, ':', gw.sender.address)
#	self.printGatewayTable()

    def setCategory(self, gw):
        if gw.latency < 0.3:
            gw.status = True
        else:
            gw.status = False
        #print(gw.address,";", gw.status,";",gw.latency)


    def getLatestMovingAverage(self):
	candidates = [] #Emptying the candidate list first to update new info
        performances = self.getRecentGateways()
        #Filtering last 2 measurement round results
        gateway_candidates = [x for x in performances if (datetime.datetime.now() - x.ts).seconds <= (self.client.senseLatency*2+20)]
        #Filtering unique gateways
        addresses = list(set([x.address for x in gateway_candidates]))
        for address in addresses:
            #Filtering only those gateway performances
            performances = [x for x in gateway_candidates if x.address == address]
	    performances.sort(key=lambda x: (x.ts), reverse=False)
	    print(address, ':',[[x.latency] for x in performances])
            size = len(performances)
            i =1
            latency = 0
	    actualLatency = 0
	    root = (1+size)*size/2
            for perf in performances:
                latency += (perf.latency*i)/root
                i+=1
		actualLatency = perf.actualLatency
            gw = gt.Gateway(perf.address, latency, datetime.datetime.now(), status = True, sender=None)
	    gw.actualLatency = actualLatency
	    self.setCategory(gw)
            candidates.append(gw)
	return candidates

    #Select the random best from the smoothed performances.
    def selectRandomBest(self):
	candidates = self.getLatestMovingAverage()
	candidates = [x for x in candidates if x.status == True]
	print("Best random:", [[x.address, x.latency] for x in candidates])
        choice = random.choice([x.address for x in candidates])
        print("Best random choice:", choice)
        return choice

    def isDefaultRandomGood(self):
	for gw in self.getRecentGateways():
	    if gw.address == self.defaultGatewayRandom:
		return True
	return False

    def connectRandom(self):
#        print("Connecting collab random")
        threading.Timer(60.0, self.connectRandom).start()
	gatewayCandidates = self.getRecentGateways()
        if len(gatewayCandidates) == 0:
            return
        while True:
            if self.defaultGatewayRandom == None:
                self.defaultGatewayRandom = self.selectRandomBest()
                self.connectTimeRandom = datetime.datetime.now()

	    if self.isDefaultRandomGood() == False:
                self.connectTimeRandom = datetime.datetime.now()
                self.defaultGatewayRandom = self.selectRandomBest()

            cmd='''curl -x '''+self.defaultGatewayRandom+''':3128 -U david.pinilla:"|Jn 5DJ\\7inbNniK|m@^ja&>C" -m 180 -w %{time_starttransfer},%{time_total},%{http_code},%{size_download} http://ovh.net/files/10Mb.dat -o /dev/null -s'''
            command = Popen(shlex.split(cmd),stdout=PIPE, stderr=PIPE)
            stdout, stderr = command.communicate()
            ttfb, lat, status,size = stdout.decode("utf-8").split(',')
            if status !=0:                
                with open('download_result_collab_random5','a') as f:
                    f.write("{0},{1},{2},{3},{4},{5}\n".format(datetime.datetime.now(), self.defaultGatewayRandom,float(ttfb),float(lat),int(status),int(size)))
                    break
            
        
    def connectBest(self):
        print("Connecting collab best")
        threading.Timer(60.0, self.connectBest).start()
        
        if self.defaultGateway == None:
            self.defaultGateway = self.selectBestGateway()
            self.connectTime = datetime.datetime.now()
        elif (datetime.datetime.now() - self.connectTime).seconds >=300:
            self.connectTime = datetime.datetime.now()
            self.defaultGateway = self.selectBestGateway()
            
        if self.defaultGateway == None:
            return
        

        cmd='''curl -x '''+self.defaultGateway.address+''':3128 -U david.pinilla:"|Jn 5DJ\\7inbNniK|m@^ja&>C" -m 180 -w %{time_starttransfer},%{time_total},%{http_code},%{size_download} http://ovh.net/files/10Mb.dat -o /dev/null -s'''
        command = Popen(shlex.split(cmd),stdout=PIPE, stderr=PIPE)
        stdout, stderr = command.communicate()
        ttfb, lat, status,size = stdout.decode("utf-8").split(',')
        with open('download_collab_best','a') as f:
            f.write("{0},{1},{2},{3},{4},{5}\n".format(datetime.datetime.now(), self.defaultGateway.address,float(ttfb),float(lat),int(status),int(size)))
            
    
    def connectBruteForce(self):
        print("Connecting Brute Force")
        threading.Timer(300.0, self.connectBruteForce).start()
        gwAddress = [x.address for x in self.gateways]
        bestGW = None
        for gw in gwAddress:
            tempGW = gt.Gateway(gw, 0.5, datetime.datetime.strptime('2018-03-15 18:59:15', '%Y-%m-%d %H:%M:%S'), status = False)
            status = self.ping.pingGateway(tempGW) 
            if status != 0:
                self.setCategory(tempGW)
            if bestGW == None:
                bestGW = tempGW
            elif bestGW.latency > tempGW.latency:
                bestGW = tempGW

        if bestGW == None:
            return
        count = 0        
        print("Best gw:", bestGW.address)
        while count <5:
            cmd='''curl -x '''+bestGW.address+''':3128 -U david.pinilla:"|Jn 5DJ\\7inbNniK|m@^ja&>C" -m 180 -w %{time_starttransfer},%{time_total},%{http_code},%{size_download} http://ovh.net/files/10Mb.dat -o /dev/null -s'''
            command = Popen(shlex.split(cmd),stdout=PIPE, stderr=PIPE)
            stdout, stderr = command.communicate()
            ttfb, lat, status,size = stdout.decode("utf-8").split(',')
            with open('download_brute_force','a') as f:
                f.write("{0},{1},{2},{3},{4},{5}\n".format(datetime.datetime.now(),
                                                       bestGW.address,float(ttfb),float(lat),int(status),int(size)))
            time.sleep(60)
            count +=1
            

