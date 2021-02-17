import zmq
from zmq.utils.monitor import recv_monitor_message
import sys
from os.path import dirname
sys.path.append(dirname(dirname(__file__)))
from PyQt5 import QtCore as qtc
from QtThreadWorker import QtThreadWorker
import traceback
import time

class ZmqSocketMonitor(qtc.QObject):

    readReady = qtc.pyqtSignal(qtc.QByteArray)
    disconnected = qtc.pyqtSignal()
    errorOccurred = qtc.pyqtSignal()
    
    def __init__(self, socket: zmq.Socket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generateEventDict()
        
        self.socket = socket
        self.monitor_socket = socket.get_monitor_socket()   # returns a connected PAIR socket 
        self.monitor_threadpool = qtc.QThreadPool(self)
        self.monitor_signals = ZmqSocketMonitorSignals(self)

        self.monitor_signals.sig_connected.connect(lambda x: print("Connected!"))
        self.monitor_signals.sig_disconnected.connect(lambda x: print("DISConnected!"))


        self.threadworker = QtThreadWorker(self.monitorSocket, self.monitor_socket, self.monitor_signals)
        self.monitor_threadpool.globalInstance().start(self.threadworker)
    
    def generateEventDict(self):
        '''
        Loop through all attributes of the zmq package that begin 
        with 'EVENT_', saving it's name and value in a dictionary
        '''
        self.EVENT_MAP = {}
        for name in dir(zmq):
            if name.startswith('EVENT_'):
                value = getattr(zmq,name)
                self.EVENT_MAP[value] = name
        print("{}".format(self.EVENT_MAP))

    def monitorSocket(self, monitor_socket: "zmq.Socket", monitor_signals: "ZmqSocketMonitorSignals"):
        '''
        Main monitoring function. While loop that receives message
        from the monitoring PAIR socket as they arrive. Emit provided signals
        according to received events
        '''
        print("Hello from thread {}".format(qtc.QThread.currentThread()))
        while monitor_socket.poll():
            evt = recv_monitor_message(monitor_socket)
            evt.update({'description': self.EVENT_MAP[evt['event']]})
            print("Event: {}".format(evt))
            monitor_signals.zmq_signal_dict[evt['event']].emit(evt)
            if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
                break
        
        monitor_socket.close()

class ZmqSocketMonitorSignals(qtc.QObject):
    '''
    Define signals passed as argument to the threaded monitoring loop.
    Signals with dict datatypes pass the dict returned by recv_monitor_message,
    which is of the form {'event': int, 'value': int, 'endpoint': bytes, 'description': str}
    '''
    #
    sig_connected = qtc.pyqtSignal(dict)
    sig_connect_delayed = qtc.pyqtSignal(dict)
    sig_connect_retired = qtc.pyqtSignal(dict)
    sig_listening = qtc.pyqtSignal(dict)
    sig_bind_failed = qtc.pyqtSignal(dict)
    sig_accepted = qtc.pyqtSignal(dict)
    sig_accept_failed = qtc.pyqtSignal(dict)
    sig_accept_failed = qtc.pyqtSignal(dict)
    sig_closed = qtc.pyqtSignal(dict)
    sig_close_failed = qtc.pyqtSignal(dict)
    sig_disconnected = qtc.pyqtSignal(dict)
    sig_monitor_stopped = qtc.pyqtSignal(dict)
    sig_handshake_failed = qtc.pyqtSignal(dict)
    sig_handshake_failed_proto = qtc.pyqtSignal(dict)
    sig_handhake_succeeded  = qtc.pyqtSignal(dict)
    sig_handshake_failed_auth = qtc.pyqtSignal(dict)

    sig_read_ready = qtc.pyqtSignal()
    sig_error_occurred = qtc.pyqtSignal(dict)

    #dictionary associating a ZMQ socket event id with a PyQt5 signal
    zmq_signal_dict = {
        1: sig_connected,
        2: sig_connect_delayed,
        4: sig_connect_retired,
        8: sig_listening,
        16: sig_bind_failed,
        32: sig_accepted,
        64: sig_accept_failed,
        128: sig_closed,
        256: sig_close_failed,
        512: sig_disconnected,
        1024: sig_monitor_stopped,
        2048: sig_handshake_failed,
        8192: sig_handshake_failed_proto,
        4096: sig_handhake_succeeded,
        16384: sig_handshake_failed_auth
    }
    

if __name__ == "__main__":
    s = ZmqSocketMonitor(10)
    s.generateEventDict()
    '''
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    subscriber = context.socket(zmq.SUB)

    monitor = ZmqSocketMonitor(subscriber)
    subscriber.connect("tcp://localhost:49217")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, '')

    #publisher.bind('tcp://*:49217')
    end_time = time.time() + 60

    i = 0
    while (time.time() < end_time):
        print("before rec")
        print(subscriber.recv_string())
        print("after rec")
        #publisher.send_string(str(i))
        i += 1
        time.sleep(0.5)

    subscriber.close()
    #subscriber.disconnect("tcp://localhost:49217")

    #publisher.close()
    time.sleep(5)
    context.destroy()
    
'''