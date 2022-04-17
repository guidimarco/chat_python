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

VALID_CRED = False
CLIENT_NICK = None
CLIENT_IP = None
CLIENT_PORT = None

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

def setChatInfo(info, reset=False):
    global CHAT_NICK, CHAT_IP, CHAT_PORT
    if reset:
        CHAT_NICK, CHAT_IP, CHAT_PORT = [None, None, None]
    else:
        CHAT_NICK, CHAT_IP, CHAT_PORT = info.split("|")
        CHAT_PORT = int(CHAT_PORT)
        print(type(CHAT_PORT))

# =============================================================================
# FUNCTIONS (0) Global functions
# =============================================================================

def startNewChat(opt):
    global CHAT_NICK, CHAT_IP, CHAT_PORT
    CHAT_NICK, CHAT_IP, CHAT_PORT = opt.split("|")
    print(f"{NEW_LINE}-----{NEW_LINE}New chat with {CHAT_NICK}{NEW_LINE}-----{NEW_LINE}")


def deserializeUserMsg(msg):
    code = False
    if COMM_START in msg and msg.index(COMM_START) == 0:
        msgList = msg.split()
        code = msgList[0][1:]
        msg = "" if len(msgList) == 1 else msgList[1]
        if code == "QUIT":
            msg = CLIENT_NICK
        elif code == "CHAT" and msg == CLIENT_NICK:
            print(f"{PYCHAT}You cannot chat with yourself. Find another user with !ALL")
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
            print(f"{PYCHAT}Failed to send. Error: {er}")
            retry += 1
            time.sleep(1)

# =============================================================================
# FUNCTIONS (1) Connection to the server
# =============================================================================

def getUserInfo():
    global CLIENT_NICK
    while True:
        inputsList = input(
            f"{PYCHAT}Insert your nickname, IP address and port: "
        ).split()

        if len(inputsList) < 3:
            print(f"{PYCHAT}Enter 3 values")
            continue
        
        CLIENT_NICK = inputsList[0]
        break

def checkCredentials(skt):
    global VALID_CRED, CLIENT_NICK, CLIENT_IP, CLIENT_PORT
    sendServerMsg(skt, "START", f"{CLIENT_NICK}|{CLIENT_IP}|{CLIENT_PORT}")

    data = skt.recv(1024)
    code, msg = deserializeServerMsg(data)
    print(f"{NEW_LINE}" + msg)

    if not code == "ERR":
        VALID_CRED = True

# =============================================================================
# SCRIPT (0) Connect to server
# =============================================================================

print(f"{NEW_LINE}-----{NEW_LINE}Hi! Welcome to PyChat{NEW_LINE}-----{NEW_LINE}")
try:
    serverSkt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSkt.connect((SERVER_IP, SERVER_PORT))
    CLIENT_IP, CLIENT_PORT = serverSkt.getsockname()
except socket.error as ex:
    print(f"{PYCHAT}Failed connecting to the server. Error: {ex}")
    sys.exit()

# =============================================================================
# SCRIPT (1) Check the user info
# =============================================================================

while not VALID_CRED:
    getUserInfo()
    checkCredentials(serverSkt)

try:
    clientSkt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSkt.bind((CLIENT_IP, CLIENT_PORT))
except socket.error as ex:
    print(f"{PYCHAT}Failed creating socket UDP. Error: {ex}")
    serverSkt.close()
    print(f"{NEW_LINE}-----{NEW_LINE}PyChat closed{NEW_LINE}-----{NEW_LINE}")
    sys.exit()

while True:
    msg = input(f"{CLIENT_NICK}> ")
        
    code, msg = deserializeUserMsg(msg)
    
    if code:
        sendServerMsg(serverSkt, code, msg)

        serverResp = serverSkt.recv(1024)
        code, msg = deserializeServerMsg(serverResp)
        
        print(f"{PYCHAT}{msg}")

        if code == "CHAT" and CHAT_NICK == None:
            setChatInfo(info=msg)
            startNewChat(msg)
        elif code == "CHAT":
            print(f"{PYCHAT}You're already chatting.")
        elif code == "QUIT":
            serverSkt.close()
            print(f"{NEW_LINE}-----{NEW_LINE}PyChat closed{NEW_LINE}-----{NEW_LINE}")
            sys.exit()
    elif not CHAT_NICK == None:
        print(msg, msg.encode(), CHAT_IP, CHAT_PORT)
        clientSkt.sendto(msg.encode(), (CHAT_IP, CHAT_PORT))
    else:
        print(f"{PYCHAT}You're not in a chat!")