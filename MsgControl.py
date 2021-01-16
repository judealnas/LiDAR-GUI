from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg

class MsgControl(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.send_button = qtw.QPushButton('SEND', self)
        self.send_lineedit = qtw.QLineEdit(self)
        self.rec_lineedit = qtw.QLineEdit(self)
        self.rec_lineedit.setEnabled(False)

        # create form layout containing one lineedit for the send message
        self.send_form = qtw.QFormLayout()
        self.send_form.addRow('Msg to send', self.send_lineedit)

        #create another form layout containing the other lineedit for the received message
        self.rec_form = qtw.QFormLayout()
        self.rec_form.addRow('Received', self.rec_lineedit)

        #Place the two lineedits next to each other
        self.lineedit_layout = qtw.QHBoxLayout()
        self.lineedit_layout.addLayout(self.send_form)
        self.lineedit_layout.addLayout(self.rec_form)

        
        self.setLayout(qtw.QVBoxLayout())
        self.layout().addLayout(self.lineedit_layout)
        self.layout().addWidget(self.send_button)

        self.show()

    def getSendTrigger(self):
        return self.send_button.released

if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)
    widg = MsgControl()
    sys.exit(app.exec_())