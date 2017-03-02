# SDN testbed

Library for SDN tests automatization

## Installation

### Install python dependencies
```
sudo apt-get install curl
sudo apt-get install libcurl4-openssl-dev libssl-dev
pip install pycurl
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

## Usage
```
sudo python main.py
```

