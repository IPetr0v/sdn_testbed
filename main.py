#!/usr/bin/env python

from subprocess import call

from sdntestbed.controller import Runos
from sdntestbed.multicast_test import MulticastTest

if __name__ == '__main__':
    
    call('mkdir .tmp > /dev/null 2>&1', shell=True)
    
    network_list = [12]
    group_list = xrange(0,1050,50)#[1,10,50,130,250]
    #MulticastTest(network_list, group_list).connection_time_test()
    
    controller_list = [Runos("10.30.40.69","8080")]
    #group_list = [1]
    network_list = [10, 15, 20]
    group_list = [1]
    MulticastTest(controller_list, network_list, group_list).reconnection_time_test()
    
    call('rm -rf .tmp/ > /dev/null 2>&1', shell=True)
    
