from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
import sys
import os
import time

class StatusWindow(qtw.QPlainTextEdit):
    # class constants
    log_file = 'status_logs.txt'
    log_path = os.path.join(os.path.dirname(__file__), log_file)
    
    # class custom signal definitions
    sig_add_msg = qtc.pyqtSignal(str)
    sig_log_msg = qtc.pyqtSignal(str, str)
              
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(qtc.Qt.NoTextInteraction)  
        self.initLog(self.log_path)

        # connect signals
        self.sig_add_msg.connect(self.addMsg)
        self.sig_log_msg.connect(self.logMsg)

   
    @qtc.pyqtSlot(qtc.QByteArray)
    def receiveData(self, qdata):
        '''
        Slot used to receive data from external modules
        '''
        data = str(float(qdata))
        self.sig_add_msg.emit(data)

    def addMsg(self,text):
        '''
        Prefix timestamp, add to widget, and queue for logging
        '''
        timestr = time.strftime("%c >> ")
        new_string = timestr + text
        self.appendPlainText(new_string)
        
        # automatically log any message added to window
        self.sig_log_msg.emit(new_string, self.log_path)

    def logMsg(self, text, path):
        with open(path, 'a') as out:
            out.write(text)
            out.write('\n')

    def initLog(self, path):
        '''
        Write length of hyphens as a session delimiter
        '''
        with open(path, 'a') as out:
            out.write(''.join(['-']*10))
            out.write('\n')


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = StatusWindow()
    window.show()
    sys.exit(app.exec_())