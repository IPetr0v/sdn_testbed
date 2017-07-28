import time
from random import choice
from random import randint
from subprocess import call

MULTICAST_VLAN = 405

class Activity(object):
    def __init__(self): pass
    def start_activity(self): pass
    def stop_activity(self): pass

class UnicastActivity(Activity):
    def __init__(self, controller, network, hosts, host_pairs=None):
        self.controller = controller
        self.network = network
        self.hosts = list(hosts)
        self.host_pairs = {}
        self.host_ip = {}
        
        # Create host pairs
        if host_pairs != None:
            self.host_pairs = host_pairs
        else:
            # Partice hosts by pairs (if host number is odd then discard one host)
            tmp_hosts = self.hosts
            while len(tmp_hosts)>1:
                host1_num = randint(0, len(tmp_hosts)-1)
                host1 = tmp_hosts[host1_num]
                del tmp_hosts[host1_num]
                
                host2_num = randint(0, len(tmp_hosts)-1)
                host2 = tmp_hosts[host2_num]
                del tmp_hosts[host2_num]
                
                self.host_pairs[host1] = host2
        
        # Set routes
        vlan = 1;
        host_counter = 1;
        for host1 in self.host_pairs:
            if len(host1.intfList())>0:
                host2 = self.host_pairs[host1]
    
                # Create route by controller
                sw1 = host1.intfList()[0].link.intf2.node
                dpid1 = sw1.dpid
                port1 = self.network.topo.port(host1.name, sw1.name)[1]
                
                sw2 = host2.intfList()[0].link.intf2.node
                dpid2 = sw2.dpid
                port2 = self.network.topo.port(host2.name, sw2.name)[1]
    
                self.controller.set_route(dpid1, port1, dpid2, port2, vlan)
                #print "host_pairs["+host1.name+"] = "+host2.name
                #print "set_route("+dpid1.lstrip("0")+":"+str(port1)+" <-> "+dpid2.lstrip("0")+":"+str(port2)+", vlan="+str(vlan)
                
                # Save ip
                host1_ip = host1.intfList()[0].ip
                host2_ip = host2.intfList()[0].ip
                self.host_ip[host1.name] = '10.0.1.'+str(host_counter)
                self.host_ip[host2.name] = '10.0.1.'+str(host_counter+1)
    
                # Set vlan
                host1.cmd('/sbin/vconfig add '+host1.name+'-eth0 '+str(vlan))
                host1.cmd('ifconfig '+host1.name+'-eth0.'+str(vlan)+' '+self.host_ip[host1.name]+' netmask 255.255.255.0')
                host1.cmd('ifconfig '+host1.name+'-eth0 '+host1_ip+' netmask 255.255.255.0')
                #host1.cmd('route add -net 10.0.1.0/24 '+host1.name+'-eth0.'+str(vlan))
                
                host2.cmd('/sbin/vconfig add '+host2.name+'-eth0 '+str(vlan))
                host2.cmd('ifconfig '+host2.name+'-eth0.'+str(vlan)+' '+self.host_ip[host2.name]+' netmask 255.255.255.0')
                host2.cmd('ifconfig '+host2.name+'-eth0 '+host2_ip+' netmask 255.255.255.0')
                #host2.cmd('route add -net 10.0.1.0/24 '+host2.name+'-eth0.'+str(vlan))
                
                vlan += 1
                if vlan == MULTICAST_VLAN: vlan += 1
                host_counter += 2
            
    def start(self):
        # Start performance test
        #call("rm ../.tmp/*.pcap > /dev/null 2>&1", shell=True)
        
        for host1 in self.host_pairs:
            host2 = self.host_pairs[host1]

            bandwidth = 1 # Mbit/s
            
            #print host2.name, 'iperf3 -s -B '+self.host_ip[host2.name]+' -i 1'
            #print host1.name, 'iperf3 -c '+self.host_ip[host2.name]+' -u -b '+str(bandwidth*1000000)+' -i 1 -t 60'
            #host1.cmd('sudo tcpdump -i '+host1.name+'-eth0 -U -w azaza.pcap &')
            
            host2.cmd('iperf3 -s -B '+self.host_ip[host2.name]+' -i 1 &')
            host1.cmd('iperf3 -c '+self.host_ip[host2.name]+' -u -b '+str(bandwidth*1000000)+' -i 1 -t 60 &')            
            #host2.cmd('xterm -e "iperf3 -s -B '+self.host_ip[host2.name]+' -i 1" &')
            #host1.cmd('xterm -e "iperf3 -c '+self.host_ip[host2.name]+' -u -b '+str(bandwidth*1000000)+' -i 1 -t 60" &')
    
    def stop(self):
        for host in self.hosts: 
            host.cmd('kill $(jobs -p)')
        
        self.controller.clear_routes()

class MulticastActivity(Activity):
    def __init__(self, servers, hosts, group_num, tmp_folder, save_pcap=True):
        self.hosts = list(hosts)
        self.servers = list(servers)
        self.group_num = group_num
        self.save_pcap = save_pcap
        self.tmp_folder = tmp_folder
    
    def start(self):
        #print "Multicast activity"
        # Host startup scripts
        #print "Host number", len(self.hosts)
        host_counter = 1;
        for server in self.servers:
            host_counter += 1
            '''server.cmd('/sbin/vconfig add '+server.name+'-eth0 '+str(MULTICAST_VLAN))
            server.cmd('ifconfig '+server.name+'-eth0.'+str(MULTICAST_VLAN)+' 10.0.3.'+str(host_counter)+' netmask 255.255.255.0')
            server.cmd('route add -net 239.255.0.0/16 '+server.name+'-eth0.'+str(MULTICAST_VLAN))''' 
        for host in self.hosts:
            host_counter += 1
            host.cmd('/sbin/vconfig add '+host.name+'-eth0 '+str(MULTICAST_VLAN))
            host.cmd('ifconfig '+host.name+'-eth0.'+str(MULTICAST_VLAN)+' 10.0.3.'+str(host_counter)+' netmask 255.255.255.0')
            host.cmd('route add -net 239.255.0.0/16 '+host.name+'-eth0.'+str(MULTICAST_VLAN))
        
        # Save pcap
        call("rm "+self.tmp_folder+"/*.pcap > /dev/null 2>&1", shell=True)
        for host in self.hosts:
            host.cmd('sudo tcpdump -i '+host.name+'-eth0 -U -w '+self.tmp_folder+'/'+host.name+'.pcap &') # filter can be = host 239.255.0.1
            #host.cmd('sudo tcpdump -i any -U -w '+self.tmp_folder+'/ololo.pcap &')
    
        # Force IGMPv2 for iperf
        for server in self.servers:
            server.cmd('echo "2" > /proc/sys/net/ipv4/conf/'+server.name+'-eth0.'+str(MULTICAST_VLAN)+'/force_igmp_version')
        for host in self.hosts:
            host.cmd('echo "2" > /proc/sys/net/ipv4/conf/'+host.name+'-eth0.'+str(MULTICAST_VLAN)+'/force_igmp_version')
    
        # Start performance test
        bandwidth = 0
        if len(self.hosts)>0: bandwidth = int((1*1000)/len(self.hosts)) #bit/s
        for i in range(1,self.group_num+1):
            for host in self.hosts:
                #host.cmd('iperf -s -u -B 239.255.0.'+str(i)+' -i 1 &')
                #host.cmd('iperf -s -u -B 239.255.0.'+str(i)+' -i 1 &')
                leave_message = ('python -c \"from scapy.all import Ether, Dot1Q, IP, sendp; '
                                'from scapy.contrib.igmp import IGMP; '
                                'from scapy.arch import get_if_hwaddr; '
                                'sendp(Ether(src=get_if_hwaddr(\''+host.name+'-eth0.'+str(MULTICAST_VLAN)+'\'))/IP(dst=\'239.255.0.'+str(i)+'\')/IGMP(type=0x16, gaddr=\'239.255.0.'+str(i)+'\'), '
                                'iface=\''+host.name+'-eth0.'+str(MULTICAST_VLAN)+'\')\" ')
                host.cmd(leave_message)
                
        '''for i in range(1,self.group_num+1):
            for server in self.servers:
                #server.cmd('iperf -c 239.255.0.'+str(i)+' -u -b '+str(bandwidth)+' -i 1 -t 60 &')
                server.cmd('iperf -c 239.255.0.'+str(i)+' -u -i 1 -t 60 &')'''
    
    def stop(self):
        for i in range(1,self.group_num+1):
            for host in self.hosts:
                leave_message = ('python -c \"from scapy.all import Ether, Dot1Q, IP, sendp; '
                                'from scapy.contrib.igmp import IGMP; '
                                'from scapy.arch import get_if_hwaddr; '
                                'sendp(Ether(src=get_if_hwaddr(\''+host.name+'-eth0.'+str(MULTICAST_VLAN)+'\'))/IP(dst=\'239.255.0.'+str(i)+'\')/IGMP(type=0x17, gaddr=\'239.255.0.'+str(i)+'\'), ' #Dot1Q(vlan='+str(MULTICAST_VLAN)+')/
                                'iface=\''+host.name+'-eth0.'+str(MULTICAST_VLAN)+'\')\" ')
                #print leave_message
                host.cmd(leave_message)
        #time.sleep(1)
        '''for server in self.servers:
            server.cmd('kill $(jobs -p); pkill iperf; pkill tcpdump;')'''
        for host in self.hosts: 
            host.cmd('kill $(jobs -p); pkill iperf; pkill tcpdump;')
        