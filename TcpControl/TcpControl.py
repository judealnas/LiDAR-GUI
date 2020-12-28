import sys
from os.path import dirname, join
sys.path.append(dirname(__file__))
from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import uic
import random
from enum import Enum, auto

Ui_TcpControl, baseClass = uic.loadUiType(join(dirname(__file__),'TcpControl.ui'))

class TcpControl(baseClass, Ui_TcpControl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.setupUi(self)
        self.receive_led.setMinimumSize(35,35)
        self.send_led.setMinimumSize(35,35)

        ## signals
        self.dis_conn_button.released.connect(self.connectSocket)

        self.show()

    def connectSocket(self):
        timeout_ms = 30*1000
        # save address
        address_text = self.address_lineedit.text()
        print(address_text)
        if address_text.lower() == 'localhost':
            self.address = QHostAddress(QHostAddress.LocalHost)
        else:
            self.address = QHostAddress(address_text)
        
        #save port
        self.port = int(self.port_lineedit.text())
        print(self.port)
        print(self.address.toString())

        self.socket = QTcpSocket(self)
        self.socket.connected.connect(lambda: print("Connected!"))
        self.socket.disconnected.connect(lambda: print("Disconnected!"))

        self.socket.connectToHost(self.address, self.port)
        self.dis_conn_button.setEnabled(False)
        if (self.socket.waitForConnected(timeout_ms)): #BLOCKING
            print("Connected")
            self.lockPanel()
        else:
            print("Failed to Connect!", self.socket.error())
        self.dis_conn_button.setEnabled(True)
        print(self.socket.state())
        self.panelConnected()
    
    def disconnectSocket(self):
        print("Disconnecting...")
        self.socket.disconnectFromHost()
    
    def panelConnected(self):
        self.address_lineedit.setEnabled(False)
        self.port_lineedit.setEnabled(False)
        
        self.dis_conn_button.disconnect()
        self.dis_conn_button.released.connect(self.panelDisconnected)
        self.dis_conn_button.setText("DISCONNECT")
        
    
    def panelDisconnected(self):
        self.address_lineedit.setEnabled(True)
        self.port_lineedit.setEnabled(True)
        
        self.dis_conn_button.disconnect()
        self.dis_conn_button.released.connect(self.panelDisconnected)
        self.dis_conn_button.setText("DISCONNECT")
        

    def receiveLedState(self, state):
        self.receive_led.setChecked(state)
    
    def sendLedState(self, state):
        self.send_led.setChecked(state)

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    tcp_widget = TcpControl()
    sys.exit(app.exec_())