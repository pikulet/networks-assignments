#######################################################
# MODIFY THE FOLLOWING TO SUIT YOUR PROGRAM
#######################################################
# Write what you use in your program as method descriptions
responseCodes = { "200" : "OK", "403" : "Forbidden", "404" : "NotFound" }

# Write what you used as content-length, because you might have
# different case e.g. "Content-Length".
contentLength = "content-length"

# Choose your port number
serverPort = 10003

# Disable tests that you don't want
KVSTest = True          # Key-value store test
FILETest = True         # File serving test
PERSISTENCYTest = True  # Persistence test
ROBUSTTest = True       # Robustness test
MULTIPACKETTest = True  # Multi packet test

# Copy CS2105_Assignment_1.pdf to your webserver folder, as well as the
# directory where you are running this client.
PdfCopied = True    # Disable if you haven't

#######################################################
#######################################################

# Setup
from socket import *
import os
serverName = 'sunfire.comp.nus.edu.sg'

# Send the server the test, and receive a response to compare with ans. Return
# currScore + 1 if correct, currScore otherwise.
def testSend(test, ans, currScore, cs = None):
    pipelined = cs is not None
    # For non pipelining test, create new socket every test
    if (not pipelined):
        cs = socket(AF_INET, SOCK_STREAM)
        cs.connect((serverName, serverPort))
    cs.send(test.encode())
    response = cs.recv(1024)
    print('Send: ' + test + '\nRecv:', response.decode('ascii', 'replace'))
    if (not pipelined): cs.close()
    if response == ans.encode(): print("PASS ✓"); return currScore + 1
    else: print("FAIL ✗"); return currScore

# Use this to easily send queries to the server.
# Usage: manualSend("get /key/abc  ")
def manualSend(test, awaitResponse = True):
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    print('Send:', test)
    cs.sendall(test.encode())
    if awaitResponse:
        response = cs.recv(1024)
        print('Recv:', response.decode())
    else:
        print("Not awaiting response, check server side if it didn't crash.")
    cs.close()

# Use this to receive a large file from the server.
# Usage: getLargeFile("CS2105_Assignment_1.pdf", "pdf.pdf")
def getLargeFile(filename, outputname, preview = True):
    # Create socket
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    # Send request
    print('Send:', 'get /file/' + filename + '  ')
    cs.sendall(('get /file/' + filename + '  ').encode())
    # Receive first packet
    firstPart = cs.recv(1024)
    received = firstPart.split(b' ', 5)
    sizeLeft = int(received[3]) - len(received[5])
    data = received[5]
    # receive the rest of packets until sizeLeft = 0
    while sizeLeft > 0:
        part = cs.recv(1024)
        data += part
        sizeLeft -= len(part)
    with open(outputname, "wb") as f:
        f.write(data)
    if preview: print('Recv:', data.decode('ascii', 'replace'))
    cs.close()

#######################################################
# KEY-VALUE STORE TESTS
#######################################################
if KVSTest:
    print("----------------\nKey-Value Store Tests\n----------------")
    kvsTestScore = 0; kvsTotal = 8;

    # Fill up the dictionary
    test = 'post /key/abc content-length 3  cba'
    ans = '200 ' + responseCodes["200"] + '  '
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Get a correct value
    test = 'get /key/abc  '
    ans = '200 ' + responseCodes["200"] + ' ' + contentLength + ' 3  cba'
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Get a wrong value (case sensitive)
    test = 'get /key/abC  '
    ans = '404 ' + responseCodes["404"] + '  '
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Delete an existing value
    test = 'delete /key/abc  '
    ans = '200 ' + responseCodes["200"] + ' ' + contentLength + ' 3  cba'
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Get a non-existing value
    test = 'get /key/abc  '
    ans = '404 ' + responseCodes["404"] + '  '
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Delete a non-existing value
    test = 'delete /key/abc  '
    ans = '404 ' + responseCodes["404"] + '  '
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Post a binary value
    test = 'post /key/binary content-length 6  ' + chr(255) + chr(245) + chr(129)
    ans = '200 ' + responseCodes["200"] + '  '
    kvsTestScore = testSend(test, ans, kvsTestScore)

    # Get a binary value
    test = 'get /key/binary  '
    ans = '200 ' + responseCodes["200"] + ' ' + contentLength + ' 6  ' + chr(255) + chr(245) + chr(129)
    kvsTestScore = testSend(test, ans, kvsTestScore)

    print("Key-value store test:", kvsTestScore, "/", kvsTotal, "\n")

#######################################################
# FILE SERVER TEST
#######################################################
if FILETest:
    print("----------------\nFile Server Tests\n----------------")
    fileTestScore = 0; fileTotal = 2 if PdfCopied else 1;

    # Test on a text file
    outputPath = "Output.txt"
    getLargeFile("CS2105.txt", outputPath)
    ans = b"Intro To Computer Networks!"
    with open (outputPath, "rb") as f:
        data = f.read()
        if data == ans:
            print("PASS ✓")
            fileTestScore += 1
        else:
            print("FAIL ✗")
    os.remove(outputPath)

    # Test on a binary file
    if PdfCopied:
        outputPath = "Output.pdf"
        getLargeFile("CS2105_Assignment_1.pdf", outputPath, False)
        with open ("CS2105_Assignment_1.pdf", "rb") as f:
            ans = f.read()
        with open (outputPath, "rb") as f:
            data = f.read()
            if data == ans:
                print("PASS ✓")
                fileTestScore += 1
            else:
                print("FAIL ✗")
        os.remove(outputPath)

    print("File server test:", fileTestScore, "/", fileTotal, "\n")

#######################################################
# PIPELINING TEST
#######################################################
if PERSISTENCYTest:
    print("----------------\nPersistency Tests\n----------------")
    persistenceTestScore = 0; persistenceTotal = 5;
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))

    test = 'post /key/laugh conTent-LeNgTh 5  HUHUE'
    ans = '200 ' + responseCodes["200"] + '  '
    persistenceTestScore = testSend(test, ans, persistenceTestScore, cs)

    test = 'get /key/laugh  '
    ans = '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  HUHUE'
    persistenceTestScore = testSend(test, ans, persistenceTestScore, cs)

    test = 'delete /key/laugh  '
    ans = '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  HUHUE'
    persistenceTestScore = testSend(test, ans, persistenceTestScore, cs)

    test = 'get /key/laugh  '
    ans = '404 ' + responseCodes["404"] + '  '
    persistenceTestScore = testSend(test, ans, persistenceTestScore, cs)

    test = 'delete /key/laugh  '
    ans = '404 ' + responseCodes["404"] + '  '
    persistenceTestScore = testSend(test, ans, persistenceTestScore, cs)

    cs.close()
    print("nPersistency test:", persistenceTestScore, "/", persistenceTotal, "\n")

#######################################################
# ROBUSTNESS TEST
#######################################################
if ROBUSTTest:
    print("----------------\nRobustness Tests\n----------------")
    robustTestScore = 0; robustTotal = 8;

    # Legit method but with extra unknown headers
    robustTestScore = testSend('POST /key/neigh Content-Length 5 user-agent Mozilla Connection: Keep-Alive  HUHUE', \
                               '200 ' + responseCodes["200"] + '  ', robustTestScore)
    robustTestScore = testSend('GET /key/neigh Apples Connection: Keep-Alive  ', \
                               '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  HUHUE', robustTestScore)
    robustTestScore = testSend('DELete /key/neigh user-agent Mozilla Connection: Keep-Alive  ', \
                               '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  HUHUE', robustTestScore)

    # Not key/file, for get, post and delete
    robustTestScore = testSend('get /abc/laugh  ', \
                               '404 ' + responseCodes["404"] + '  ', robustTestScore)
    robustTestScore = testSend('POST /aba/laugh content-Length 5  HUHUE', \
                               '404 ' + responseCodes["404"] + '  ', robustTestScore)
    robustTestScore = testSend('delete /add/abc  ', \
                               '404 ' + responseCodes["404"] + '  ', robustTestScore)

    # Unrecognized header
    manualSend('abced yolo  ', False)
    # If the above was ignored, this test will pass. If you lose score on this, handle
    # unrecognized headers.
    robustTestScore = testSend('post /key/laugh conTent-LeNgTh 5  HUHUE', \
                               '200 ' + responseCodes["200"] + '  ', robustTestScore)

    # Unrecognized header with no value
    manualSend('lala  ', False)
    # If the above was ignored, this test will pass. If you lose score on this, handle
    # unrecognized headers.
    robustTestScore = testSend('get /key/laugh  ', \
                               '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  HUHUE', robustTestScore)

    print("Robustness Test:", robustTestScore, "/", robustTotal, "\n")

#######################################################
# MULTI PACKET TEST
#######################################################
if MULTIPACKETTest:
    print("----------------\nMulti Packet Tests\n----------------")
    multiTestScore = 0; multiTotal = 4;

    # POST
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    print('Send:', 'POST /key/aaa ')
    cs.sendall('POST /key/aaa '.encode())
    print('Send:', 'Content-Length 5  ')
    cs.sendall('Content-Length 5  '.encode())
    multiTestScore = testSend('bbbbb', '200 ' + responseCodes["200"] + '  ', multiTestScore, cs);
    cs.close()

    # GET
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    print('Send:', 'GET /key/')
    cs.sendall('GET /key/'.encode())
    print('Send:', 'aaa ')
    cs.sendall('aaa '.encode())
    multiTestScore = testSend(' ', '200 ' + responseCodes["200"] + ' ' + contentLength + ' 5  bbbbb', multiTestScore, cs);
    cs.close()

    # DELETE
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    print('Send:', 'DELETE /ke')
    cs.sendall('DELETE /ke'.encode())
    print('Send:', 'y/aaa  ')
    cs.sendall('y/aaa'.encode())
    multiTestScore = testSend('  ', '200 ' + responseCodes["200"] + ' ' + contentLength +  ' 5  bbbbb', multiTestScore, cs);
    cs.close()

    # FILE GET
    cs = socket(AF_INET, SOCK_STREAM)
    cs.connect((serverName, serverPort))
    print('Send:', 'get /')
    cs.sendall(('get /').encode())
    print('Send:', 'file/CS2105.txt')
    cs.sendall(('file/CS2105.txt').encode())
    print('Send:', '  ')
    cs.sendall(('  ').encode())
    data = cs.recv(1024)
    ans = ("200 " + responseCodes["200"] + ' ' + contentLength +  " 27  Intro To Computer Networks!").encode()
    if data == ans:
        print("PASS ✓")
        multiTestScore += 1
    else:
        print("FAIL ✗")

    print("Multi packet test:", multiTestScore, "/", multiTotal, "\n")
