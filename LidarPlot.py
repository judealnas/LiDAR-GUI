import sys
import pyqtgraph as pg
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
import random
from enum import Enum, auto

#Ui_LidarPlot, baseClass = uic.loadUiType('LidarPlot.ui')
#ui_builder = Ui_LidarPlot()

class LidarPlot(qtw.QWidget):
    
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        # UI Generation #################    
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': TimestampAxisItem(orientation='bottom')})
        self.clear_button = qtw.QPushButton('Clear')
        self.pause_button = qtw.QPushButton('Pause')
        
        
        #main layout
        self.setLayout(qtw.QVBoxLayout())
        
        # add plot widget
        self.layout().addWidget(self.plot_widget)
        
        # add horizonatl row of buttons
        self.button_layout = qtw.QHBoxLayout()
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.clear_button)
        self.layout().addLayout(self.button_layout)

        self.show()
        #############################
        
        ## Class instance variables
        self.buffer_size = 20 # number of data points to plot when scrolling
        self.x = []
        self.buffer = []
        self.plot_buffer = self.buffer.copy()
        self.plot_mode = LidarPlotMode.SCROLLING
        self.data_curve = self.plot_widget.plot()

        ## Connecting signals
        self.pause_button.released.connect(self.updateData)
        self.clear_button.released.connect(self.clearData)
        
    def plotData(self):
        self.data_curve.setData(self.x, self.buffer)
    
    def updateData(self):
        y = random.random()*5
        self.buffer.append(y)
        if len(self.buffer) >= self.buffer_size:
            self.buffer.pop(0)
            self.x[:-1] = self.x[1:] #rotate values left
            self.x[-1] = (self.x[-1] + 0.9) #add new larger value
        else:
            self.x = list(range(len(self.buffer)))

        self.plotData()

    def clearData(self):
        self.buffer = []
        self.x = []
        self.plotData()

t = qtc.QDateTime()
class TimestampAxisItem(pg.AxisItem):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)

    def tickStrings(self, values, scale, spacing):
        
        return [t.addSecs(v).toString('mm:ss') for v in values ]

class LidarPlotMode(Enum):
    SCROLLING = auto()  # 1
    ALL = auto()        # 2
    

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    plot_widget = LidarPlot()
    sys.exit(app.exec_())