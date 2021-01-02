import sys
from os.path import dirname, join
sys.path.insert(0,dirname(dirname(__file__)))
from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import uic
import random
from enum import Enum, auto

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
        self.subscribers = [] # list of slots to connect data-ready signal
        
        ## signals
        self.dis_conn_button.released.connect(self.connectSocket)
        #self.socket.connected.connect(lambda: print("Connected!"))
        #self.socket.disconnected.connect(lambda: print("Disconnected!"))
        self.socket.readyRead.connect(self.readSocket)

        #self.show()

    def connectSocket(self):
        timeout_ms = 30*1000
        
        # parse line edits
        address_text = self.address_lineedit.text()
        if address_text.lower() == 'localhost':
            self.address = QHostAddress(QHostAddress.LocalHost)
        else:
            self.address = QHostAddress(address_text).to
        
        #save port
        self.port = int(self.port_lineedit.text())
        
        # connect socket
        self.socket.connectToHost(self.address, self.port)
        self.dis_conn_button.setEnabled(False)
        if (self.socket.waitForConnected(timeout_ms)): #BLOCKING
            print("Connected")
            self.sig_log_event.emit(log_event_string+f"addSubsrciber::connected to {self.address.toIPv4Address}:{self.port}")
            self.panelConnected(True)
        else:
            print("Failed to Connect!", self.socket.error())
            self.sig_log_event.emit(log_event_string+f"connectSocket::failed to connect with {self.socket.error()}")

        self.dis_conn_button.setEnabled(True)
    
    def disconnectSocket(self):
        self.socket.disconnectFromHost()
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

        # rewire signals
        self.dis_conn_button.disconnect()
        self.dis_conn_button.released.connect(callback)

        self.sig_log_event.emit(log_event_string+"panelConnected::entered state {}".format(str(state)))


    def readSocket(self):
        self.receiveLedState(True)
        data_in = self.socket.readAll()
        self.sig_log_event.emit(log_event_string+"readSocket::received {}".format(str(data_in)))
        self.sig_broadcast_data.emit(data_in)
        self.receiveLedState(False)
    
    def receiveLedState(self, state):
        self.receive_led.setChecked(state)
    
    def sendLedState(self, state):
        self.send_led.setChecked(state)



if __name__ == "__main__":
    from StatusWindow import StatusWindow as MsgWindow
    
    class Manager(qtw.QApplication):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.Tcp = TcpControl()
            self.Tcp.show()

            self.Msg = MsgWindow()
            self.Msg.show()

            self.Tcp.addSubscriber(self.Msg.receiveData)
    
    app = Manager(sys.argv)
    sys.exit(app.exec_())