import sys
from os.path import dirname, join
sys.path.insert(0,dirname(dirname(__file__)))
from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc, QtWidgets as qtw, uic, QtNetwork as qtn
import random
import zmq
import zmq.utils
from ZmqMonitor import ZmqMonitor

Ui_TcpControl, baseClass = uic.loadUiType(join(dirname(__file__),'Ui_TcpControl.ui'))
log_event_string = "{}::".format(__name__)

class TcpControl(baseClass, Ui_TcpControl):
    
    sig_broadcast_data = qtc.pyqtSignal(qtc.QByteArray)
    sig_log_event = qtc.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.setupUi(self)
        self.receive_led.setMinimumSize(35,35)
        self.send_led.setMinimumSize(35,35)
        
        self.socket = QTcpSocket(self)

        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PAIR)
        #self.zmq_socket.setsockopt_string(zmq.SUBSCRIBE,'')
        self.zmq_notifier = qtc.QSocketNotifier(self.zmq_socket.getsockopt(zmq.FD), qtc.QSocketNotifier.Read, self)
        self.zmq_monitor_thread = qtc.QThread(self)
        self.zmq_monitor = ZmqMonitor(self.zmq_socket)
        self.zmq_monitor.moveToThread(self.zmq_monitor_thread)

        ## signals
        self.dis_conn_button.released.connect(self.connectSocket)
        self.socket.readyRead.connect(self.readSocket) #automatically read data from socket whenever availables
        self.socket.stateChanged.connect(self.logSocketStateChage)  #for debugging, track state of socket
        self.socket.errorOccurred.connect(self.logSocketError)  #log any socket errors as they occur
        
        self.zmq_notifier.activated.connect(self.zmqActivity)
        self.zmq_monitor.sig_error_occurred.connect(self.logZmqEvent)
        self.zmq_monitor.sig_connected.connect(self.logZmqEvent)
        self.zmq_monitor.sig_disconnected.connect(self.logZmqEvent)
        self.zmq_monitor.sig_closed.connect(self.logZmqEvent)
        self.zmq_monitor.sig_closed.connect(self.disconnectSocket)

        self.zmq_monitor_thread.finished.connect(self.zmq_monitor.deleteLater)
        self.zmq_monitor_thread.started.connect(self.zmq_monitor.monitorSocket)

        self.zmq_monitor_thread.start() #this QThread is not closing on exit, causing core dump on GUI exit

    def zmqActivity(self):
        print("Notifer")
        self.zmq_notifier.setEnabled(False)
        print(self.zmq_socket.getsockopt(zmq.EVENTS))
        if (self.zmq_socket.getsockopt(zmq.EVENTS) & zmq.POLLIN):
            while (self.zmq_socket.getsockopt(zmq.EVENTS) & zmq.POLLIN):
                rec_data = self.zmq_socket.recv_string()
                print("ZMQ Received: {}".format(rec_data))
                self.sig_log_event.emit(log_event_string+"zmqActivity::received {}".format(str(rec_data)))
                self.sig_broadcast_data.emit(qtc.QByteArray(bytes(rec_data, 'utf-8')))
            
        self.zmq_notifier.setEnabled(True)
        print("Notifer Enabled")

    def logZmqEvent(self, evt):
        self.sig_log_event.emit(log_event_string + f"{evt}")
        
    def logSocketError(self, value:int):
        error_str = self.socket.errorString()
        self.sig_log_event.emit(log_event_string+error_str)


    def logSocketStateChage(self, value: int): 
        meta = self.socket.staticMetaObject
        state_str = meta.enumerator(meta.indexOfEnumerator('SocketState')).valueToKey(value)
        self.sig_log_event.emit(log_event_string+"Socket State = {}".format(state_str))

    def connectSocket(self):
        timeout_ms = 30*1000
        
        # parse line edits
        address_text = self.address_lineedit.text()
        if address_text.lower() == 'localhost':
            self.address = QHostAddress(QHostAddress.LocalHost)
        else:
            self.address = QHostAddress(address_text)
        
        #save port
        self.port = int(self.port_lineedit.text())
        
        #zmq socket
        zmq_connect_status = self.zmq_socket.connect("tcp://localhost:49217")
        
        # connect socket
        self.socket.connectToHost(self.address, self.port)
        self.dis_conn_button.setEnabled(False)
        if (self.socket.waitForConnected(timeout_ms)): #BLOCKING
            print("Connected")
            self.sig_log_event.emit(log_event_string+f"connectSocket::connected to {self.address.toIPv4Address}:{self.port}")
            self.panelConnected(True)
        else:
            print("Failed to Connect!", self.socket.error())
            self.sig_log_event.emit(log_event_string+f"connectSocket::failed to connect with {self.socket.error()}")

        self.dis_conn_button.setEnabled(True)
    
    def disconnectSocket(self):
        '''
        TO-DO: Depending on conditions, emit signals to exit the socket read/write threads
        '''
        self.socket.disconnectFromHost()
        self.zmq_socket.disconnect("tcp://localhost:49217")
        self.sig_log_event.emit(log_event_string+"disconnectSocket::disconnected socket")
        self.panelConnected(False)
        
    def panelConnected(self, state):
        '''
        Disable line edits, change button name, and rewire button signals according
        to TCP socket state.

        state = True: Socket connected; disable UI elements
        state = False: Socket disconnected; enable UI elements
        '''
        if state:
            button_text = "DISCONNECT"
            callback = self.disconnectSocket
        else:
            button_text = "CONNECT"
            callback = self.connectSocket
        
        # disable line edits
        self.address_lineedit.setEnabled(not state)
        self.port_lineedit.setEnabled(not state)
        
        # change button text
        self.dis_conn_button.setText(button_text)

        # rewire dis/connect button signals
        self.dis_conn_button.disconnect()
        self.dis_conn_button.released.connect(callback)

        self.sig_log_event.emit(log_event_string+"panelConnected::entered state {}".format(str(state)))


    def readSocket(self):
        self.receive_led.toggle()
        data_in = self.socket.readAll()
        #self.sig_log_event.emit(log_event_string+"readSocket::received {}".format(str(data_in)))
        #self.sig_broadcast_data.emit(data_in)
    
    def writeSocket(self, msg: str):
        self.send_led.toggle()
        print("Sending {}".format(bytes(msg + '\0', 'utf-8')))
        #write_status = self.socket.write(bytes(msg + '\0', 'utf-8'))
        write_status = self.zmq_socket.send(bytes(msg + '\0', 'utf-8'), zmq.DONTWAIT)
        print(write_status)
        print("zmq sent")
        self.sig_log_event.emit(log_event_string+"writeSocket:: wrote {} with status {}".format(msg,write_status))

    def receiveLedState(self, state):
        self.receive_led.setChecked(state)
    
    def sendLedState(self, state):
        self.send_led.setChecked(state)
    
    ## Accessor functions for modularity############
    def getLogSignal(self):
        return self.sig_log_event
    
    def getBroadcastSignal(self) -> qtc.pyqtSignal:
        return self.sig_broadcast_data

    def getWriteSocketSlot(self):
        return self.writeSocket
    ###################################################

            
if __name__ == "__main__":
    from StatusWindow import StatusWindow as MsgWindow
    
    class Manager(qtw.QApplication):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.Tcp = TcpControl()
            self.Tcp.show()

            self.Msg = MsgWindow()
            self.Msg.show()

    
    app = Manager(sys.argv)
    sys.exit(app.exec_())