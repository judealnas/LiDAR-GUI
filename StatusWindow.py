from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
import sys
import os
import time

class StatusWindow(qtw.QPlainTextEdit):

    # class custom signal definitions
    sig_add_msg = qtc.pyqtSignal(str)
    sig_log_msg = qtc.pyqtSignal(str, str)
              
    def __init__(self,path='status_logs.txt', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = path
        if os.path.isabs(path):
            self.log_path = path
        else:
            self.log_path = os.path.join(os.path.dirname(__file__), self.log_file)
        self.initLog(self.log_path)
        self.setReadOnly(True) 
    
        # connect signals
        self.sig_add_msg.connect(self.addMsg)
        self.sig_log_msg.connect(self.logMsg)

    def createStandardContextMenu(self, pos):
        '''
        reimplimentation
        '''
        old_menu = super().createStandardContextMenu(pos)
        return old_menu

    @qtc.pyqtSlot(qtc.QByteArray)
    def receiveData(self, qdata):
        '''
        Slot used to receive data from external modules
        '''
        data = str(qdata)
        self.sig_add_msg.emit(data)

    def addMsg(self,text):
        '''
        Prefix timestamp, add to widget, and queue for logging
        '''
        timestr = time.strftime("%c >> ")
        new_string = timestr + text
        self.appendPlainText(new_string)
        self.moveCursor(qtg.QTextCursor.End)
        
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