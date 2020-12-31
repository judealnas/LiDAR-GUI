import sys
from os.path import dirname, join
sys.path.insert(0,dirname(dirname(__file__)))
from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import uic
import random
from enum import Enum, auto
from StatusWindow import StatusWindow as MsgWindow

Ui_TcpControl, baseClass = uic.loadUiType(join(dirname(__file__),'Ui_TcpControl.ui'))

class TcpControl(baseClass, Ui_TcpControl):

    notify_subscribers = qtc.pyqtSignal(qtc.QByteArray)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.setupUi(self)
        self.receive_led.setMinimumSize(35,35)
        self.send_led.setMinimumSize(35,35)
        self.socket = QTcpSocket(self)
        self.subscribers = [] # list of slots to connecct data-ready signal
        ## signals
        self.dis_conn_button.released.connect(self.connectSocket)
        #self.socket.connected.connect(lambda: print("Connected!"))
        #self.socket.disconnected.connect(lambda: print("Disconnected!"))
        self.socket.readyRead.connect(self.readData)

        self.show()

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
            self.panelConnected(True)
        else:
            print("Failed to Connect!", self.socket.error())
        self.dis_conn_button.setEnabled(True)
    
    def disconnectSocket(self):
        self.socket.disconnectFromHost()
        self.panelConnected(False)
        print("Disconnected from host!")
        
    def panelConnected(self, state):
        '''
        Once TCP connection is established, disable line edits, change button name,
        and rewire button signals
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

    def readData(self):
        self.receiveLedState(True)
        data_in = self.socket.readAll()
        self.notify_subscribers.emit(data_in)
        self.receiveLedState(False)
    
    def addSubscriber(self, slot):
        self.subscribers.append(slot)
        self.notify_subscribers.connect(slot)

    def removeSusbcriber(self,slot):
        self.subscribers.remove(slot)
        self.notify_subscribers.disconnect(slot)

    def receiveLedState(self, state):
        self.receive_led.setChecked(state)
    
    def sendLedState(self, state):
        self.send_led.setChecked(state)
'''
class MsgWindow(qtw.QTextEdit):
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(qtc.Qt.NoTextInteraction)       
        self.show()
    
    @qtc.pyqtSlot(qtc.QByteArray)
    def receiveData(self, qdata):
        data = float(qdata)
        self.append(str(data))
'''
class Manager(qtw.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Tcp = TcpControl()
        self.Msg = MsgWindow()

        self.Tcp.addSubscriber(self.Msg.receiveData)


if __name__ == "__main__":
    app = Manager(sys.argv)
    sys.exit(app.exec_())