from socket import *
import sys
import os

welcomePort = int(sys.argv[1])
SINGLE_SPACE = " "
SINGLE_SPACE_BYTE = SINGLE_SPACE.encode('utf-8')
DOUBLE_SPACE = "  "

### PrematureConnectionSocketClosureException:
### Indicates the connectionSocket closed before the request message was completed
###
class ConnectionSocketClosureException(Exception):
    pass

### The WebServer that listens to TCP Connections
###
class WebServer():

    def __init__(self, welcomePort):
        self.welcomePort = welcomePort
        self.keyValueStore = dict()

    def start(self):
        welcomeSocket = socket(AF_INET, SOCK_STREAM)
        welcomeSocket.bind(('', self.welcomePort))
        self.waitForTCPConnection(welcomeSocket)

    def waitForTCPConnection(self, welcomeSocket):
        welcomeSocket.listen(5)

        while True:
            self.handleClientSocket(*welcomeSocket.accept())

    def handleClientSocket(self, connectionSocket, addr):
            
        while True:
            try:
                message = self.readBytesUntilDoubleSpace(connectionSocket)
                request = HttpRequest(message)

                # Invalid request message, continue to read next request
                if request.method == HttpRequest.INVALID_METHOD:
                    continue
                
                request.content = self.getContent(connectionSocket, request.contentLength)
                response, content = self.formHttpResponse(request)
                self.sendHttpResponse(connectionSocket, response, content)
                
            except ConnectionSocketClosureException:
                break

        connectionSocket.close()
        
    ## Read from the TCP stream until a double space is encountered        
    def readBytesUntilDoubleSpace(self, connectionSocket):
        message = list()
    
        firstByte = connectionSocket.recv(1)
        if not firstByte:
            raise ConnectionSocketClosureException
        secondByte = connectionSocket.recv(1)
        if not secondByte:
            raise ConnectionSocketClosureException

        message.append(firstByte)
        message.append(secondByte)

        while not firstByte == SINGLE_SPACE_BYTE\
              or not secondByte == SINGLE_SPACE_BYTE:
            firstByte = secondByte
            secondByte = connectionSocket.recv(1)            
            if not secondByte:
                # Client closed connection before request message was complete
                raise ConnectionSocketClosureException
            message.append(secondByte)

        return bytearray(message)

    ## Read in content data of length n
    def getContent(self, connectionSocket, n):
        if n == 0:
            return None
        data = list()

        for i in range(n):
            d = connectionSocket.recv(1)     
            if not d:
                raise ConnectionSocketClosureException
            data.append(d)
        return bytearray(data)

    def formHttpResponse(self, request):
        if request.subserver == HttpRequest.FILE_SUBSERVER:
            return self.formHttpResponse_FileServing(request)
        elif request.subserver == HttpRequest.KEY_SUBSERVER:
            return self.formHttpResponse_KeyValueStore(request)

    def formHttpResponse_FileServing(self, request):
        if not (os.path.isfile(request.path)):
            return HttpResponse("404 NotFound"), None

        try:
            with open(request.path) as f:
                data = f.read()
            return HttpResponse("200 OK", len(data)), data
        except IOError:
            return HttpResponse("403 Forbidden"), None

    def formHttpResponse_KeyValueStore(self, request):
        keyValue = request.path

        if request.method == HttpRequest.POST_METHOD:
            self.keyValueStore[keyValue] = request.content
            return HttpResponse("200 OK"), None

        elif request.method == HttpRequest.GET_METHOD:
            if not keyValue in self.keyValueStore.keys():
                return HttpResponse("404 NotFound"), None

            data = self.keyValueStore[keyValue]
            return HttpResponse("200 OK", len(data)), data

        elif request.method == HttpRequest.DELETE_METHOD:
            if not keyValue in self.keyValueStore.keys():
                return HttpResponse("404 NotFound"), None

            data = self.keyValueStore.pop(keyValue)
            return HttpResponse("200 OK", len(data)), data
                            
    def sendHttpResponse(self, connectionSocket, response, content):
        connectionSocket.send(response.formatString().encode('utf-8'))
        if content:
            connectionSocket.send(content)

### A HTTPRequest class to reprsent such a request.
###
class HttpRequest():

    POST_METHOD = "POST"
    GET_METHOD = "GET"
    DELETE_METHOD = "DELETE"
    INVALID_METHOD = ""
    VALID_METHODS = [POST_METHOD, GET_METHOD, DELETE_METHOD]
    CONTENT_LENGTH = "content-length"    
    FILE_SUBSERVER = "file"
    KEY_SUBSERVER = "key"
    VALID_SUBSERVERS = [FILE_SUBSERVER, KEY_SUBSERVER]
    
    def __init__(self, header):
        self.header = "".join(header.decode('utf-8'))
        self.method = HttpRequest.INVALID_METHOD
        self.subserver = ""
        self.path = ""
        self.contentLength = 0
        self.content = None
        self.parseRequest()
        
    def parseRequest(self):
        self.method = self.header.split()[0].upper()   # Case-insensitive
        header_path = self.header.split()[1]
        self.subserver = header_path.split("/")[1]     # Case-sensitive
        self.path = header_path.split("/")[2]          # Case-sensitive

        if not self.method in HttpRequest.VALID_METHODS:
            self.invalidMethod()
            return
            
        if not self.subserver in HttpRequest.VALID_SUBSERVERS:
            self.invalidMethod()
            return

        if self.method == HttpRequest.POST_METHOD:
            if self.subserver == HttpRequest.FILE_SUBSERVER:
                self.invalidMethod()
                return
            else:
                self.parseContentLength()
            
    def parseContentLength(self):
        splitMessage = self.header.split()
        
        for i in range(2, len(splitMessage) - 1, 2):
            # Search for the content-length header field
            if splitMessage[i].lower() == HttpRequest.CONTENT_LENGTH:
                self.contentLength = int(splitMessage[i + 1])
                return

        # Invalid POST method, no content-length header field
        self.invalidMethod()

    def invalidMethod(self):
        self.method = HttpRequest.INVALID_METHOD
        
### A HTTPResponse class to reprsent such a response.
###
class HttpResponse():

    CONTENT_LENGTH = "content-length"    

    def __init__(self, status, contentLength=0):
        self.status = status
        self.contentLength = contentLength

    def formatString(self):
        if self.contentLength:
            contentLengthHeader = HttpResponse.CONTENT_LENGTH + \
                    SINGLE_SPACE + str(self.contentLength)
            return self.status + SINGLE_SPACE + contentLengthHeader + \
                   DOUBLE_SPACE

        return self.status + DOUBLE_SPACE
        
ws = WebServer(welcomePort)
ws.start()
