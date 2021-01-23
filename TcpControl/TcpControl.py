import sys
from os.path import dirname, join
sys.path.insert(0,dirname(dirname(__file__)))
from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc, QtWidgets as qtw, uic
import random

Ui_TcpControl, baseClass = uic.loadUiType(join(dirname(__file__),'Ui_TcpControl.ui'))
log_event_string = "{}::".format(__name__)

class TcpControl(baseClass, Ui_TcpControl):
    
    sig_broadcast_data = qtc.pyqtSignal(qtc.QByteArray)
    sig_log_event = qtc.pyqtSignal(str)
    sig_relay_read = qtc.pyqtSignal(qtc.QByteArray)
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.setupUi(self)
        self.receive_led.setMinimumSize(35,35)
        self.send_led.setMinimumSize(35,35)
        self.socket = QTcpSocket(self)
        
        ## connecting GUI element signals
        self.dis_conn_button.released.connect(self.connectSocket)

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
        
        # connect socket
        self.socket.connectToHost(self.address, self.port)
        self.dis_conn_button.setEnabled(False)
        if (self.socket.waitForConnected(timeout_ms)): #BLOCKING
            print("Connected")
            self.sig_log_event.emit(log_event_string+f"connectSocket::connected to {self.address.toIPv4Address}:{self.port}")
            self.panelConnected(True)
            
            #instantiate socket reader and thread
            self.socket_reader = SocketReader(self.socket)
            self.socket_reader_thread = qtc.QThread()
            self.socket_reader.moveToThread(self.socket_reader_thread)
            #connect socket reader signals
            self.socket.readyRead.connect(self.socket_reader.getReadSlot()) #When data available, call appropriate method in SocketReader object
            self.socket_reader.getReturnSig().connect(self.relaySocketRead) #signal emitted when data is received
        
            #instantiate socket writer and thread
            self.socket_writer = SocketWriter(self.socket)
            self.socket_writer_thread = qtc.QThread()
            self.socket_writer.moveToThread(self.socket_writer_thread)

            #connect socket writer signasl
            self.socket_writer.getReturnSig().connect(self.relaySocketWrite)

            #start threads
            self.socket_reader_thread.start()
            self.socket_writer_thread.start()
        else:
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

        # rewire dis/connect button signals
        self.dis_conn_button.disconnect()
        self.dis_conn_button.released.connect(callback)

        self.sig_log_event.emit(log_event_string+"panelConnected::entered state {}".format(str(state)))

    def relaySocketRead(self,data_in: qtc.QByteArray):
        '''
        Slot that receives read data from socket reader thread. Broadcasts
        data to modules subscribed to data via signals/slots. Also controls
        receive LED indicator and emits logging signal
        '''
        self.receive_led.toggle()
        self.sig_log_event.emit(log_event_string+"readSocket::received {}".format(data_in.data().decode('utf-8')))
        self.sig_broadcast_data.emit(data_in)
    
    def relaySocketWrite(self,write_status: int):
        '''
        Slot that receives the status of write and emits logging event
        '''
        self.sig_log_event(log_event_string+"writeSocket::write_status={}".format(write_status))
    
    ####Accessor functions for modularity######
    def getLogSignal(self) -> qtc.pyqtSignal:
        return self.sig_log_event
    
    def getBroadcastSignal(self) -> qtc.pyqtSignal:
        return self.sig_broadcast_data
    
    def getWriteSlot(self):
        return self.socket_writer.getWriteSlot
    ############################################

class SocketReader(qtc.QObject):
    '''
    Class dedicated to simply reading data from a QTcpSocket object
    and returning read data to the parent TcpContorl object. Meant to
    be pushed into a separate thread
    '''
    sig_return = qtc.pyqtSignal(qtc.QByteArray)

    def __init__(self,socket: QTcpSocket,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.socket = socket
    
    def readSocket(self):
        data_in = self.socket.readAll()
        self.sig_return.emit(data_in)
    
    ##Accessor functions for modularity
    def getReturnSig(self):
        return self.sig_return

    def getReadSlot(self):
        return self.readSocket

class SocketWriter(qtc.QObject):
    '''
    Class dedicated to simply reading data from a QTcpSocket object
    and returning read data to the parent TcpContorl object. Meant to
    be pushed into a separate thread
    '''
    sig_return = qtc.pyqtSignal(int)

    def __init__(self, socket:QTcpSocket, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.socket = socket
    
    def writeSocket(self,msg: str):
        '''
        TO-DO: depending on protocol, send message size first
        '''
        write_status = self.socket.write(bytes(msg,'utf-8'))
        self.sig_return.emit(write_status)
    
    ##Accessor functions for modularity
    def getReturnSig(self):
        return self.sig_return

    def getWriteSlot(self):
        return self.writeSocket

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