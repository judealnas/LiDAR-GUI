from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtNetwork import QTcpSocket, QHostAddress
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
from random import randint
import socket
import struct

ui_filename = 'mainwindow.ui'

_, baseClass = uic.loadUiType(ui_filename)

class MainWindow(baseClass):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi(ui_filename, self)
        
        self.x = list(range(100))
        self.y = [randint(0,1) for _ in range(100)]
       
        self.data_line = self.graphWidget.plot(self.x, self.y)

        #connecting signals to slots
        self.startButton.released.connect(self.openConnection)
        self.pauseButton.toggled.connect(self.pausePlot)
    #   self.stopButton.released.connect(self.close) #connects to close() method of QMainWindow class
        self.stopButton.released.connect(self.closeConnection)

    
    def openConnection(self):
        self.tcpSocket = QTcpSocket(self)
        self.tcpSocket.connectToHost(QHostAddress.LocalHost, 49417)

        self.tcpSocket.connected.connect(lambda: print("Connected!"))
        self.tcpSocket.disconnected.connect(lambda: print("Disconnected!"))
        self.tcpSocket.readyRead.connect(self.update_plot_data)

        print("socket open and timer set\n")


    def plot(self, x, y):
        self.data_line = self.graphWidget.plot(x, y)
    
    def pausePlot(self):
        pass


    def closeConnection(self):
        print("closing socket\n")
        self.tcpSocket.disconnectFromHost()

    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first x element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first y element
        rec_data2 = self.tcpSocket.readAll()
        print(type(rec_data2),float(rec_data2))
        self.y.append(float(rec_data2))

        self.data_line.setData(self.x,self.y)  # Update the data.



def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()