"""
    CLIENT script:
        1) Connect to server: create TCP socket for server connection
        2) Check user credentials: set valid credentials ( nickname, IP, port )
        3) Start server for client-client communication:
            start UDP-server for client-client comm
        4) Start server thread: TCP thread
"""

# =============================================================================
# IMPORT ALL PACKAGES
# =============================================================================

import socket
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
PYCHAT = "PyChat"
NICK_END = ">"

# =============================================================================
# FUNCTIONS (0) Getter and setter
# =============================================================================

def setChatInfo( info="", reset=False ):
    global CHAT_NICK, CHAT_IP, CHAT_PORT
    if reset:
        CHAT_NICK, CHAT_IP, CHAT_PORT = [ None, None, None ]
    else:
        CHAT_NICK, CHAT_IP, CHAT_PORT = info.split("|")
        print( f"{NEW_LINE}*****{NEW_LINE}" +
            f"New chat with {CHAT_NICK}" +
            f"{NEW_LINE}*****{NEW_LINE}" )

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def recvServerMsg( serverSkt ):
    data = serverSkt.recv( 1024 )
    msg = data.decode()

    # deserialize server msg
    msgList = msg.split( CODE_END )
    code = msgList[0][2:]
    opt = None if len( msgList ) == 1 else msgList[1]

    return [ code, opt ]

def sendServerMsg( skt, code, opt=None ):
    # serialize msg for server
    reply = str( CODE_START + code + CODE_END + opt )
    skt.sendall( reply.encode() )

def deserializeUserMsg( msg ):
    code = False
    if ( COMM_START in msg 
    and msg.index( COMM_START ) == 0 ):
        msgList = msg.split()
        code = msgList[0][1:]
        msg = "" if len( msgList ) == 1 else msgList[1]

        if code == "QUIT":
            msg = NICK
        elif code == "CHAT" and msg == NICK:
            print( f"{PYCHAT + NICK_END} You cannot chat with yourself." +
                "Find another user with !ALL" )
            code = False
            msg = ""
        elif code == "END" and CHAT_NICK == None:
            print( f"{PYCHAT + NICK_END} You're not in a chat!" )
            code = False
            msg = ""

    return [ code, msg ]

def deserializeChatMsg( msg ):
    nick = False
    if ( NICK_END in msg
    and msg.index( NICK_END ) != 0 ):
        msgList = msg.split( NICK_END )
        nick = msgList[0]
        msg = msgList[1]
    return [ nick, msg ]

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
    print( f"{PYCHAT + NICK_END} Failed connecting to the server. Error: {ex}" )
    sys.exit()

# =============================================================================
# PART (2) Check user credentials
# =============================================================================

while NICK == None:
    """
        Check user credentials
        -----
        Ask for nickname, IP and port untill the user choose free credentials.
    """
    inputsList = input(
        f"{PYCHAT + NICK_END} Insert your nickname, IP address and port: "
    ).split()

    if len( inputsList ) < 3:
        print( f"{PYCHAT + NICK_END} Enter 3 values" )
        continue
    
    NICK = inputsList[0]

    sendServerMsg( serverSkt, "START", f"{NICK}|{IP}|{PORT}" )

    code, msg = recvServerMsg( serverSkt )
    print( f"{NEW_LINE}" + msg )

    if code == "ERR":
        NICK = None

# =============================================================================
# PART (3) Start server for client-client communication
# =============================================================================

def clientThread( clientSkt ):
    """
        Client-client thread ( UDP socket )
        -----
        This thread listen and process client msg.
        1) Receive client msg
        2) Check sender ( when the chat is on )
        3) Start a new chat ( when the chat is off )
        4) Print message on the screen
    """
    while True:
        try:
            data, addr = clientSkt.recvfrom( 1024 )
        except:
            setChatInfo( reset=True )
            continue
        
        if ( CHAT_NICK != None and
            str(addr[1]) != CHAT_PORT ):
            # 2) Check sender
            clientSkt.sendto( f"I'm already in a chat!".encode(), (addr[0], addr[1]) )
            continue
        nick, msg = deserializeChatMsg( data.decode() )

        if CHAT_NICK == None:
            # 3) Start a new chat
            chatInfo = nick + "|" + addr[0] + "|" + str( addr[1] )
            setChatInfo( info=chatInfo )
        
        print( f"{CHAT_NICK + NICK_END}" + " " + f"{msg}" )

clientSkt = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
clientSkt.bind( (IP, PORT) )

clientThread = threading.Thread( target=clientThread, args=(clientSkt,) )
clientThread.start()

# =============================================================================
# PART (4) Start server thread
# =============================================================================

def serverThread( serverSkt, clientSkt ):
    """
        Client-server thread ( TCP socket )
        -----
        This thread listen and process user msg.
        1) Get and serialize user msg
        2) Process user msg. The msg could have different receiver:
            a) Server > if contain a code 
            b) Client > a chat is on
            c) No-one > otherwise 
    """
    while True:
        inputMsg = f"Write to {PYCHAT}...{NEW_LINE}" if CHAT_NICK == None else f"Write to {CHAT_NICK}...{NEW_LINE}"
        msg = input( inputMsg )
        code, msg = deserializeUserMsg( msg )

        if code == "END" and CHAT_NICK != None:
            print( f"{NEW_LINE}*****{NEW_LINE}" +
                f"End chat with {CHAT_NICK}" +
                f"{NEW_LINE}*****{NEW_LINE}" )
            setChatInfo( reset=True )
        elif code == "END":
            print(f"{PYCHAT + NICK_END} You're not in a chat.")
        elif code:
            sendServerMsg( serverSkt, code, msg )
            code, msg = recvServerMsg( serverSkt )

            if code == "CHAT" and CHAT_NICK == None:
                setChatInfo( info=msg )
            elif code == "CHAT":
                print( f"{PYCHAT + NICK_END} You're already chatting." )
            elif code == "QUIT":
                print( f"{NEW_LINE}-----{NEW_LINE}" +
                    "PyChat closed" +
                    f"{NEW_LINE}-----{NEW_LINE}" )
                serverSkt.close()
                clientSkt.close()
                sys.exit()
            else:
                print( f"{PYCHAT + NICK_END}" + " " + f"{msg}" )
        elif ( CHAT_NICK != None and
            msg != "" ):
            msg = f"{NICK + NICK_END}" + msg
            clientSkt.sendto( msg.encode(), (CHAT_IP, int(CHAT_PORT)) )

serverThread = threading.Thread( target=serverThread, args=(serverSkt, clientSkt) )
serverThread.start()