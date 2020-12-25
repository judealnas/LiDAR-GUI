from PyQt5 import QtWidgets, QtCore, uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
from random import randint
import socket
import struct


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('mainwindow.ui', self)
        
        self.x = list(range(100))
        self.y = [randint(0,1) for _ in range(100)]
       
        self.data_line = self.graphWidget.plot(self.x, self.y)

        #connecting signals to slots
        self.startButton.released.connect(self.openConnection)
        self.pauseButton.toggled.connect(self.pausePlot)
        self.stopButton.released.connect(self.close) #connects to close() method of QMainWindow class
        self.stopButton.released.connect(self.closeConnection)

    
    def openConnection(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET = IPv4; SOCK_STREAM = TCP
        self.s.connect((socket.gethostname(), 49417))

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
        print("socket open and timer set\n")


    def plot(self, x, y):
        self.data_line = self.graphWidget.plot(x, y)
    
    def pausePlot(self):
        if self.pauseButton.isChecked():
            self.timer.stop()
        else:
            self.timer.start()
    
    def closeConnection(self):
        print("closing socket\n")
        self.s.close()
        self.timer.stop()
        
    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first x element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first y element
        rec_data = self.s.recv(10)
        rec_data = float(rec_data.decode("utf-8"))
        self.y.append(rec_data)  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.



def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()