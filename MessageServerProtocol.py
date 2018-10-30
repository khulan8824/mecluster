import datetime
from subprocess import check_output, PIPE, Popen
import subprocess
import shlex
import threading
import os

import sys
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.internet.protocol import ServerFactory, Protocol
import Gateway as gw
import Client as cl

#SERVER SECTION
class MessageServerProtocol(Protocol):
    client = None
    
#    def connectionMade(self):
#        print('Server started running at: '+ self.transport.getPeer().host+'\n')

    # When receiving data from the client, it should update neighbour information
    def dataReceived(self,data):
#        print("DATA:", data)
            
        connected = self.transport.getPeer().host
        
        if self.client is not None:
	    #print('Received info from:', self.client.address)
            #If information received from the unlisted new close neighbour 
            #then add it to the close neighbouring list
            if self.client.cManager.neighbourManager.isNeighbourExists(connected) is False:
                self.client.cManager.neighbourManager.addCloseNeigbour(connected)           
            
            if str(data.decode('utf-8')) == 'ask':
                text = self.client.cManager.neighbourManager.sendInformation(True, None)
                #print("Sending information back:",connected, ',',text)
                #Sending all measurement back to the client
                self.client.cManager.neighbourManager.sendMeasurements(connected, text)
                return
            
            nlist = data.decode('utf-8').split(',')
            gateways = []
            for gwInfo in nlist:
                address, latency, ts, sender  = gwInfo.split('#')
                gwTemp =gw.Gateway(str(address), float(latency), datetime.datetime.strptime(ts,'%Y-%m-%d %H:%M:%S'), False)
                #Checking actual GW performance
                tempLat = float(latency)
                tempTs = datetime.datetime.strptime(ts,'%Y-%m-%d %H:%M:%S')
		tempSender = cl.Client(sender,[],[],None)
                self.client.cManager.ping.getPingGateway(gwTemp)
                actual = gwTemp.latency
                gwTemp.latency = tempLat
                gwTemp.actualLatency = actual
                gwTemp.ts = tempTs
		gwTemp.sender = tempSender
                with open('estimation','a') as f:  
                    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+','+gwTemp.address+','+str(gwTemp.latency)+','+str(gwTemp.actualLatency)+','+str(sender)+'\n')
#                self.client.cManager.gatewayTable.append(gwTemp)
		gateways.append(gwTemp)
	
                
            self.client.cManager.updateGateways(gateways)
            status = False
            
        
#    def connectionLost(self, reason):
#        print("Connection lost:", self.transport.getPeer())
        #with open('log','a') as f:  
        #    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+', Server connection lost\n')
        #reactor.callFromThread(reactor.stop)
        #if reactor.running:
        #        reactor.stop()
        #os._exit(0)
