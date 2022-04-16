# =============================================================================
# IMPORT ALL PACKAGES
# =============================================================================

import socket

import sys

# =============================================================================
# GLOBAL VARS
# =============================================================================
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8080

CLIENT_CHECKED = False
CLIENT_NICK = None
CLIENT_IP = None
CLIENT_PORT = None

CHAT_SOCKET = None
CHAT_NICK = None
CHAT_IP = None
CHAT_PORT = None

NEW_LINE = "\r\n"

CODE_START = "/*"
CODE_END = "*/"
COMM_START = "!"

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def deserializeUserMsg(msg):
    code = False
    if COMM_START in msg and msg.index(COMM_START) == 0:
        msgList = msg.split()
        code = msgList[0][1:]
        msg = "" if len(msgList) == 1 else msgList[1]
        if code == "QUIT":
            msg = CLIENT_NICK
        elif code == "CHAT" and opt == CLIENT_NICK:
            print("You cannot chat with yourself. Find another user with !ALL")
            code = False
            msg = ""
    return [code, msg]

def deserializeServerMsg(data):
    msg = data.decode()

    msgList = msg.split(CODE_END)
    code = msgList[0][2:]
    opt = None if len(msgList) == 1 else msgList[1]

    return [code, opt]

def sendServerMsg(skt, code, opt=None):
    # serialize msg
    reply = str(CODE_START + code + CODE_END + opt)
    
    retry = 0
    while 0 <= retry < 5:
        try:
            skt.sendall(reply.encode())
            return True
        except socket.error as er:
            print(f"Failed to send. Error: {er}")
            retry += 1
            time.sleep(1)

# =============================================================================
# FUNCTIONS (1) Connection to the server
# =============================================================================

def getUserInfo():
    global CLIENT_NICK, CLIENT_IP, CLIENT_PORT
    CLIENT_NICK, CLIENT_IP, CLIENT_PORT = input(
        "Insert your nickname, IP address and port: "
    ).split()

def checkCredentials(skt):
    sendServerMsg(skt, "START", f"{CLIENT_NICK}|{CLIENT_IP}|{CLIENT_PORT}")

    data = skt.recv(1024)
    code, msg = deserializeServerMsg(data)
    print(f"{NEW_LINE*2}" + msg)

    if code == "ERR":
        return False
    return True

# =============================================================================
# SCRIPT (0) Connect to server
# =============================================================================

print(f"{NEW_LINE}-----{NEW_LINE}Hi! Welcome to PyChat{NEW_LINE}-----{NEW_LINE}")
try:
    serverSkt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSkt.connect((SERVER_IP, SERVER_PORT))
except socket.error as ex:
    print(f"Failed connecting to the server. Error: {ex}")
    sys.exit()

# =============================================================================
# SCRIPT (1) Check the user info
# =============================================================================

while not CLIENT_CHECKED:
    getUserInfo()
    CLIENT_CHECKED = checkCredentials(serverSkt)

while True:
    msg = input(f"{CLIENT_NICK}> ")
        
    code, msg = deserializeUserMsg(msg)
    
    if code:
        sendServerMsg(serverSkt, code, msg)

        serverResp = serverSkt.recv(1024)
        code, msg = deserializeServerMsg(serverResp)
        
        print("PyChat> " + msg)

        if code == "QUIT":
            serverSkt.close()
            print(f"{NEW_LINE}-----{NEW_LINE}PyChat closed{NEW_LINE}-----{NEW_LINE}")
            sys.exit()

sys.exit()