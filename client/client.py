#following this tutorial https://www.geeksforgeeks.org/socket-programming-python/

import socket

s = socket.socket()

port = 12345

s.connect(('127.0.0.1', port))

print (s.recv(1024) )

s.close()
