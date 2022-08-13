import zmq
import yaml
from Link import LinkBuilder
import Boards

""" ZMQ-Server: Redirect user request to Board. """

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
print('[ZMQ] Server started')

def redirect(fn):
    socket.send_string('READY')
    cfg_str  = socket.recv_string()
    cfg_yaml = yaml.safe_load(cfg_str)
    ans_yaml = fn(cfg_yaml)
    ans_str  = yaml.dump(ans_yaml, default_flow_style=False)
    socket.send_string(ans_str)

try:

    links = LinkBuilder.create(sc_type='xil')
    if len(links) == 1: board = Boards.CharBoard(links)
    if len(links) >= 3: board = Boards.HexaBoard(links)

    while True:
        string = socket.recv_string().lower()

        if string == "initialize" or string == "configure":
            if board: redirect(board.configure)
            else: socket.send_string("E: Board not initialized.")

        elif string == "read": redirect(board.read)

        elif string == "reset_tdc" or string == "resettdc":
            ans = board.reset_tdc()
            socket.send_string('%s' % ans)

        elif string == "read_adc" or string == "measadc":
            if type(board) is Boards.HexaBoard: redirect(board.read_adc)
            else: socket.send_string('E: ADCs exist only on Trophy/Hexaboard.')

        elif string == "read_pwr":
            if type(board) is Boards.HexaBoard:
                pwr = board.read_pwr()
                socket.send_string("%s" % yaml.dump(pwr, default_flow_style=False))
            else: socket.send_string('E: ADCs exist only on Trophy/Hexaboard.')

except KeyboardInterrupt:
    print('\nClosing server.')
    socket.close()
    context.term()
