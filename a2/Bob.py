import sys
from socket import *
from zlib import crc32

# Set up connection socket
serverName = 'localhost'
serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((serverName, serverPort))

ACK = 1
NAK = 0
MAXCRC = 0xffffffff

lastACKedSeqNumber = -1
maxSeqNumber = 256
### Process a particular message received
###
def process(packet):
    global lastACKedSeqNumber

    expectedSeqNumber = (lastACKedSeqNumber + 1) % maxSeqNumber
    if not isCorrupt(packet):
        seqNumber = packet[0]
        if lastACKedSeqNumber == -1 or seqNumber == expectedSeqNumber: 
            # first packet received or packet is expected
            outputData(packet)
            reply = createReply(seqNumber)
            lastACKedSeqNumber = seqNumber 
        else: 
            # Alice did not receive ACK, resend previous ACK
            reply = createReply(lastACKedSeqNumber)
    else:
        # packet is corrupted
        reply = createNAK()

    checksumBytes = getCRC(reply)
    packet =  reply + checksumBytes
    return packet

### Checks if a packet received is corrupted
###
def isCorrupt(packet):
    checksum = crc32(packet) & MAXCRC
    return checksum != MAXCRC
    
### Helper method to convert int to bytes
###
def intToBytes(n, bytelength):
    return n.to_bytes(bytelength, byteorder='little')

### Generate the inverse CRC checksum
###
def getCRC(data):
    invChecksum = MAXCRC - (crc32(data) & MAXCRC)
    return intToBytes(invChecksum, 4)

### Write the packet content to standard output
###
def outputData(packet):
    data = packet[1: -4]
    sys.stdout.buffer.write(data)

### Craft a reply message
### Packet format: (ACK, 1) + (seqNumber, 1) + (checksum, 4)
###
def createReply(seqNumber):
    ACKByte = intToBytes(ACK, 1)
    seqNumberByte = intToBytes(seqNumber, 1)
    return ACKByte + seqNumberByte

### Craft a NAK message
### Packet format: (NAK, 1) + (checksum, 4)
###
def createNAK():
    return intToBytes(NAK, 1)

while True:
    packet, clientAddress = serverSocket.recvfrom(64)
    replyMessage = process(packet)
    serverSocket.sendto(replyMessage, clientAddress)

