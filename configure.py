import yaml
from Link import LinkBuilder
import Boards
import sys

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-f", "--configFile",default="../hexactrl-script/configs/initLD.yaml",
                      action="store", dest="configFile",
                      help="initial configuration yaml file")

    parser.add_option("-r", "--readConfig",
                      action="store", dest="readConfig",type=int,default=0,
                      help="set to 1 to print out the ROCs configuration")


    (options, args) = parser.parse_args()
    print(options)

    links = LinkBuilder.create(sc_type='xil')
    if len(links) == 1: board = Boards.CharBoard(links)
    if len(links) >= 3: board = Boards.HexaBoard(links)

    try:
        with open(options.configFile) as fin:
            config = yaml.safe_load(fin)
    except FileNotFoundError:
        print("%s not found"%(options.configFile))
        sys.exit(1)

    ans = board.configure(config)
    if options.readConfig:
        print( yaml.dump(board.read()) )
