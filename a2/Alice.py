import sys
import random
import math
from socket import *
from zlib import crc32

# Define constants
HEADER_SIZE = 6
MAX_PACKET_SIZE = 64
PAYLOAD_SIZE = MAX_PACKET_SIZE - HEADER_SIZE
NAK = 0

# Set up connection socket
serverName = 'localhost'
serverPort = int(sys.argv[1])
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.050)

# Read data from standard input
data = sys.stdin.buffer.read()
numPacketsRequired = math.ceil(len(data)/PAYLOAD_SIZE)

MAXCRC = 0xffffffff
### Creates a byte packet using the data
### Packet format: (seqNumber, 1) + (data, 59) + (checksum, 4)
seqNumber = -1
maxSeqNumber = 256
def createPacket(i, data):
    global seqNumber

    if i == 0:
        seqNumber = random.randint(0, maxSeqNumber)
    else:
        seqNumber += 1
        seqNumber %= maxSeqNumber

    seqNumberByte = intToBytes(seqNumber, 1)
    checksumData = seqNumberByte + data
    checksumBytes = getCRC(checksumData)
    packet =  checksumData + checksumBytes
    return packet

### Helper method to convert int to bytes
###
def intToBytes(n, bytelength):
    return n.to_bytes(bytelength, byteorder='little')

### Generate the inverse CRC checksum
###
def getCRC(data):
    invChecksum = MAXCRC - (crc32(data) & MAXCRC)
    return intToBytes(invChecksum, 4)

### Checks if the ACK/ NAK packet is corrupted
###
def isCorrupt(replyPacket):
    checksum = crc32(replyPacket) & MAXCRC
    return checksum != MAXCRC

### Checks if the reply packet is a NAK packet
###
def isNAK(replyPacket):
    return replyPacket[0] == NAK

### Checks if the ACK number is the same as the SEQ number
###
def isValid(packet, replyPacket):
    if isCorrupt(replyPacket):
        return False
    elif isNAK(replyPacket):
        return False

    replyACK = replyPacket[1]   # check position
    packetSEQ = packet[0]       # check position

    return replyACK == packetSEQ

### Sends a packet until it is successfully ACKed
###
def sendPacket(p): 
    try:
        clientSocket.sendto(packet, (serverName, serverPort))
        replyPacket, serverAddress = clientSocket.recvfrom(MAX_PACKET_SIZE)
        return isValid(packet, replyPacket)
    except timeout:
        return False

# Send data over unreliable channel
i = 0
for i in range(numPacketsRequired):
    if i != numPacketsRequired - 1:
        packet = createPacket(i, data[i*PAYLOAD_SIZE: i*PAYLOAD_SIZE + PAYLOAD_SIZE])
    else:
        # last packet
        packet = createPacket(i, data[i*PAYLOAD_SIZE: ])

    while True:
        success = sendPacket(packet) 
        if success:
            break
    print("sent packet", packet[0])

clientSocket.close()
