from PyQt5 import QtCore as qtc
import traceback

class QtThreadWorker(qtc.QRunnable):
    '''
    This class provides a generic way of using QThreadPool.
    When initializing ThreadWorker, pass the function to execute in a thread
        as well as necessary arguments. Connect the provided signals if needed
    Then pass the object to QThreadpool.start method
    '''

    class QtThreadWorkerSignals(qtc.QObject):
        '''
        Holds the signals associated with ThreadWorker. ThreadWorker
        does not inherit from QObject and thus cannot make custom signals
        '''

        sig_finished = qtc.pyqtSignal()     #signal to notify parent threads of task completion
        sig_error = qtc.pyqtSignal(str)   #if error, return error data in tuples
        sig_return = qtc.pyqtSignal(object) #signal to return parameters of any type
    
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = self.QtThreadWorkerSignals()

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
