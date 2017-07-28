# SDN testbed

Library for SDN tests automatization

## Installation

### Install python dependencies
```
sudo apt-get install curl
sudo apt-get install libcurl4-openssl-dev libssl-dev
```

### Install python packages
```
pip install networkx
pip install pycurl
pip install termcolor
```

### Install scapy
```
git clone https://github.com/levigross/Scapy.git
cd Scapy
sudo python setup.py install
```

### Install mininet
```
git clone git://github.com/mininet/mininet
cd mininet
git tag  # list available versions
git checkout -b 2.2.1 2.2.1  # or whatever version you wish to install
cd ..
mininet/util/install.sh -nfv
```

### Run OVS
```
/usr/local/share/openvswitch/scripts/ovs-ctl stop

ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
    --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
    --pidfile --detach --log-file

ovs-vsctl --no-wait init

ovs-vswitchd -v --pidfile --detach \
 --log-file \
 -vconsole:err -vsyslog:info -vfile:info

/sbin/modprobe openvswitch
```

## Usage
```
sudo python main.py
```

