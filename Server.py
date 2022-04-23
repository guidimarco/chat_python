"""
    SERVER script:
        1) create a TCP socket
        2) start the multithread-daemon for client connection
            Single-thread:
                - START > Add new user ( nickname, IP, port )
                - Listen for user command untill
                - QUIT > Close the thread
"""

# =============================================================================
# IMPORT ALL PACKAGES
# =============================================================================

import socket
from _thread import *

import time
import sys

# =============================================================================
# GLOBAL VARS
# =============================================================================

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8080

NEW_LINE = "\r\n"

CODE_START = "/*"
CODE_END = "*/"

COMMANDS = [
    {
        "name": "!HELP",
        "description": "Return the list of all PyChat commands"
    }, {
        "name": "!ALL",
        "description": "Return all user currently connected"
    }, {
        "name": "!CHAT",
        "description": "Start a chat with an user (require the user nickname)"
    }, {
        "name": "!END",
        "description": "End the current chat"
    }, {
        "name": "!QUIT",
        "description": "Close the program"
    }
]

USERS = []

# =============================================================================
# FUNCTIONS (0) Getter and setter
# =============================================================================

def getHelp():
    return f"Here's the list of all commands:{NEW_LINE}" + "".join(
        [ comm["name"] + ": " + comm["description"] + NEW_LINE for comm in COMMANDS ]
    )

def getUsers():
    return f"Users currently connected:{NEW_LINE}" + "".join(
        [ user["name"] + NEW_LINE for user in USERS ]
    )

def getUser( par, value ):
    global USERS
    userObj = list( filter(lambda U: U[par] == str( value ), USERS) )
    if len( userObj ) == 0:
        return False
    return "|".join( userObj[0].values() )

def setErr( errMsg="Bad request" ):
    return [ "ERR", errMsg ]

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def recvClientMsg( conn ):
    try:
        data = conn.recv( 1024 )
    except:
        conn.close()
        return [ False, None ]
    msg = data.decode()

    if not (
        CODE_START not in msg or
        msg.index( CODE_START ) != 0 or
        CODE_END not in msg
    ):
        msgList = msg.split( CODE_END )
        code = msgList[0][2:]
        opt = None if len( msgList ) == 1 else msgList[1]
    else:
        code = "ERR"
        opt = None

    return [ code, opt ]

def sendClientMsg( conn, code, opt=None ):
    reply = str( CODE_START + code + CODE_END + opt )
    conn.sendall( reply.encode() )

def addUser( nick, IP, PORT ):
    for user in USERS:
        if user["name"] == nick or user["port"] == PORT:
            return False
    USERS.append({
        "name": nick,
        "IP": IP,
        "port": PORT
    })
    return True

def removeUser( nick ):
    for user in USERS:
        if user["name"] == nick:
            USERS.remove( user )
            return True
    return False

# =============================================================================
# FUNCTIONS (0) Set-up
# =============================================================================

def clientThread( conn, addr ):
    while True:
        userInfo = getUser( "port", addr[1] )
        code, opt = recvClientMsg( conn )

        if code == "START" and not userInfo:
            optList = opt.split( "|" )
            if not len( optList ) == 3:
                code, opt = setErr()
            else:
                nick, ip, port = opt.split( "|" )
                # Overwrite with real IP and port
                result = addUser( nick, addr[0], str(addr[1]) )
                opt = getHelp()
                if not result:
                    code, opt = setErr( f"Nickname or port already used!{NEW_LINE}" )
        elif code == "HELP":
            opt = getHelp()
        elif code == "ALL":
            opt = getUsers()
        elif code == "CHAT":
            opt = getUser( "name", opt )
            if not opt:
                code, opt = setErr( "User not found! You can find all user with the !ALL command." )
        elif code == "QUIT" or code == False:
            nick, IP, port = userInfo.split("|")
            print( f"Client connection down. IP: {IP}, port: {port}" )
            removeUser( nick )
            conn.close()
            break
        else:
            code, opt = setErr( "Command not found" )
        
        sendClientMsg( conn, code, opt )

# =============================================================================
# SCRIPT (1) Start the server
# =============================================================================

try:
    socketSrv = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    socketSrv.bind( (SERVER_IP, SERVER_PORT) )
    socketSrv.listen( 10 )

    print( f"{NEW_LINE}-----{NEW_LINE}" + 
        f"The server is on. IP: {SERVER_IP} at port: {SERVER_PORT}" +
        f"{NEW_LINE}-----{NEW_LINE}" )
except socket.error as er:
    print( f"Failed to create a socket. Error: {er}" )
    sys.exit()

# =============================================================================
# SCRIPT (2) Start the daemon
# =============================================================================

while True:
    conn, addr = socketSrv.accept()
    print( f"Client connection up. IP: {addr[0]}, port: {addr[1]}" )
    start_new_thread( clientThread, (conn, addr) )