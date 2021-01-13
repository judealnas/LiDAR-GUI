import sys
import pyqtgraph as pg
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
import random
from enum import Enum, auto
import time
import math

#Ui_LidarPlot, baseClass = uic.loadUiType('Ui_LidarPlot.ui')
#ui_builder = Ui_LidarPlot()

class LidarPlot(qtw.QWidget):
    
    sig_log_event = qtc.pyqtSignal(str)

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        # UI Generation #################    
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': TimestampAxisItem(orientation='bottom')})
        self.clear_button = qtw.QPushButton('Clear')
        self.pause_button = qtw.QPushButton('Pause')
        self.mode_button = qtw.QPushButton('Mode')
        
        #main layout
        self.setLayout(qtw.QVBoxLayout())
        
        # add plot widget
        self.layout().addWidget(self.plot_widget)
        
        # add horizonatl row of buttons
        self.button_layout = qtw.QHBoxLayout()
        buttons = [self.pause_button, self.clear_button, self.mode_button]
        for b in buttons:
            self.button_layout.addWidget(b)
        
        self.layout().addLayout(self.button_layout)

        self.show()
        #############################
        
        ## Class instance variables
        self.buffer_size = 20 # number of data points to plot when scrolling
        self.x = []
        self.buffer = []
        self.plot_buffer = self.buffer.copy()
        self.plot_mode = LidarPlotMode.SCROLLING
        self.data_curve = self.plot_widget.plot()   # create data curve object

        ## Connecting signals
        self.pause_button.released.connect(self.updateData)
        self.clear_button.released.connect(self.clearData)
        self.mode_button.released.connect(self.changeMode)
        
    def changeMode(self):
        if self.plot_mode == LidarPlotMode.SCROLLING:
            self.plot_mode = LidarPlotMode.ALL
        else: 
            self.plot_mode = LidarPlotMode.SCROLLING

    def plotData(self):
        self.data_curve.setData(self.x, self.buffer)
    
    def updateData(self, data: qtc.QByteArray):
        y, epoch = self.parseData(data)
        
        self.buffer.append(y)
        self.x.append(epoch)
        if (len(self.buffer) >= self.buffer_size) and self.plot_mode == LidarPlotMode.SCROLLING:
            self.buffer.pop(0)
            self.x.pop(0)
            #self.x[:-1] = self.x[1:] #rotate values left
            #self.x[-1] = (self.x[-1] + 1) #add new larger value
        else:
            pass
            #non-scrolling or insufficient data points for scrolling
            #self.x = list(range(len(self.buffer)))

        self.plotData()

    def parseData(self, data: qtc.QByteArray):
        '''
        Parses a QByteArray expecting the following format:

        [10-width numeric]_[4-digit year]_[2-digit numeric month]_[2-digit numeric day]_[2-digit hour]_[2-digit minute]
        _[2-digit second]_[6-digit microsecond]
        '''
        # decode data from bytes into string
        data_str = data.data().decode('utf-8')
        
        data_list = data_str.split('_')
        num = float(data_list[0])
        epoch = float(data_list[1])
        print(num, epoch)

        return num, epoch

    def clearData(self):
        self.buffer = []
        self.x = []
        self.plotData()

class TimestampAxisItem(pg.AxisItem):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)

    def tickStrings(self, values, scale, spacing):
        vs = [v*scale for v in values]
        tick_str = []
        for v in vs:
            l = str(v).split('.')
            out = time.strftime("%Y %b %d\n%H:%M:%S", time.gmtime(int(l[0])))
            out += "." + l[1]
            tick_str.append(out)
        
        return tick_str
            

class LidarPlotMode(Enum):
    SCROLLING = auto()  # 1
    ALL = auto()        # 2
    

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    plot_widget = LidarPlot()
    sys.exit(app.exec_())