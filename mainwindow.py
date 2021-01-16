import os
import sys
sys.path.extend([os.path.join(os.path.dirname(__file__), x) for x in ['TcpControl', 'LidarPlot']])

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from TcpControl import TcpControl 
from LidarPlot import LidarPlot  
from StatusWindow import StatusWindow 

class MainWindow(qtw.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.central_widget = qtw.QWidget()
        self.grid = qtw.QGridLayout(self.central_widget)
        
        self.lidar_plot = LidarPlot(self.central_widget)
        self.grid.addWidget(self.lidar_plot, 0,0,3,1)
        
        self.tcp_control = TcpControl()
        self.tcp_control.sizePolicy().setVerticalStretch(1)
        self.tcp_control.sizePolicy().setHorizontalStretch(1)
        self.grid.addWidget(self.tcp_control, 0,1,1,1)


        self.status_window = StatusWindow()
        self.status_window.sizePolicy().setVerticalStretch(2)
        self.grid.addWidget(self.status_window, 1,1,1,1)
        

        self.central_widget.setLayout(self.grid)
        self.setCentralWidget(self.central_widget)

        ## connect signals
        self.tcp_control.getBroadcastSignal().connect(self.lidar_plot.updateData)
        self.tcp_control.getLogSignal().connect(self.status_window.addMsg)
        self.lidar_plot.getLogSignal().connect(self.status_window.addMsg)

        
        
def main():
    app = qtw.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()