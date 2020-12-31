from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
import sys
import os
import time


class StatusWindow(qtw.QPlainTextEdit):
    # class constants
    log_file = 'status_logs.txt'
    log_path = os.path.join(__file__, log_file)
    
    # class custom signal definitions
    sig_add_msg = qtc.pyqtSignal(str)
    sig_log_msg = qtc.pyqtSignal(str, str)
              
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(qtc.Qt.NoTextInteraction)       
        self.show()
    
    @qtc.pyqtSlot(qtc.QByteArray)
    def receiveData(self, qdata):
        data = str(float(qdata))
        self.sig_add_msg.emit(data)

    def addMsg(self,text):
        self.append(text)
        
        # automatically log any message added to window
        self.sig_log_msg.emit(text, self.log_path)

    def logMsg(self, text, path):
        with open(path, 'ab') as out:
            out.write(text)

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    sys.exit(app.exec_())