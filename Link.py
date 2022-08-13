from smbus2 import SMBus
import gpiod

class LinkBuilder:
    @staticmethod
    def create(sc_type='xil'):
        assert(sc_type in ['xil','sca'])
        if sc_type == 'xil': 
            i2cs = xil_i2c_discover()
            gpios = xil_gpio_discover()
        elif sc_type == 'sca': 
            i2cs = []
            gpios = []


        links = {}
        for gpio_name, gpio in gpios.items():
            for i2c_name, i2c in i2cs.items():
                if gpio_name in i2c_name:
                    links[i2c_name] = Link(i2c, gpio)
        return links

class Link:
    def __init__(self, i2c, gpio):
        self.i2c = i2c
        self.gpio = gpio

class i2c():
    def __init__(self, addr, bus):
        self._addr = addr
        self._bus = bus

    def write(self, *args, **kwargs):
        raise NotImplementedError

    def read(self, *args, **kwargs):
        raise NotImplementedError

class sca_i2c(i2c):
    pass

def sca_i2c_discover():
    pass

class xil_i2c(i2c):
    def write(self, offset, byte):
        with SMBus(self._bus) as bus:
            bus.write_byte(self._addr + offset, byte)
        return None

    def read(self, offset):
        with SMBus(self._bus) as bus:
            ret = bus.read_byte(self._addr + offset)
        return ret

i2c_char_map = {0x28: 'roc_s0'}
i2c_ld_map = {0x00: 'roc_s0', 0x40: 'roc_s1', 0x20: 'roc_s2'}
i2c_hd_map = {0x18: 'roc_s0_0', 0x30: 'roc_s0_1', 0x08: 'roc_s1_0', 0x20: 'roc_s1_1', 0x10: 'roc_s2_0', 0x28: 'roc_s2_1'}

def xil_i2c_discover():
    """ Discover all ROCs on i2c """

    rocs = []
    for bus_id in range(8):  # 8 i2c bus lines
        try:
            with SMBus(bus_id) as bus:
                addrs = []
                for addr in range(128):  # 128 addrs per bus line
                    try:
                        bus.read_byte(addr)
                        addrs.append(addr)
                    except IOError as e: 
                        pass # skip non-existing addr
                print('[I2C] Found %d address(es) on bus %d' % (len(addrs),bus_id))
                if len(addrs) >= 8: 
                    rocs.append((addrs[0], bus_id))
                if len(addrs) == 16:
                    rocs.append((addrs[8], bus_id))
        except FileNotFoundError:
            pass  # skip undefined i2c busses
    return xil_i2c_create(rocs)

def xil_i2c_create(rocs):
    """ Detect board type & create i2c objects """

    n = len(rocs)
    if n == 1:   
        print('[I2C] Identified Single-Chip (Char) board')
        roc_map = i2c_char_map
    elif n == 3: 
        print('[I2C] Identified LD HexaBoard')
        roc_map = i2c_ld_map
    elif n == 6: 
        print('[I2C] Identified HD HexaBoard')
        roc_map = i2c_hd_map
    return {roc_map[addr]:xil_i2c(addr,bus) for (addr, bus) in rocs}

class gpio():
    def __init__(self, lines):
        self._lines = lines

    def write(self, *args, **kwargs):
        raise NotImplementedError
    
    def read(self, *args, **kwargs):
        raise NotImplementedError

class sca_gpio(gpio):
    pass

def sca_gpio_discover():
    pass

class xil_gpio(gpio):

    def write(self, val):
        for line in self._lines:
            config = gpiod.line_request()
            config.consumer = "xil_gpio_write"
            config.request_type = gpiod.line_request.DIRECTION_OUTPUT
            line.request(config)
            line.set_value(val)
            line.release()

    def read(self):
        ans = {}
        for line in self._lines:
            config = gpiod.line_request()
            config.consumer = "xil_gpio_read"
            config.request_type = gpiod.line_request.DIRECTION_INPUT
            line.request(config)
            ans[line.name] = line.get_value()
        return ans

gpio_char_map = {'roc_s0': ['hgcroc_rstB', 'resyncload', 'hgcroc_i2c_rstB']}
gpio_hexa_map = {'roc_s0': ['s0_resetn', 's0_resyncload', 's0_i2c_rstn'], 
                 'roc_s1': ['s1_resetn', 's1_resyncload', 's1_i2c_rstn'], 
                 'roc_s2': ['s2_resetn', 's2_resyncload', 's2_i2c_rstn']}

def xil_gpio_discover():
    # get all lines on all connected gpio chips
    lines = []
    for chip in gpiod.chip_iter():
        for line in gpiod.line_iter(chip):
            lines.append(line)

    # check if line names are in char map
    sel_names = set(gpio_char_map['roc_s0']).intersection([l.name for l in lines])
    if sel_names:
        return {'roc_s0': xil_gpio([l for l in lines if l.name in sel_names])}
    else:
        ret = {}
        # check if line names in hexa map
        for roc, line_names in gpio_hexa_map.items():
            sel_names = set(line_names).intersection([l.name for l in lines])
            if sel_names:
                ret[roc] = xil_gpio([l for l in lines if l.name in sel_names])
        if ret: return ret
        else: raise('Missing HexaBoard GPIO lines.')
