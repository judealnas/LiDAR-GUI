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
            if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
                break
        
        monitor_socket.close()

class ZmqSocketMonitorSignals(qtc.QObject):
    '''
    Define signals passed as argument to the threaded monitoring loop
    '''
    sig_connected = qtc.pyqtSignal()
    sig_connect_delayed = qtc.pyqtSignal()
    sig_connect_retired = qtc.pyqtSignal()
    sig_listening = qtc.pyqtSignal()
    sig_bind_failed = qtc.pyqtSignal()
    sig_accepted = qtc.pyqtSignal()
    sig_accept_failed = qtc.pyqtSignal()
    sig_accept_failed = qtc.pyqtSignal()
    sig_closed = qtc.pyqtSignal()
    sig_close_failed = qtc.pyqtSignal()
    sig_disconnected = qtc.pyqtSignal()
    sig_monitor_stopped = qtc.pyqtSignal()
    sig_handshake_failed = qtc.pyqtSignal()
    sig_handhake  = qtc.pyqtSignal()
    sig_handshake_failed_auth = qtc.pyqtSignal()

    sig_read_ready = qtc.pyqtSignal()
    sig_error_occurred = qtc.pyqtSignal(dict)
    

if __name__ == "__main__":
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
    monitor2 = ZmqSocketMonitor(publisher)
    monitor1 = ZmqSocketMonitor(subscriber)
    time.sleep(1)
    subscriber.connect('tcp://localhost:49417')
    time.sleep(1)
    publisher.bind('tcp://127.0.0.1:49417')
    time.sleep(5)
    subscriber.disconnect("tcp://localhost:49417")
    time.sleep(5)
    publisher.disable_monitor()
    time.sleep(1)
    publisher.disconnect("tcp://127.0.0.1:49417")
    time.sleep(1)
