from ROC import ROC
from Translator import Translator
from nested_dict import nested_dict
from nested_lookup import get_all_keys, nested_update
from threading import Thread
from itertools import groupby

class PropagatingThread(Thread):
    """ Thread class to propagate occuring Exceptions to the calling thread. """

    def run(self):
        self.exc = None
        try: self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e: self.exc = e     # store exception

    def join(self):
        super(PropagatingThread, self).join()
        if self.exc: raise self.exc
        return self.ret

class CharBoard():
    """ Base class for characterization boards """

    def __init__(self, links):
        self.rocs = {name:ROC(link) for (name, link) in links.items()}
        self.writeCaches = {name:{} for name in links.keys()}  # dicts are thread-safe, so we can write to it from different threads
        for rname, roc in self.rocs.items(): 
            roc.reset()
            print('[%s] GPIO reset' % rname)
        roc_type = self.__detect_roc_type()         # Determine which ROC architecture we're on.
        self.translator = Translator(roc_type)      

    def configure(self, cfgs):
        """ Configure ROCs in separate threads and return after all are finished. """

        threads = []
        for lbl, cfg in cfgs.items():
            for rname in [name for name in self.rocs.keys() if lbl in name]:
                roc = self.rocs[rname]
                thread = PropagatingThread(target=self.__write, args=(roc, rname, cfg))
                thread.start()
                threads.append(thread)
        for thread in threads:
            try: 
                thread.join()                       # wait for threads to finish
            except Exception as e:                  # catch i2c exceptions.
                print("ERROR in configure: ", e)
                for rname, roc in self.rocs.items(): 
                    print('[%s] GPIO reset' % rname)
                    roc.reset()
                for lbl, roc in self.rocs.items(): 
                    sortedPairs = self.translator.sort_pairs(self.writeCaches[lbl])
                    roc.write(sortedPairs)                                                      # Rewrite caches
                return self.configure(cfgs)                                                     # Reload cfgs

        return "ROC(s) CONFIGURED"

    def read(self, cfgs):
        """ Factory method for unified interface to write. """

        if cfgs: return self.__read_fr_cfgs(cfgs)
        else: return self.__read_fr_cache()

    def reset_tdc(self):
        """ Reset MasterTDC parameter for all ROCs. """

        self.configure({lbl:{"MasterTdc":{"all":{"START_COUNTER":0}}} for lbl in self.rocs.keys()})
        self.configure({lbl:{"MasterTdc":{"all":{"START_COUNTER":1}}} for lbl in self.rocs.keys()})
        return "masterTDCs reset."

    def __write(self, roc, roc_name, cfg):
        """ Stuff that should run in a separate thread per ROC. """

        pairs = self.translator.pairs_from_cfg(cfg, self.writeCaches[roc_name], roc)
        self.writeCaches[roc_name].update(pairs)
        sortedPairs = self.translator.sort_pairs(pairs)
        roc.write(sortedPairs)
        print('[%s] Configured' % roc_name)

    def __read_fr_cache(self):
        """ Read addresses in write_param cache from rocs. """

        rd_cfgs = {}
        for lbl, roc in self.rocs.items():
            pairs = self.writeCaches[lbl]
            sortedPairs = self.translator.sort_pairs(pairs)
            rd_pairs = roc.read(sortedPairs)
            rd_cfg = self.translator.cfg_from_pairs(rd_pairs)
            rd_cfgs[lbl] = rd_cfg
        return rd_cfgs

    def __read_fr_cfgs(self, cfgs):
        """ Read addresses (=keys) in cfgs from rocs. """

        rd_cfgs = {}
        for lbl, cfg in cfgs.items():
            for roc_name in [name for name in self.rocs.keys() if lbl in name]:
                roc = self.rocs[rname]
                req_keys = set(key[-1] for key in nested_dict(cfg).keys_flat())
                pairs = self.translator.pairs_from_cfg(cfg, roc_name)
                sortedPairs = self.translator.sort_pairs(pairs)
                rd_pairs = roc.read(sortedPairs)
                rd_cfg = self.translator.cfg_from_pairs(rd_pairs)	# params in same reg are also read..
                req_cfg = nested_dict()		                        # .. so only return requested config.
                for idx, val in nested_dict(rd_cfg).items_flat():
                    if idx[-1] in req_keys: 	                    # idx=(block,blockID,param)
                        req_cfg[idx[0]][idx[1]][idx[2]] = val
                rd_cfgs[roc_name] = req_cfg.to_dict()
        return rd_cfgs

    def __detect_roc_type(self):
        """ Query ROCs to detect if we're on Si or SiPM. """

        for roc in self.rocs.values():
            Glob_Ana_reg0_half0 = (32, 37)
            probe_pair = [[{Glob_Ana_reg0_half0: None}]]
            answer = roc.read(probe_pair)
            val = answer[Glob_Ana_reg0_half0]

        if val == 130: 
            print('[roc_s*] Detected Si type')
            return "Si"
        elif val == 143: 
            print('[roc_s*] Detected SiPM type')
            return "SiPM"

class HexaBoard(CharBoard):
    """
    HexaBoard differs from CharBoard by:
    1. Board Orientation (alignment of Trophy i2c labels with ROC addresses found on bus)
    2. On-board Trophy ADCs
    """

    def read_pwr(self):
        """ Return reading of TrophyBoard's analog (piv_a) and digital (piv_d) ADCs. """

        adc = { 'piv_a': '/sys/class/i2c-dev/i2c-1/device/1-0049/in4_input' ,
                'piv_d': '/sys/class/i2c-dev/i2c-1/device/1-0049/in5_input' }
        res = {}
        for lbl, cmd in adc.items():
            with open(cmd) as f:
                res[lbl] = f.read().rstrip('\n')
        return res

    def read_adc(self, cfgs):
        """
        Return reading of TrophyBoard's probeDC and InCtest ADCs.
        Since both halves of a chip and all the chips in a sector are wired together for one ADC,
        we have to set and read probeDC and calibDAC sequentially per chip and per half.
        Orientation of HexaBoard determines which ADC (in TrophyBoard sectors) have to be read.
        """

        pdc_adc = {'roc_s0': '/sys/class/i2c-dev/i2c-2/device/2-0048/in5_input',
                   'roc_s1': '/sys/class/i2c-dev/i2c-3/device/3-0049/in5_input',
                   'roc_s2': '/sys/class/i2c-dev/i2c-1/device/1-0048/in5_input', }

        cal_adc = {'roc_s0': '/sys/class/i2c-dev/i2c-2/device/2-0048/in4_input',
                   'roc_s1': '/sys/class/i2c-dev/i2c-3/device/3-0049/in4_input',
                   'roc_s2': '/sys/class/i2c-dev/i2c-1/device/1-0048/in4_input', }

        sectors = self.__get_sectorNames()
        cfg_keys = get_all_keys(cfgs)    # scan the received cfg for 'Calib_dac' or 'Probe_dcX'
        if 'Calib_dac' in cfg_keys: 
            adc  = cal_adc
            keys = ['IntCtest', 'ExtCtest', 'Calib_dac']
        elif any('Probe_dc' in str(key) for key in cfg_keys): 
            adc  = pdc_adc
            keys = [key for key in cfg_keys if 'Probe_dc' in key]

        # expand original cfgs (ocfgs) and zero'd cfgs (zcfgs)
        res = nested_dict()
        ocfgs = self.translator.expand_cfgs(cfgs, self.rocs)
        zcfgs = ocfgs.copy()
        for key in keys: zcfgs = nested_update(zcfgs, key=key, value=0)
        
        # group ROCs that can be configured in parallel
        rocs = sorted(list(ocfgs.keys()), key=lambda roc: roc[-1])
        confGroup = [list(g) for _, g in groupby(rocs, key=lambda roc: roc[-1])]

        for sel_half in [0,1]:
            for group in confGroup:
                # create cfgs for ROCs and Halves that can be configured together
                ncfgs = nested_dict(zcfgs)
                for roc in group:
                    ncfgs[roc]['ReferenceVoltage'][sel_half] = ocfgs[roc]['ReferenceVoltage'][sel_half]

                # configure, readout & save
                self.configure(ncfgs.to_dict())
                for roc in group:
                    sector = self.sector_map[roc]
                    try:
                        with open(adc[sector]) as f:
                            res[roc][sel_half] = f.read().rstrip('\n')
                    except:
                        res[roc][sel_half] = 0
                        continue

        self.configure(zcfgs)   # deconfigure
        return res.to_dict()
