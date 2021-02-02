from PyQt5 import QtCore as qtc
from PyQt5.QtNetwork import QTcpSocket
socket = QTcpSocket()

meta = socket.staticMetaObject
x = meta.enumerator(meta.indexOfEnumerator('SocketState')).valueToKey(6)
print(socket.errorString())
