import json
import pycurl

from subprocess import call
from paramiko import SSHClient

class Controller(object):
    
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
    
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
    
    def start(self):
        pass
    
    def stop(self):
        pass

class Runos(Controller):
    
    def __init__(self, ip, port, ssh):
        Controller.__init__(self, name="runos", ip=ip, port=port)
        self.ssh = ssh
        
        self.routes = []
    
    def start(self):
        Controller.start(self)
    
    def stop(self):
        call(["ssh", self.ssh, "pkill runos"]);       
        Controller.stop(self)
    
    def set_route(self, dpid1, port1, dpid2, port2, vlan):
        dname = "Domain-"+str(vlan)
        self.routes.append(dname)
        data = self._bridge_domain(dtype="P2P", dname=dname,
                                   dpid1=dpid1, port1=port1,
                                   dpid2=dpid2, port2=port2,
                                   vlan=vlan)
        
        request = pycurl.Curl()
        request.setopt(pycurl.URL, str(self.ip)+':'+str(self.port)+'/bridge_domains/')
        request.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json', 'Accept: application/json'])
        #request.setopt(pycurl.HTTPPOST, send)
        request.setopt(pycurl.CUSTOMREQUEST, "PUT")
        request.setopt(pycurl.POSTFIELDS, data)
        #request.setopt(pycurl.VERBOSE, 0)
        request.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        request.perform()
        #print request.getinfo(pycurl.RESPONSE_CODE)
        request.close()
    
    def del_route(self, dname):
        request = pycurl.Curl()
        request.setopt(pycurl.URL, str(self.ip)+':'+str(self.port)+'/bridge_domains/'+str(dname)+'/')
        request.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json', 'Accept: application/json'])  
        request.setopt(pycurl.CUSTOMREQUEST, "DELETE") 
        #request.setopt(pycurl.VERBOSE, 0)  
        request.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        request.perform()
        #print request.getinfo(pycurl.RESPONSE_CODE)
        request.close() 
    
    def clear_routes(self):
        for dname in self.routes:
            self.del_route(dname)
        self.routes = []
    
    def _bridge_domain(self, dtype, dname, dpid1, port1, dpid2, port2, vlan):
        #"isSelected": "true"
        return json.dumps({
            "type": dtype,
            "name": dname,
            "metrics": "Hop",
            "sw": [
                {
                    "dpid": dpid1.lstrip("0"),
                    "ports": [
                        {
                            "port_num": port1,
                            "stag": vlan
                        }
                    ]
                },
                {
                    "dpid": dpid2.lstrip("0"),
                    "ports": [
                        {
                            "port_num": port2,
                            "stag": vlan
                        }
                    ]
                }
            ],
            "flapping": "0"
        })

class Ryu(Controller):
    
    def __init__(self, ip, port):
        Controller.__init__(self, name="ryu", ip=ip, port=port)
    
