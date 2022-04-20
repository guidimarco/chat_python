"""
    CLIENT script:
        1) create TCP socket for server connection
        2) set valid credentials ( nickname, IP, port )
        3) start server thread ( TCP )
        4) start UDP-server for client-client comm
"""

# =============================================================================
# IMPORT ALL PACKAGES
# =============================================================================

import socket
import socketserver
import threading

import sys

# =============================================================================
# GLOBAL VARS
# =============================================================================

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8080

NICK = None
IP = None
PORT = None

CHAT_NICK = None
CHAT_IP = None
CHAT_PORT = None

NEW_LINE = "\r\n"

CODE_START = "/*"
CODE_END = "*/"
COMM_START = "!"

PYCHAT = "PyChat> "

# =============================================================================
# FUNCTIONS (0) Getter and setter
# =============================================================================

def setChatInfo( info, reset=False ):
    global CHAT_NICK, CHAT_IP, CHAT_PORT
    if reset:
        CHAT_NICK, CHAT_IP, CHAT_PORT = [None, None, None]
    else:
        CHAT_NICK, CHAT_IP, CHAT_PORT = info.split("|")

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def recvServerMsg( serverSkt ):
    data = serverSkt.recv( 1024 )
    msg = data.decode()

    msgList = msg.split( CODE_END )
    code = msgList[0][2:]
    opt = None if len( msgList ) == 1 else msgList[1]

    return [ code, opt ]

def sendServerMsg( skt, code, opt=None ):
    reply = str( CODE_START + code + CODE_END + opt )
    
    skt.sendall( reply.encode() )

def startNewChat( opt ):
    global CHAT_NICK, CHAT_IP, CHAT_PORT
    CHAT_NICK, CHAT_IP, CHAT_PORT = opt.split( "|" )

    print( f"{NEW_LINE}-----{NEW_LINE}" +
        f"New chat with {CHAT_NICK}" +
        f"{NEW_LINE}-----{NEW_LINE}" )


def deserializeUserMsg( msg ):
    code = False
    if COMM_START in msg and msg.index( COMM_START ) == 0:
        msgList = msg.split()
        code = msgList[0][1:]
        msg = "" if len( msgList ) == 1 else msgList[1]

        if code == "QUIT":
            msg = NICK
        elif code == "CHAT" and msg == NICK:
            print( f"{PYCHAT}You cannot chat with yourself. Find another user with !ALL" )
            code = False
            msg = ""
    return [code, msg]

# =============================================================================
# PART (1) Connect to server
# =============================================================================

print( f"{NEW_LINE}-----{NEW_LINE}" +
    "Hi! Welcome to PyChat" +
    f"{NEW_LINE}-----{NEW_LINE}" )

try:
    serverSkt = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    serverSkt.connect( (SERVER_IP, SERVER_PORT) )
    IP, PORT = serverSkt.getsockname()
except socket.error as ex:
    print( f"{PYCHAT}Failed connecting to the server. Error: {ex}" )
    sys.exit()

# =============================================================================
# PART (2) Connect to server
# =============================================================================

# Functions

def getUserInfo():
    global NICK
    while True:
        inputsList = input(
            f"{PYCHAT}Insert your nickname, IP address and port: "
        ).split()

        if len( inputsList ) < 3:
            print( f"{PYCHAT}Enter 3 values" )
            continue
        
        NICK = inputsList[0]
        break

def checkCredentials( skt ):
    global NICK, IP, PORT
    sendServerMsg( skt, "START", f"{NICK}|{IP}|{PORT}" )

    code, msg = recvServerMsg( skt )
    print( f"{NEW_LINE}" + msg )

    if code == "ERR":
        NICK = None

# Script

while NICK == None:
    getUserInfo()
    checkCredentials( serverSkt )

# =============================================================================
# PART (3) Start server thread
# =============================================================================

# Functions

def serverThread( serverSkt ):
    while True:
        msg = input( f"{NICK}> " )
        code, msg = deserializeUserMsg( msg )

        if code:
            sendServerMsg( serverSkt, code, msg )

            code, msg = recvServerMsg( serverSkt )
            print( f"{PYCHAT}{msg}" )

            if code == "CHAT" and CHAT_NICK == None:
                setChatInfo( info=msg )
                startNewChat( msg )
            elif code == "CHAT":
                print( f"{PYCHAT}You're already chatting." )
            elif code == "QUIT":
                serverSkt.close()
                print( f"{NEW_LINE}-----{NEW_LINE}" +
                    "PyChat closed" +
                    f"{NEW_LINE}-----{NEW_LINE}" )
                sys.exit()
    # elif not CHAT_NICK == None:
    #     clientSkt.sendto( msg.encode(), (CHAT_IP, int(CHAT_PORT)) )
    # else:
    #     print( f"{PYCHAT}You're not in a chat!" )

# Script

serverThread = threading.Thread( target=serverThread, args=(serverSkt,) )
serverThread.start()
serverThread.join()

# =============================================================================
# SCRIPT (1) Check the user info
# =============================================================================

# clientSkt = socketserver.UDPServer( (CHAT_IP, CHAT_PORT), ChatRequestHandler )

# try:
#     clientSkt = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
#     clientSkt.bind( (IP, PORT) )
# except socket.error as ex:
#     print( f"{PYCHAT}Failed creating socket UDP. Error: {ex}" )
#     serverSkt.close()
#     print( f"{NEW_LINE}-----{NEW_LINE}PyChat closed{NEW_LINE}-----{NEW_LINE}" )
#     sys.exit()