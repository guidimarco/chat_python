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

COMMANDS = [{
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
}]

USERS = []

# =============================================================================
# FUNCTIONS (0) Getter and setter
# =============================================================================

def getHelp():
    return f"Here's the list of all commands:{NEW_LINE}" + "".join(
        [ comm["name"] + ": " + comm["description"] + NEW_LINE for comm in COMMANDS ]
    )

def getUsers():
    return [ user["name"] for user in USERS ]

def getUser(nick):
    global USERS
    print(USERS)
    userObj = list(filter(lambda U: U["name"] == nick, USERS))
    if len(userObj) == 0:
        return False
    return "|".join(userObj[0].values())

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def deserializeClientMsg(data):
    msg = data.decode()

    if not (
        CODE_START not in msg or
        msg.index(CODE_START) != 0 or
        CODE_END not in msg
    ):
        msgList = msg.split(CODE_END)
        code = msgList[0][2:]
        opt = None if len(msgList) == 1 else msgList[1]
    else:
        code = "ERR"
        opt = "Bad Request"

    return [code, opt]

def sendClientMsg(conn, code, opt=None):
    # serialize msg
    reply = str(CODE_START + code + CODE_END + opt)
    
    retry = 0
    while 0 <= retry < 5:
        try:
            conn.sendall(reply.encode())
            return True
        except socket.error as er:
            print(f"Failed to send. Error: {er}")
            retry += 1
            time.sleep(1)

def addUser(nick, IP, PORT):
    for user in USERS:
        if user["name"] == nick or user["port"] == PORT:
            return False
    USERS.append({
        "name": nick,
        "IP": IP,
        "port": PORT
    })
    return True

def removeUser(nick):
    for user in USERS:
        if user["name"] == nick:
            USERS.remove(user)
            return True
    return False

# =============================================================================
# FUNCTIONS (0) Set-up
# =============================================================================

def clientThread(conn, addr):
    userAdded = False
    retry = 0
    while not userAdded:
        data = conn.recv(1024)
        code, opt = deserializeClientMsg(data)

        nick, ip, port = opt.split("|")

        # Overwrite user IP and port with real one
        userAdded = addUser(nick, addr[0], str(addr[1]))
        if userAdded:
            sendClientMsg(conn, "START", getHelp())
        else:
            sendClientMsg(conn, "ERR", f"Nickname or port already used!{NEW_LINE}")

    print(userAdded, USERS)
    if not userAdded: return

    while True:
        data = conn.recv(1024)
        code, opt = deserializeClientMsg(data)
                
        if code == "HELP":
            opt = getHelp()
        elif code == "ALL":
            opt = f"Users currently connected:{NEW_LINE}" + "\r\n".join(getUsers()) + f"{NEW_LINE}"
        elif code == "CHAT":
            opt = getUser(opt)
            if not opt:
                code = "ERR"
                opt = "User not found! You can find all user with the !ALL command."
        elif code == "QUIT":
            removeUser(opt)
            opt = "Connection closed!"
        else:
            code = "ERR"
            opt = "Command not found!"
        
        sendClientMsg(conn, code, opt)

        if code == "QUIT":
            break

# =============================================================================
# SCRIPT (0) Start the server
# =============================================================================

try:
    socketSrv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketSrv.bind((SERVER_IP, SERVER_PORT))
    socketSrv.listen(10)
    print(f"{NEW_LINE}-----{NEW_LINE}The server is on. IP: {SERVER_IP} at port: {SERVER_PORT}{NEW_LINE}-----{NEW_LINE}")
except socket.error as er:
    print(f"Failed to create a socket. Error: {er}")
    sys.exit()

# =============================================================================
# SCRIPT (1) Start the daemon
# =============================================================================

while True:
    conn, addr = socketSrv.accept()
    print(f"Client connection up. IP: {addr[0]}, port: {addr[1]}")
    start_new_thread(clientThread, (conn, addr))
socketSrv.close()