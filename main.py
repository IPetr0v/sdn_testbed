#!/usr/bin/env python

from subprocess import call

from sdntestbed.controller import Runos
from sdntestbed.test import MulticastTest

if __name__ == '__main__':
    
    call('mkdir .tmp > /dev/null 2>&1', shell=True)
    
    controller_list = [Runos("127.0.0.1","8080", ssh="root@127.0.0.1")]
    network_list = xrange(1,26,5) #[1, 5, 10, 15, 20, 25]
    host_list = lambda netsize: [netsize/2+1] #range(1,netsize+1,netsize/10 if netsize/10!=0 else 1) #[1]
    group_list = xrange(1,11,1)#xrange(0,105,5) #[1,10,50,130,250]
    
    test = MulticastTest(controller_list, network_list, host_list, group_list, tmp_folder="/tmp")
    
    test.connection_time_test()
    test.reconnection_time_test()
    
    call('rm -rf .tmp/ > /dev/null 2>&1', shell=True)
    
