import binascii
import socket

##Open a test PSM message
filename = 'test_sae_psm.txt'
with open(filename, 'rb') as f:
    content = f.read()
print(binascii.hexlify(content))
##Encode for sending to an RSU
bytesToSend         = content
#bytesToSend         = str.encode(content)
##Setup an RSU that will receive the PSM on port 62451
serverAddressPort   = ("10.X.X.X", 62451)
bufferSize          = 1024

## Send the message
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.sendto(bytesToSend, serverAddressPort)
