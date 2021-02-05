import sys
import os
import pyqtgraph as pg
from PyQt5 import QtCore as qtc, QtWidgets as qtw
import random
from enum import Enum, auto
import time
import math
import re
from collections import deque

#Ui_LidarPlot, baseClass = uic.loadUiType('Ui_LidarPlot.ui')
#ui_builder = Ui_LidarPlot()

class LidarPlot(qtw.QWidget):
    
    #"External" signals meant to be connected to other modules
    sig_log_event = qtc.pyqtSignal(str)
    ##########################################################

    #"Internal" signals to invoke methods of LidarLogger
    sig_read_last_n_lines = qtc.pyqtSignal(int)
    sig_read_first_n_lines = qtc.pyqtSignal(int)
    sig_write_line = qtc.pyqtSignal(str)
    #####################################################

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
        
        # add horizontal row of buttons
        self.button_layout = qtw.QHBoxLayout()
        buttons = [self.pause_button, self.clear_button, self.mode_button]
        for b in buttons:
            self.button_layout.addWidget(b)
        
        self.layout().addLayout(self.button_layout)

        #self.show()
        #############################
        
        ## Class instance variables
        self.buffer_size = 20 # number of data points to plot when scrolling
        self.x = []
        self.buffer = []
        self.plot_buffer = self.buffer.copy()
        self.plot_mode = LidarPlotMode.SCROLLING
        self.data_curve = self.plot_widget.plot()   # create data curve object

        ## Instantiate logger object and threads
        self.data_logger = LidarLogger()
        self.data_logger_thread = qtc.QThread(self)
        #####################################
        
        ## Connecting signals ###############################
        #GUI signals
        self.pause_button.released.connect(self.updateData)
        self.clear_button.released.connect(self.clearData)
        self.mode_button.released.connect(self.changeMode)

        #Thread signals
        self.sig_read_first_n_lines.connect(self.data_logger.getReadFirstNSlot())
        self.sig_read_last_n_lines.connect(self.data_logger.getReadLastNSlot())
        self.sig_write_line.connect(self.data_logger.getWriteSlot())
        ###################################################

        #Allocate objects to threads and start
        self.data_logger.moveToThread(self.data_logger_thread)
        self.data_logger_thread.start()

    def changeMode(self):
        if self.plot_mode == LidarPlotMode.SCROLLING:
            self.plot_mode = LidarPlotMode.ALL
        else: 
            self.plot_mode = LidarPlotMode.SCROLLING

    def plotData(self):
        self.data_curve.setData(self.x, self.buffer)
    
    def updateData(self, data: qtc.QByteArray):
        y, epoch = self.parseData(data)
        
        #send data to LidarLogger
        data_log_str = str(epoch) + ',' + str(y)
        self.sig_write_line.emit(str(data_log_str))

        #plot data
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

        [numeric data]_[epoch timestamp]
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

    # Accessor methods for modularity
    def getLogSignal(self):
        return self.sig_log_event
    ###############################

class ThreadWorker(qtc.QRunnable):
    
    def __init__(self, fn, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.fn
        self.args = args
        self.kwargs = kwargs

class LidarLogger(qtc.QObject):
    '''
    Class responsible for logging all plotted data to CSV. Meant to run in separate thread
    '''
    sig_return = qtc.pyqtSignal(list)

    default_file = 'data_file.csv'
    default_folder = os.path.dirname(__file__)

    def __init__(self,path=None,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
        if path == None:
            self.data_path = self.__defaultPath()
        else:
            self.data_path = path

    def __defaultPath(self):
        default_path = os.path.join(self.default_folder, time.strftime("%Y_%m_%d") + self.default_file)
        default_path = self.findFileNum(default_path)
        return default_path

    def writeLine(self,msg: str):
        with open(self.data_path, 'a', newline='') as f:
            f.write(msg)
            f.write('\n')

    def readFirstNLines(self,n,delim=','):
        '''
        Returns the first n lines of self.data_path
        '''
        out_list = []
        with open(self.data_path, 'r', newline='') as f:
            for i in range(n):
                read_str = f.readline()
                if read_str == "": #if EOF reached
                    break
                else:
                    #format data as 2D list
                    read_str = read_str.replace('\n','') #remove trailing newline
                    out_list.append(read_str.split(delim))

        self.sig_return.emit(out_list) #return 

    def readLastNLines(self,n,delim=','):
        with open(self.data_path) as f:
            lastn = deque(f,n)
        
        #formatting data as 2D List
        out_list = map(lambda x: x.replace('\n',''), lastn)
        out_list = map(lambda x: x.split(delim),out_list)

        self.sig_return.emit(out_list) #return

    def findFileNum(self,path):
        '''
        if path exists append (#) just before file extension
        '''
        m = re.match(".*(\.).*$",path)
        ind_period = m.span(1)[0] #index of period before file extension
        
        path0 = path
        num = 1
        while(1): 
            if os.path.exists(path0): 
                path0 = path[:ind_period] + "({})".format(num) + path[ind_period:]
                num += 1
            else:
                break
        
        return path0

    # Accessors for modularity ###############
    def getReturnSig(self) -> qtc.pyqtSignal:
        return self.sig_return

    def getLogPath(self):
        return self.data_path
    
    def getWriteSlot(self):
        return self.writeLine
    
    def getReadFirstNSlot(self):
        return self.readFirstNLines
    
    def getReadLastNSlot(self):
        return self.readLastNLines
    ##########################################

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