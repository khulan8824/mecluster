import random
import datetime
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

class NeighbourManager():
    cManager = None
    
    neighbours = []
    closeNeighbours = []
    minNeighbour = None
    minRTT = 5
    
    def __init__(self, cManager, neighbours):
        self.cManager = cManager
        self.neighbours = neighbours

            
    def addCloseNeigbour(self, address):
        nb = cl.Client(address,[],[],None)
        self.closeNeighbours.append(nb)
        self.addNeighbour(nb)
        
    def addNeighbour(self, neighbour):
        for nb in self.neighbours:
            if nb.address == neighbour.address:
                return
            self.neighbours.append(neighbour)
    
    def removeNeighbour(self, neighbour):
        for nb in self.neighbours:
            if nb.address == neighbour.address:
                self.neighbours.remove(nb)

    def isNeighbourExists(self, address):
        for nb in self.closeNeighbours:
            if nb.address == address:
                return True
        return False

    def senseNeighbours(self):
        for nb in self.neighbours:            
	    if self.cManager.client.address == nb.address:
		continue
            rtt = self.cManager.ping.pingTest(nb.address) #CHANGE
            
            print(nb.address,":", rtt)            
            if rtt == 0:
                self.removeNeighbour(nb)
            elif rtt < self.cManager.rttLimit:
                self.closeNeighbours.append(nb)
                if self.minNeighbour is None:
                    self.minNeighbour = nb
                    self.minRTT = rtt
                else:
                    if self.minRTT > rtt:
                        self.minNeighbour = nb
                        self.minRTT = rtt
            else:
                if nb in self.closeNeighbours:
                    self.closeNeighbours.remove(nb)      
            
        self.printCloseNeighbours()

    def sendInformation(self, status, gateways):        
        info = ""
        if status is True:
        #Sending all gateway information
            for gw in self.cManager.getRecentGateways():
                if info != "":
                    info += ","
                info += gw.address+'#'+str(gw.latency)+'#'+gw.ts.strftime("%Y-%m-%d %H:%M:%S")+'#'+gw.sender.address
        else:            
        #sending updated information, not all information        
            for gw in gateways:
                if info != "":
                    info += ","
                info += gw.address+'#'+str(gw.latency)+'#'+gw.ts.strftime("%Y-%m-%d %H:%M:%S")+'#'+gw.sender.address
        return info
    
    # Send information to neighbour 
    def sendNeighbour(self, gateways):
        text = self.sendInformation(False, gateways)
        self.cManager.updatedGateways = []
        for neighbour in self.closeNeighbours:
	    print('Sending:',neighbour.address, ':', text)
            f = protocol.ClientFactory()
            f.protocol = client.MessageClientProtocol
            f.protocol.client = self.cManager.client
            f.protocol.mode='client'
            f.protocol.text = text
            f.protocol.addr = neighbour.address
            reactor.connectTCP(neighbour.address, 5555, f)
            #self.addClientCount()
        #self.round +=1

    #Sending all measurements to the client
    def sendMeasurements(self, address, text):
        f = protocol.ClientFactory()
        f.protocol = client.MessageClientProtocol
        f.protocol.client = self.cManager.client
        f.protocol.mode='client'
        f.protocol.text = text
        f.protocol.addr = address
        reactor.connectTCP(address, 5555, f)
    
    def printCloseNeighbours(self):
        print("Close neighbours")
        if len(self.closeNeighbours) == 0:
            print('No close neighbours')
            return
        for nb in self.closeNeighbours:
            print(nb.address)
            

    def askMeasurements(self):
        print('Min neighbour:', self.minNeighbour.address)
        f = protocol.ClientFactory()
        f.protocol = client.MessageClientProtocol
        f.protocol.client = self
        f.protocol.mode='client'
        f.protocol.text = 'ask'
        f.protocol.addr = self.minNeighbour.address
        reactor.connectTCP(self.minNeighbour.address, 5555, f)
