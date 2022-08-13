import zmq
from yaml import safe_load, dump, load, FullLoader
from nested_lookup import nested_update, nested_delete
from itertools import chain
import sys
import time

# generic send routine
def send(cmd, cfg=""):
    socket.send(cmd.encode())
    status = socket.recv_string()
    if status == 'READY':
        socket.send_string(cfg)
        answer = str(socket.recv_string())
        return(answer)
    else:
        return(status)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

# initialise ROCs.
#with open('./configs/init_single.yaml') as fin:
with open('./configs/init.yaml') as fin:
    cfg = safe_load(fin)
    cfg_str = dump(cfg)
ret = send("initialize", cfg_str)
cfgs = safe_load(ret)

with open('./configs/scan_pedDAC.yaml') as fin:
    conf_yaml = safe_load(fin)
    for ped_val in range(32):
        nested_update(conf_yaml, key="Ref_dac_inv",
                      value=ped_val, in_place=True)
        cfg_str = dump(conf_yaml)
        send("configure", cfg_str)

print("\n --- READ: --- \n")
#cfg_str = dump({"roc_s2":{"ReferenceVoltage":{"all":{"IntCtest":0, "ExtCtest":0, "Calib_dac":0}}}})
#ret = send("read", cfg_str)
#ret = send("resetTDC")
#print(ret)
ret = send("read")
cfgs = safe_load(ret)
print(cfgs)
#print(dump(cfgs, default_flow_style=False))
print("---")

'''
from pprint import pprint
# initialise ROCs: ADC pwr measurement
with open('./configs/scan_adc_calibdac.yaml') as fin:
    conf_yaml = safe_load(fin)
    for dac_val in range(0, 1000, 100):
        nested_update(conf_yaml, key="Calib_dac", value=dac_val, in_place=True)
        cfg_str = dump(conf_yaml)
        ret = send("measadc", cfg_str)
        pprint(safe_load(ret))

# ADC probeDC measurement
dc1 = ["Vbi_pa", "Vbm_pa", "Vbm2_pa", "Vbm3_pa", "Vbo_pa", "Vb_inputdac",
        "Vbi_discri_tot", "Vbm_discri_tot", "Vbo_discri_tot", "Vref_pa",
        "Vcp", "VD_FTDC_N_EXT", "VD_CTDC_N_EXT"]
dc1range = list(chain(range(1,10), range(12,16)))

#print("Half {0:16} roc_s0 roc_s1 roc_s2".format("Probe_dc1"))
with open('./configs/scan_adc_dc1.yaml') as fin:
    conf_yaml = safe_load(fin)
    for adc_code, name in zip(dc1range, dc1):
        nested_update(conf_yaml, key="Probe_dc1", value=adc_code, in_place=True)
        cfg_str = dump(conf_yaml)
        ret = send("measadc", cfg_str)
        cfgs = safe_load(ret)
        print(name)
        pprint(cfgs)

dc2 = ["Vbi_discri_toa", "Vcasc_discri_toa", "Vbm1_discri_toa", "Vbm2_discri_toa",
        "Vbo_discri_toa", "EXT_REF_TDC", "VrefCf", "Vcn", "VD_FTDC_P_EXT", "VD_CTDC_P_EXT"]
dc2range = list(chain(range(1,7), range(12,16)))
#print("Half {0:16} roc_s0 roc_s1 roc_s2".format("Probe_dc2"))
with open('./configs/scan_adc_dc2.yaml') as fin:
    conf_yaml = safe_load(fin)
    for adc_code, name in zip(dc1range, dc1):
        nested_update(conf_yaml, key="Probe_dc2", value=adc_code, in_place=True)
        cfg_str = dump(conf_yaml)
        ret = send("measadc", cfg_str)
        cfgs = safe_load(ret)
        print(name)
        pprint(cfgs)

# pedestal scan
with open('./configs/scan_pedDAC.yaml') as fin:
    conf_yaml = safe_load(fin)
    for _ in range(5):
        for ped_val in range(32):
            nested_update(conf_yaml, key="Ref_dac_inv",
                          value=ped_val, in_place=True)
            cfg_str = dump(conf_yaml)
            send("configure", cfg_str)


# pedestal scan
#with open('./configs/scan_pedDAC_single.yaml') as fin:
with open('./configs/scan_pedDAC.yaml') as fin:
    conf_yaml = safe_load(fin)
    for ped_val in range(32):
        nested_update(conf_yaml, key="Ref_dac_inv",
                      value=ped_val, in_place=True)
        cfg_str = dump(conf_yaml)
        send("configure", cfg_str)

# sampling scan
with open('./configs/config_samplingscan.yaml') as fin:
    conf_yaml = safe_load(fin)
    for ped_val in range(0, 2050, 50):
        nested_update(conf_yaml, key="Ref_dac_inv",
                      value=ped_val, in_place=True)
        cfg_str = dump(conf_yaml)
        send("configure", cfg_str)

print("\n --- READ: --- \n")
#cfg_str = dump({"roc_s2":{"ReferenceVoltage":{"all":{"IntCtest":0, "ExtCtest":0, "Calib_dac":0}}}})
#ret = send("read", cfg_str)
#ret = send("resetTDC")
#print(ret)
ret = send("read")
cfgs = safe_load(ret)
print(dump(cfgs, default_flow_style=False))
print("---")
'''
