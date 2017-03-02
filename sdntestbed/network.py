#!/usr/bin/env python

import time

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.link import TCLink
from mininet.topolib import Topo
from mininet.util import quietRun
from mininet.node import RemoteController

from networkx import nx
from random import randint
from termcolor import colored

class RandomTopo(Topo):
    "Random topology"

    def __init__(self, switch_num, host_num):
        Topo.__init__(self)
        self.vertex = {}
        self.graph = {}
        
        # Create graph
        self.graph = nx.barabasi_albert_graph(switch_num, 2)        

        # Create switches
        for n in self.graph.nodes():
            switch_name = 'sw'+str(n+1)
            switch = self.addSwitch(switch_name, protocols='OpenFlow13', dpid=str(n+1))
            
            self.graph.node[n]['name'] = switch_name
            self.vertex[switch_name] = n
        
        # Create servers
        server1 = self.addHost('s1')
        server2 = self.addHost('s2')
        self.addLink(server1, 'sw1', bw=2)
        self.addLink(server2, 'sw2', bw=2)
        self.vertex['s1'] = self.vertex['sw1']
        self.vertex['s2'] = self.vertex['sw2']
        
        # Create hosts
        for h in range(1, host_num+1):
            host_name = 'h'+str(h)
            switch_name = 'sw'+str(randint(1, self.graph.number_of_nodes()))
            host = self.addHost(host_name)
            self.addLink(host, switch_name, bw=2)
            
            self.vertex[host_name] = self.vertex[switch_name]
        
        # Create links between switches
        for e in self.graph.edges():
            link = self.addLink(self.graph.node[e[0]]['name'], self.graph.node[e[1]]['name'], bw=2)

class Network(Mininet):
    "Random network"
    
    def __init__(self, network_size):
        self.switch_num = network_size
        self.server_num = 2
        self.host_num = 3*network_size/2
        self.topo = {}
        
        # Create network
        #setLogLevel('info')
        self.topo = RandomTopo(self.switch_num, self.host_num)
        Mininet.__init__(self, topo=self.topo, controller=None, link=TCLink)
        self.addController('runos0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    def __enter__(self):
        # Start network emulation
        print colored('Network size = '+str(self.switch_num), 'cyan')
        self.start()
        time.sleep(1)
        #CLI(self)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        # Stop network emulation
        print colored('Stop network', 'cyan')
        self.stop()
    
    def _CLI(self):
        CLI(self)
        
    def topo(self):
        return self.topo
    
    def graph(self):
        return self.topo.graph
    
    def vertex(self, vertex_name):
        return self.topo.vertex[vertex_name]
    
    def edge_connectivity(self):
        return nx.edge_connectivity(self.topo.graph)