from PyQt5.QtNetwork import QTcpSocket, QHostAddress 
from PyQt5 import QtCore as qtc, QtWidgets as qtw, uic, QtNetwork as qtn

def enum2string(meta_obj: qtc.QObject.staticMetaObject, enum_name: str, enum_val: int):
    return (meta_obj.enumerator(meta_obj.indexOfEnumerator(enum_name)).valueToKey(enum_val))

enum2string(QTcpSocket.staticMetaObject, 'NetworkLayerProtocol', 2)
