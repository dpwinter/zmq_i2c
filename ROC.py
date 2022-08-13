class ROC(object):
    """ Interface to ROC on register-level. """

    def __init__(self, link):
        self.prev_addr = (None, None)
        self.link = link

    def read(self, sortedPairs):
        """ Read/Burst-Read addresses in addr:val pairs in 2d sortedPairs list. """

        pairs = {}
        for subList in sortedPairs:
            addr = list(subList[0].keys())[0]
            if len(subList) > 1:
                vals = self.__burst_read_param(addr, len(subList))
                for pair, val in zip(subList, vals):
                    addr = list(pair.keys())[0]
                    pairs[addr] = val
            else:
                pairs[addr] = self.__read_param(addr)
        return pairs

    def write(self, sortedPairs):
        """ Write/Burst-Write addresses in addr:val pairs in 2d sortedPairs list. """

        for subList in sortedPairs:
            addr = list(subList[0].keys())[0]
            if len(subList) > 1:        # burst-write for grouped pairs
                vals = [v for pair in subList for k, v in pair.items()]
                self.__burst_write_param(addr, vals)
            else:
                self.__write_param(addr, subList[0][addr])

    def reset(self):
        self.link.gpio.write(0)
        self.link.gpio.write(1)

    def __write_param(self, addr, val):
        """ Write parameter value (to R2). """

        if addr[0] != self.prev_addr[0]: self.__set_I2C_reg(0x00, addr[0])
        if addr[1] != self.prev_addr[1]: self.__set_I2C_reg(0x01, addr[1])
        self.__set_I2C_reg(0x02, val)
        self.prev_addr = addr
        return val

    def __burst_write_param(self, addr, vals):
        """
        Set Start Address (R0,R1) and consecutively write to R3, while updating write cache.
        Each op involving R3 increments R0 automatically at the end.
        There is max. ~20 consecutive regs for one burst and no wrapping between R0 and R1.
        """

        if addr[0] != self.prev_addr[0]: self.__set_I2C_reg(0x00, addr[0])
        if addr[1] != self.prev_addr[1]: self.__set_I2C_reg(0x01, addr[1])
        for idx, val in enumerate(vals):
            self.__set_I2C_reg(0x03, val)   # Post-increment (write, then increment R0)
            naddr = (addr[0] + idx, addr[1])
        self.prev_addr = (naddr[0]+1, naddr[1]) # R3 write is one R0 step ahead.

    def __read_param(self, addr):
        """ Read parameter value (from R2). """

        if addr[0] != self.prev_addr[0]: self.__set_I2C_reg(0x00, addr[0])
        if addr[1] != self.prev_addr[1]: self.__set_I2C_reg(0x01, addr[1])
        self.prev_addr = addr
        return self.__read_I2C_reg(0x02)

    def __burst_read_param(self, addr, nregs):
        """ Set Start Address (R0,R1) and consecutively read from R3, while updateing write cache. """

        if addr[0] != self.prev_addr[0]: self.__set_I2C_reg(0x00, addr[0])
        if addr[1] != self.prev_addr[1]: self.__set_I2C_reg(0x01, addr[1])
        vals = []
        for idx in range(nregs):
            naddr = (addr[0] + idx, addr[1])
            val = self.__read_I2C_reg(0x03)
            vals.append(val)
        self.prev_addr = naddr
        return vals

    def __read_I2C_reg(self, reg_id):
        """ Read byte from register. """

        try: 
            return self.link.i2c.read(reg_id)
        except IOError as e:
            print('IOError in read. Attempting re-read.')
            self.__read_I2C_reg(reg_id)
        except Exception: raise     # For all other errors reset the I2C state machine and the chip.

    def __set_I2C_reg(self, reg_id, val):
        """
        Write byte to register.
        Registers are treated as offset (reg_id) from ROC's first address on bus (self.link.i2c._addr).
        Ex. first address 0x20, reg_id=2 -> write val to 0x22.
        """

        try: 
            return self.link.i2c.write(reg_id, val)
        except IOError as e:
            print('IOError in write. Attempting re-write.')
            self.__set_I2C_reg(reg_id, val)
        except Exception: raise  # For all other errors reset the I2C state machine and the chip.
