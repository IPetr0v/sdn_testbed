import logging
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

DEBUG_LOG = False

MULTICAST_VLAN = 405

class MulticastTest(object):
    "Class for multicast tests"
    
    def __init__(self, controller_list, network_list, host_list, group_list, tmp_folder):
        print "Multicast Test"
        self.controller_list = controller_list
        self.network_list = network_list#.sort()
        self.host_list = host_list
        self.group_list = group_list#.sort()
        self.tmp_folder = tmp_folder
    
    def stability_test(self):
        pass
    
    def connection_time_test(self):
        #print colored('Connection time test', 'green')
        print 'Connection time test'
        # Run test
        for network_size in self.network_list:
            for host_num in self.host_list(network_size):
                #raw_input("Restart controller...")
                for controller in self.controller_list:
                    with controller:
                        with Network(controller, network_size, host_num) as network:
                            
                            # Start vlc stream
                            servers = []
                            servers.append(network.getNodeByName('s1'))
                            host_counter = 1
                            for server in servers:
                                host_counter += 1
                                server.cmd('/sbin/vconfig add '+server.name+'-eth0 '+str(MULTICAST_VLAN))
                                server.cmd('ifconfig '+server.name+'-eth0.'+str(MULTICAST_VLAN)+' 10.0.3.'+str(host_counter)+' netmask 255.255.255.0')
                                server.cmd('route add -net 239.255.0.0/16 '+server.name+'-eth0.'+str(MULTICAST_VLAN))
                            for server in servers:
                                server.cmd('./vlc_stream_100.sh &')
                            
                            time.sleep(2)
                            group_time_sum = 0.0
                            for group in self.group_list:
                                if group == 0: group = 1
                                group_time = self._connection_time_test(network, group)
                                group_time_sum += group_time
                                
                                print str(group)+' group time = '+str(group_time)
                            
                            # Stop vlc stream
                            for server in servers:
                                server.cmd('kill $(jobs -p); pkill vlc;')
                            
                            # Get mean group time
                            mean_group_time = 0.0
                            if len(self.group_list)>0:
                                mean_group_time = float(group_time_sum)/float(len(self.group_list))
                            
                            # Print results
                            #print colored('Mean '+str(len(self.group_list))+' group time = '
                            #              +str(mean_group_time), 'green')
                            print 'Mean '+str(len(self.group_list))+' group time = '+str(mean_group_time)                             
    
    def _connection_time_test(self, network, group_num):
        # Get hosts activity
        hosts = []
        servers = []
        for host in network.hosts:
            if host.name != 's1' and host.name != 's2':
                hosts.append(host)
            else:
                servers.append(network.getNodeByName('s1'))#host
                self.activity = MulticastActivity(servers, hosts, group_num, self.tmp_folder)
        
        # Start test
        #print 'Test for '+str(group_num)+' groups'
        self.activity.start()
        if group_num>10:
            time.sleep(1)
        else:
            time.sleep(2)
        #print 'Stop test for '+str(group_num)+' groups'
        # Stop test
        self.activity.stop()
        #time.sleep(1)
        #network._CLI()
        
        # Analyze traffic
        res = {}
        host_time = 0.0
        unaccounted_host_num = 0
        for host in hosts:
            # Save results
            try:
                host_time += self._get_connection_time(host.name)
            except IOError:
                unaccounted_host_num += 1
            
        # Get mean host time
        mean_host_time = 0.0
        if len(hosts)>0: mean_host_time = float(host_time)/float(len(hosts)-unaccounted_host_num)
        if DEBUG_LOG: print "    host_time = ",host_time
        if DEBUG_LOG: print "    len(hosts) = ",len(hosts)
        if DEBUG_LOG: print "    unaccounted_host_num = ",unaccounted_host_num
        return mean_host_time
    
    def _get_connection_time(self, hostname):
        filename = self.tmp_folder+'/'+hostname+'.pcap'
        call('pcapfix '+self.tmp_folder+'/'+hostname+'.pcap > /dev/null 2>&1', shell=True)
        
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
                            if DEBUG_LOG: print "        Request for "+str(p_igmp.gaddr)+" is "+str(p.time)
                        if p_igmp.type == 0x17: # Leave group
                            if DEBUG_LOG: print "        Leave group "+str(p_igmp.gaddr)+" at "+str(p.time)
                
                # Video traffic
                if UDP in p:
                    if IP in p:
                        p_ip = p.getlayer(IP)
                        #print "        UDP for "+str(p_ip.dst)+" at "+str(p.time)
                        if p_ip.dst in igmp_reports and p_ip.dst != '255.255.255.255':
                            connection_time = p.time - igmp_reports[p_ip.dst]
                            if DEBUG_LOG: print "        Connection time for "+str(p_ip.dst)+" is "+str(connection_time)
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
        if DEBUG_LOG: print "    connection_sum = ",connection_sum
        if DEBUG_LOG: print "    float(connection_num) = ",float(connection_num)
        
        return mean_group_time
    
    def reconnection_time_test(self):
        #print colored('Reconnection time test', 'green')
        print 'Reconnection time test'
        # Run test
        for network_size in self.network_list:
            for host_num in self.host_list(network_size):
                #raw_input("Restart controller...")
                for controller in self.controller_list:
                    with controller:
                        with Network(controller, network_size, host_num) as network:
                            #network._CLI()
                            #if network.edge_connectivity() <= 1:
                            #    print colored('Connectivity failure', 'red')
                            #    continue
                            if network_size == 1: continue
                            
                            # Start vlc stream
                            servers = []
                            servers.append(network.getNodeByName('s1'))
                            host_counter = 1
                            for server in servers:
                                host_counter += 1
                                server.cmd('/sbin/vconfig add '+server.name+'-eth0 '+str(MULTICAST_VLAN))
                                server.cmd('ifconfig '+server.name+'-eth0.'+str(MULTICAST_VLAN)+' 10.0.3.'+str(host_counter)+' netmask 255.255.255.0')
                                server.cmd('route add -net 239.255.0.0/16 '+server.name+'-eth0.'+str(MULTICAST_VLAN))
                            for server in servers:
                                server.cmd('./vlc_stream_100.sh &')
                            
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
                            
                            # Stop vlc stream
                            for server in servers:
                                server.cmd('kill $(jobs -p); pkill vlc;')
                            
                            # Print results
                            #print colored('Mean '+str(len(self.group_list))+' group time = '
                            #              +str(mean_group_time), 'green')
                            print 'Mean '+str(len(self.group_list))+' group time = '+str(mean_group_time)
    
    def _reconnection_time_test(self, controller, network, group_num):
        # Get hosts activity
        hosts = []
        servers = []
        servers.append(network.getNodeByName('s1'))#host
        for host in network.hosts:
            if host.name != 's1' and host.name != 's2':
                hosts.append(host)
        self.multicast_activity = MulticastActivity(servers, hosts, group_num, self.tmp_folder)
        self.unicast_activity = UnicastActivity(controller, network, hosts)
        
        # Start test
        #self.unicast_activity.start()
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
            #if DEBUG_LOG: print colored('Link down: '+sw1+' <-> '+sw2, 'red')
            network.configLinkStatus(sw1, sw2, 'down')
            #network.delLinkBetween(sw1, sw2)
            time.sleep(1)
            #if DEBUG_LOG: print colored('Link up: '+sw1+' <-> '+sw2, 'blue')
            network.configLinkStatus(sw1, sw2, 'up')
            #network.addLink(sw1, sw2)
        
        # Create switch failures
        
        # Stop test
        self.multicast_activity.stop()
        #self.unicast_activity.stop()
        time.sleep(1)
        
        # Analyze traffic
        res = {}
        host_time = 0.0
        unaccounted_host_num = 0
        for host in hosts:
            # Save results
            try:
                host_time += self._get_reconnection_time(host.name)
            except IOError:
                unaccounted_host_num += 1
            
        # Get mean host time
        mean_host_time = 0.0
        if len(hosts)>0: mean_host_time = float(host_time)/float(len(hosts)-unaccounted_host_num)
        return mean_host_time
    
    def _get_reconnection_time(self, hostname):
        filename = self.tmp_folder+'/'+hostname+'.pcap'
        call('pcapfix '+self.tmp_folder+'/'+hostname+'.pcap > /dev/null 2>&1', shell=True)
        
        # Analyze the pcap file
        prev_time = {}
        max_delta_time = {}
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
                        
                        # Get max delta time for the address
                        if p_ip.dst in prev_time and p_ip.dst in igmp_reports and p_ip.dst != '255.255.255.255':
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
            #if DEBUG_LOG: print "Max delta time for "+str(ip)+" is "+str(max_delta_time[ip])      
        
        mean_delta_time = 0.0
        if len(max_delta_time)>0: mean_delta_time = float(delta_time_sum)/float(len(max_delta_time))
        
        return mean_delta_time