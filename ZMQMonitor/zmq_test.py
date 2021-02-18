from ZmqMonitor import ZmqMonitor
import zmq
from PyQt5 import QtCore as qtc, QtWidgets as qtw
import math
import sys

class Worker(qtc.QObject):
    sig_return = qtc.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = 0
        
        self.hold = True

    def releaseHold(self):
        self.hold = False

    def doWork(self):
        self.timer = qtc.QTimer()
        self.timer.timeout.connect(self.releaseHold)
        self.timer.start(1000)
        while not self.hold: 
            print("working")
            data = math.sin(self.angle)
            self.angle = self.angle + math.pi/2
            self.sig_return.emit(data)
            self.hold = True

class Test(qtc.QObject):
    sig_start = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread = qtc.QThread(self)
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.sig_return.connect(lambda x: print(x))
        self.sig_start.connect(self.worker.doWork)
        self.thread.started.connect(self.method)
        self.thread.start()

    def method(self):
        print("method")
        self.sig_start.emit()

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    test = Test()
    sys.exit(app.exec())