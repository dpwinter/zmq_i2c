# zmq_i2c
> Object-oriented I2C Driver for configuration of custom readout chips via ZMQ protocol

This software includes client-server scripts to allow sending user-defined yaml-configuration files to a control board (running the server script) which afterwards converts the human readable config data to machine data (i.e. register value and addresses) to configure customly-designed readout chips. The driver implements not only the means to do the conversion but also introduces caches and other mechanisms to avoid redundant chip I/O as well as I/O error correction mechanisms to establish a fast and reliable configuration link to the chips. This software has been used in several chip testing sessions (see my Bachelor thesis repository) and will probably be extended and used in the future to configure thousands of chips for testing in assembly centers.

### Install on Controller Board (HexaController)

```bash 
git clone https://gitlab.cern.ch/hgcal-daq-sw/zmq_i2c.git
cd zmq_i2c
pip3 install -r requirements.txt
```

### Start server on Controller Board (HexaController)

```bash
python3 ./zmq_server.py
```

### Run client script on any remote machine

```bash
python3 ./zmq_client.py
```

Adjust *IP address/port* on the client and *port* on the server, if necessary. This allows to send specific configuration yaml-files from remote PC to Controller board via TCP (i.e. ethernet) which in turn configures the readout chips and returns once done.
