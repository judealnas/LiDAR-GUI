import sys
import zmq
from PyQt5 import QtCore as qtc, QtWidgets as qtw, QtNetwork as qtn

class Main(qtc.QObject):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.port = "5556"
        self.socket.connect("tcp://localhost:%s" % self.port)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        
        #Socket notifier
        self.socket_notifier = qtc.QSocketNotifier(self.socket.getsockopt(zmq.FD), qtc.QSocketNotifier.Read, self)
        self.socket_notifier.activated.connect(self.readData)
        
        #Monitoring pair sockets
        self.monitor_sockets = self.socket.get_monitor_socket()
        self.monitor_thread = qtc.QThread()


    def readData(self):
        self.socket_notifier.setEnabled(False)

        if (self.socket.getsockopt(zmq.EVENTS) & zmq.POLLIN):
            while self.socket.getsockopt(zmq.EVENTS) & zmq.POLLIN:
                string = self.socket.recv_string()
                topic, messagedata = string.split()
                print(topic, messagedata)
        self.socket_notifier.setEnabled(True)


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    m = Main()
    sys.exit(app.exec())
