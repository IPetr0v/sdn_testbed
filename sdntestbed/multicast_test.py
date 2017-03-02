import logging
import matplotlib.pyplot as plt
import time

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import rdpcap
from scapy.all import sniff
from scapy.all import IP
from scapy.all import UDP
from scapy.contrib.igmp import IGMP
from scapy.error import Scapy_Exception
from random import choice
from random import randint
from subprocess import call
from termcolor import colored

from activity import MulticastActivity
from activity import UnicastActivity
from network import Network

DEBUG_LOG = True

class MulticastTest(object):
    "Class for multicast tests"
    
    def __init__(self, controller_list, network_list, group_list):
        print "Multicast Test"
        self.controller_list = controller_list
        self.network_list = network_list#.sort()
        self.group_list = group_list#.sort()
    
    def stability_test(self):
        pass
    
    def connection_time_test(self):
        print colored('Connection time test', 'green') 
        # Run test
        #for controller in controller_list:
        #    with controller:
        for network_size in self.network_list:
            with Network(network_size=network_size) as network:
                print colored('Network size = '+str(network_size), 'cyan')
                
                group_time_sum = 0.0
                for group in self.group_list:
                    if group == 0: group = 1
                    group_time = self._connection_time_test(network, group)
                    group_time_sum += group_time
                    
                    print str(group)+' group time = '+str(group_time)
                
                # Get mean group time
                mean_group_time = 0.0
                if len(self.group_list)>0:
                    mean_group_time = float(group_time_sum)/float(len(self.group_list))
                
                # Print results
                print colored('Mean '+str(len(self.group_list))+' group time = '
                              +str(mean_group_time), 'green')                        
    
    def _connection_time_test(self, network, group_num):
        # Get hosts activity
        hosts = []
        servers = []
        for host in network.hosts:
            if host.name != 's1' and host.name != 's2':
                hosts.append(host)
            else:
                servers.append(network.getNodeByName('s1'))#host
                self.activity = MulticastActivity(servers, hosts, group_num)
        
        # Start test
        #if DEBUG_LOG: print colored('Test for '+str(group_num)+' groups', 'green')
        self.activity.start()
        time.sleep(2)
        
        # Stop test
        self.activity.stop()
        time.sleep(2)
        
        # Analyze traffic
        res = {}
        host_time = 0.0
        for host in hosts:
            # Save results
            host_time += self._get_connection_time(host.name)
            
        # Get mean host time
        mean_host_time = 0.0
        if len(hosts)>0: mean_host_time = float(host_time)/float(len(hosts))
        return mean_host_time
    
    def _get_connection_time(self, hostname):
        filename = '../.tmp/'+hostname+'.pcap'
        call('pcapfix ../.tmp/'+hostname+'.pcap > /dev/null 2>&1', shell=True)
        
        # Analyze the pcap file
        res = {}
        connection_sum = 0
        connection_num = 0
        igmp_reports = {}
        for p in rdpcap(filename):
            try:
                if IP in p:
                    # Group report
                    if IGMP in p:
                        p_igmp = p.getlayer(IGMP)
                        if p_igmp.type == 0x16: # Membership report
                            igmp_reports[p_igmp.gaddr] = p.time
                
                # Video traffic
                if UDP in p:
                    if IP in p:
                        p_ip = p.getlayer(IP)
                        if p_ip.dst in igmp_reports and p_ip.dst != '255.255.255.255':
                            connection_time = p.time - igmp_reports[p_ip.dst]
                            #if DEBUG_LOG: print "Connection time for "+str(p_ip.dst)+" is "+str(connection_time)
                            del igmp_reports[p_ip.dst]
                            connection_num += 1
                            connection_sum += connection_time
                            
                            # Save results
                            res[p_ip.dst] = connection_time
            
            except Scapy_Exception as ex:
                print "Filename = "+filename+" | ", ex            
        
        # Get mean time
        mean_group_time = 0.0
        if connection_num>0: mean_group_time = float(connection_sum)/float(connection_num)
        
        return mean_group_time
    
    def reconnection_time_test(self):
        print colored('Reconnection time test', 'green') 
        # Run test
        for controller in self.controller_list:
            with controller:
                for network_size in self.network_list:
                    with Network(network_size=network_size) as network:
                        #network._CLI()
                        #if network.edge_connectivity() <= 1:
                        #    print colored('Connectivity failure', 'red')
                        #    continue
                        
                        group_time_sum = 0.0
                        for group in self.group_list:
                            if group == 0: group = 1
                            group_time = self._reconnection_time_test(controller, network, group)
                            group_time_sum += group_time
                            
                            print str(group)+' group time = '+str(group_time)
                        
                        # Get mean group time
                        mean_group_time = 0.0
                        if len(self.group_list)>0:
                            mean_group_time = float(group_time_sum)/float(len(self.group_list))
                        
                        # Print results
                        print colored('Mean '+str(len(self.group_list))+' group time = '
                                      +str(mean_group_time), 'green')
    
    def _reconnection_time_test(self, controller, network, group_num):
        # Get hosts activity
        hosts = []
        servers = []
        servers.append(network.getNodeByName('s1'))#host
        for host in network.hosts:
            if host.name != 's1' and host.name != 's2':
                hosts.append(host)
        self.multicast_activity = MulticastActivity(servers, hosts, group_num)
        self.unicast_activity = UnicastActivity(controller, network, hosts)
        
        # Start test
        self.unicast_activity.start()
        self.multicast_activity.start()
        #raw_input("Press Enter to continue...")
        #network._CLI()
        time.sleep(1)
        
        # Create link failures
        for num in range(1,10):
            src_node = choice(network.graph().nodes())
            dst_node = choice(network.graph().neighbors(src_node))
            
            sw1 = network.graph().node[src_node]['name']
            sw2 = network.graph().node[dst_node]['name']
            if sw1 == sw2: continue
            
            # Link failure
            if DEBUG_LOG: print colored('Link down: '+sw1+' <-> '+sw2, 'red')
            network.configLinkStatus(sw1, sw2, 'down')
            #network.delLinkBetween(sw1, sw2)
            time.sleep(1)
            if DEBUG_LOG: print colored('Link up: '+sw1+' <-> '+sw2, 'blue')
            network.configLinkStatus(sw1, sw2, 'up')
            #network.addLink(sw1, sw2)
        
        # Create switch failures
        
        # Stop test
        self.multicast_activity.stop()
        self.unicast_activity.stop()
        time.sleep(1)
        
        # Analyze traffic
        res = {}
        host_time = 0.0
        for host in hosts:
            # Save results
            host_time += self._get_reconnection_time(host.name)
            
        # Get mean host time
        mean_host_time = 0.0
        if len(hosts)>0: mean_host_time = float(host_time)/float(len(hosts))
        return mean_host_time
    
    def _get_reconnection_time(self, hostname):
        filename = '../.tmp/'+hostname+'.pcap'
        call('pcapfix ../.tmp/'+hostname+'.pcap > /dev/null 2>&1', shell=True)
        
        # Analyze the pcap file
        prev_time = {}
        max_delta_time = {}
        for p in rdpcap(filename):
            try:
                # Video traffic
                if UDP in p:
                    if IP in p:
                        p_ip = p.getlayer(IP)
                                              
                        # Get max delta time for the address
                        if p_ip.dst in prev_time and p_ip.dst != '255.255.255.255':
                            delta_time = p.time - prev_time[p_ip.dst]
                            if p_ip.dst in max_delta_time:
                                if max_delta_time[p_ip.dst] < delta_time:
                                    max_delta_time[p_ip.dst] = delta_time
                            else:
                                max_delta_time[p_ip.dst] = delta_time
                        
                        # Save previous time for the address
                        prev_time[p_ip.dst] = p.time
            
            except Scapy_Exception as ex:
                print "Filename = "+filename+" | ", ex            
        
        # Get mean time
        delta_time_sum = 0.0
        for ip in max_delta_time:
            delta_time_sum += max_delta_time[ip]
            if DEBUG_LOG: print "Max delta time for "+str(ip)+" is "+str(max_delta_time[ip])      
        
        mean_delta_time = 0.0
        if len(max_delta_time)>0: mean_delta_time = float(delta_time_sum)/float(len(max_delta_time))
        
        return mean_delta_time