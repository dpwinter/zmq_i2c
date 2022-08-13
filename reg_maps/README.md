# SlowControls configuration of ROCs via ZMQ & I2C

## Download & install requirements

```bash 
git clone https://gitlab.cern.ch/hgcal-daq-sw/zmq_i2c.git
cd zmq_i2c
pip3 install -r requirements.txt
```
This installs all necessary requirements on the HexaController.

### Run server on HexaController
```bash
python3 ./zmq_server.py
```
Run server on the HexaController.

### Run client either on HexaController or other machine
```bash
python3 ./zmq_client.py
```
Start client either locally on HexaController or on another machine (in same network). For the latter, adjust *IP address/port* on the client and *port* on the server, if necessary.

