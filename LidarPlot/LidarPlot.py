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
import traceback

class LidarPlot(qtw.QWidget):
    
    #"External" signals meant to be connected to other modules
    sig_log_event = qtc.pyqtSignal(str)
    ##########################################################

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        # UI Generation #################    
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': TimestampAxisItem(orientation='bottom')})
        self.clear_button = qtw.QPushButton('Clear')
        self.pause_button = qtw.QPushButton('Pause')
        self.pause_button.setCheckable(True)
        #self.mode_button = qtw.QPushButton('Mode')
        
        #main layout
        self.setLayout(qtw.QVBoxLayout())
        
        # add plot widget
        self.layout().addWidget(self.plot_widget)
        
        # add horizontal row of buttons
        self.button_layout = qtw.QHBoxLayout()
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.clear_button)
        #self.button_layout.addWidget(self.mode_button)
        self.layout().addLayout(self.button_layout)
        #############################
        
        ## Class instance variables
        self.pause_flag = False
        self.plot_points = 80 # number of points to maintain on scrolling plot
        self.buffer_size = 200 # number of data points to hold in memory
        self.x = []
        self.buffer = []        #retains the last buffer_size readings from server      
        self.plot_buffer = self.buffer.copy()   #a subsection of buffer that is plotted
        self.data_curve = self.plot_widget.plot()   # create data curve object

        ## Instantiate logger object and threads
        self.data_logger = LidarLogger()
        #self.data_logger_thread = qtc.QThread(self)
        self.thread_pool = qtc.QThreadPool(self)
        #####################################
        
        ## Connecting signals ###############################
        #GUI signals
        self.pause_button.toggled.connect(self.setPauseFlag)
        self.clear_button.released.connect(self.clearData)
        #self.mode_button.released.connect(self.changeMode)

    def setPauseFlag(self,state: bool):
        self.pause_flag = state

    def plotData(self):
        if (not self.pause_flag):
            self.data_curve.setData(self.x[-self.plot_points:], self.buffer[-self.plot_points:])
    
    def updateData(self, data: qtc.QByteArray):
        #parse byte data received
        y, epoch = self.parseData(data)
        
        #send data to LidarLogger
        data_log_str = str(epoch) + ',' + str(y)                                            
        worker = ThreadWorker(self.data_logger.writeLine, data_log_str) #Instantiatie worker object
        worker.signals.sig_error.connect(lambda x: self.sig_log_event.emit("LidarLogger::" + x))  #connect error callback signals    
        self.thread_pool.globalInstance().start(worker) #start in any available thread

        #add data to buffers
        self.buffer.append(y)   #most recent data is at end
        self.x.append(epoch)
        if (len(self.buffer) >= self.buffer_size):
            self.buffer.pop(0)
            self.x.pop(0)
        else:
            pass

        self.plotData()

    def parseData(self, data: qtc.QByteArray):
        '''
        Parses a QByteArray expecting the following format:

        [epoch timestamp],[distance],[ToF],...
        '''
        # decode data from bytes into string
        data_str = data.data().decode('utf-8')
        
        data_list = data_str.split(',')
        epoch = float(data_list[0])
        dist = float(data_list[1])
        print(dist, epoch)

        return dist, epoch

    def clearData(self):
        self.buffer = []
        self.x = []
        self.plotData()

    # Accessor methods for modularity
    def getLogSignal(self):
        return self.sig_log_event
    
    def getDataSlot(self):
        return self.updateData
    ###############################

class ThreadWorker(qtc.QRunnable):
    '''
    This class provides a generic way of using QThreadPool.
    When initializing ThreadWorker, pass the function to execute in a thread
        as well as necessary arguments. Connect the provided signals if needed
    Then pass the object to QThreadpool.start method
    '''
    
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = ThreadWorkerSignals()

    @qtc.pyqtSlot()
    def run(self): #overloaded function
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            self.signals.sig_error.emit(traceback.format_exc())
        else:
            self.signals.sig_return.emit(result)  # Return the result of the processing
        finally:
            self.signals.sig_finished.emit()  # Done

class ThreadWorkerSignals(qtc.QObject):
    '''
    Holds the signals associated with ThreadWorker. ThreadWorker
    does not inherit from QObject and thus cannot make custom signals
    '''

    sig_finished = qtc.pyqtSignal()     #signal to notify parent threads of task completion
    sig_error = qtc.pyqtSignal(str)   #if error, return error data in tuples
    sig_return = qtc.pyqtSignal(object) #signal to return parameters of any type
    
    
class LidarLogger(qtc.QObject):
    '''
    Class that encapsulates all logging functionality
    '''

    default_file = 'lidarplot_datafile.csv'
    default_folder = os.path.dirname(__file__)

    def __init__(self,path=None,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
        if path == None:                            #if no path provided ...
            self.data_path = self.__defaultPath()   #...use the default path
        else:
            self.data_path = path    
            

    def __defaultPath(self):
        '''
        Generates a path to a timestamped file with leaf default_file
        '''
        default_path = os.path.join(self.default_folder, time.strftime("%Y_%m_%d") + self.default_file)
        default_path = self.findFileNum(default_path)
        return default_path

    def writeLine(self,msg: str) -> int:
        with open(self.data_path, 'a', newline='') as f:
            write_status = f.write(msg + '\n')
        return write_status

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

    def readLastNLines(self,n,delim=','):
        with open(self.data_path) as f:
            lastn = deque(f,n)
        
        #formatting data as 2D List
        out_list = map(lambda x: x.replace('\n',''), lastn)
        out_list = map(lambda x: x.split(delim),out_list)

    def findFileNum(self,path):
        '''
        if path exists append a number (#) just before file extension
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


class TimestampAxisItem(pg.AxisItem):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)

    def tickStrings(self, values, scale, spacing):
        '''
        This class defines for the pyqtgraph module a means of converting a UNIX timestamp
        into axis tickmarks. This is done by converting the raw axis data (UNIX timestamp with fractional part)
        into a timestamp string
        '''
        vs = [v*scale for v in values] #retrieve raw x-axis data (UNIX timestamp form [secs].[msecs] from Epoch)
        tick_str = []
        for v in vs:
            l = str(v).split('.') #split number to get seconds and milliseconds part
            out = time.strftime("%Y %b %d\n%H:%M:%S", time.gmtime(int(l[0]))) #use seconds to get timestamp string
            out += "." + l[1] #append decimal point and milliseconds
            out += " GMT" #append timezone
            tick_str.append(out)
        
        return tick_str
    

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    plot_widget = LidarPlot()
    sys.exit(app.exec_())