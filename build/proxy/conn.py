import ctypes
import json
import os.path
import uuid
from typing import Tuple
import platform

GoInt = ctypes.c_longlong
GoString = ctypes.c_char_p
GoBytes = ctypes.POINTER(ctypes.c_char)


class intGoSlice(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(ctypes.c_longlong)),
                ("len", ctypes.c_longlong),
                ("cap", ctypes.c_longlong)]


class byteGoSlice(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(ctypes.c_char)),
                ("len", ctypes.c_longlong),
                ("cap", ctypes.c_longlong)]


class ConnectFB_return(ctypes.Structure):
    _fields_ = [("connID", GoInt),
                ("err", GoString)]


class RecvGamePacket_return(ctypes.Structure):
    _fields_ = [("pktBytes", GoBytes),
                ('l', GoInt),
                ("err", GoString)]


class SendWSCommand_return(ctypes.Structure):
    _fields_ = [("uuid", GoString),
                ("err", GoString)]


class SendMCCommand_return(ctypes.Structure):
    _fields_ = [("uuid", GoString),
                ("err", GoString)]


class GamePacketBytesAsIsJsonStr_return(ctypes.Structure):
    _fields_ = [("jsonStr", GoString),
                ("err", GoString)]


class JsonStrAsIsGamePacketBytes_return(ctypes.Structure):
    _fields_ = [("pktBytes", GoBytes),
                ('l', GoInt),
                ("err", GoString)]


def InitLib(lib_path: str):
    LIB = ctypes.cdll.LoadLibrary(lib_path)

    # struct ConnectFB_return ConnectFB(char* address);
    LIB.ConnectFB.argtypes = [GoString]
    LIB.ConnectFB.restype = ConnectFB_return

    # ReleaseConnByID(GoInt id);
    LIB.ReleaseConnByID.argtypes = [GoInt]

    # struct RecvGamePacket_return RecvGamePacket(GoInt connID);
    LIB.RecvGamePacket.argtypes = [GoInt]
    LIB.RecvGamePacket.restype = RecvGamePacket_return

    # char* SendGamePacketBytes(GoInt connID, GoSlice content);
    LIB.SendGamePacketBytes.argtypes = [GoInt, byteGoSlice]
    LIB.SendGamePacketBytes.restype = GoString

    # char* SendFBCommand(GoInt connID, char* cmd);
    LIB.SendFBCommand.argtypes = [GoInt, GoString]
    LIB.SendFBCommand.restype = GoString

    # struct SendWSCommand_return SendWSCommand(GoInt connID, char* cmd);
    LIB.SendWSCommand.argtypes = [GoInt, GoString]
    LIB.SendWSCommand.restype = SendWSCommand_return

    # struct SendMCCommand_return SendMCCommand(GoInt connID, char* cmd);
    LIB.SendMCCommand.argtypes = [GoInt, GoString]
    LIB.SendMCCommand.restype = SendMCCommand_return

    # struct SendNoResponseCommand(GoInt connID, char* cmd);
    LIB.SendNoResponseCommand.argtypes = [GoInt, GoString]
    LIB.SendNoResponseCommand.restype = GoString

    # struct GamePacketBytesAsIsJsonStr_return GamePacketBytesAsIsJsonStr(char* pktBytes);
    LIB.GamePacketBytesAsIsJsonStr.argtypes = [byteGoSlice]
    LIB.GamePacketBytesAsIsJsonStr.restype = GamePacketBytesAsIsJsonStr_return

    # struct JsonStrAsIsGamePacketBytes_return JsonStrAsIsGamePacketBytes(GoInt packetID, char* jsonStr);
    LIB.JsonStrAsIsGamePacketBytes.argtypes = [GoInt, GoString]
    LIB.JsonStrAsIsGamePacketBytes.restype = JsonStrAsIsGamePacketBytes_return

    # char* CreatePacketInJsonStrByID(GoInt packetID);
    # LIB.CreatePacketInJsonStrByID.argtypes = [GoInt]
    # LIB.CreatePacketInJsonStrByID.restype = GoString

    # FreeMem(address *C.char)
    LIB.FreeMem.argtypes=[ctypes.c_void_p]
    return LIB


def to_GoInt(i: int):
    return ctypes.c_longlong(i)


def to_PyInt(i):
    return i


def to_GoString(string: str):
    return ctypes.c_char_p(bytes(string, encoding="utf-8"))


def to_PyString(string: bytes):
    return string.decode(encoding="utf-8")


def to_GoByteSlice(bs: bytes):
    l = len(bs)
    kwargs = {
        'data': (ctypes.c_char * l)(*bs),
        'len': l,
        'cap': l,
    }
    return byteGoSlice(**kwargs)

def freeMem(address):
    LIB.FreeMem(address)

def check_err_in_struct(r):
    if r.err != None:
        err=to_PyString(r.err)
        # freeMem(r.err)
        raise Exception(err)


def check_err(r):
    if r != None:
        err=to_PyString(r)
        # freeMem(r.err)
        raise Exception(err)

LIB = None
if platform.system() == "Windows":
    if os.path.isfile("proxy/fbconn.dll"):
        LIB = InitLib("proxy/fbconn.dll")
    elif os.path.isfile("proxy/fbconn_Windows.dylib"):
        LIB = InitLib("proxy/fbconn_Windows.dylib")
elif platform.system() == "Linux":
    if platform.machine() == "aarch64":
        if os.path.isfile("proxy/fbconn_Linux_aarch64.dylib"):
            LIB = InitLib("proxy/fbconn_Linux_aarch64.dylib")
if LIB is None:
    raise Exception("Dylib file not found.")

    


def ConnectFB(address: str) -> int:
    r = LIB.ConnectFB(to_GoString(address))
    check_err_in_struct(r)
    return r.connID


def ReleaseConnByID(connID: int) -> None:
    LIB.ReleaseConnByID(to_GoInt(connID))


def RecvGamePacket(connID: int) -> bytes:
    r = LIB.RecvGamePacket(to_GoInt(connID))
    check_err_in_struct(r)
    bs=r.pktBytes[:r.l]
    freeMem(r.pktBytes)
    return bs


# not tested
def SendGamePacketBytes(connID: int, content: bytes) -> None:
    inp = to_GoByteSlice(content)
    r = LIB.SendGamePacketBytes(connID, inp)
    check_err(r)


def SendFBCommand(connID: int, cmd: str) -> None:
    r = LIB.SendFBCommand(to_GoInt(connID), to_GoString(cmd))
    check_err(r)


def SendNoResponseCommand(connID: int, cmd: str) -> None:
    r = LIB.SendNoResponseCommand(to_GoInt(connID), to_GoString(cmd))
    check_err(r)


def SendMCCommand(connID: int, cmd: str) -> str:
    r = LIB.SendMCCommand(to_GoInt(connID), to_GoString(cmd))
    check_err_in_struct(r)
    uuid=r.uuid[:]
    # freeMem(r.uuid)
    return uuid


def SendWSCommand(connID: int, cmd: str) -> str:
    r = LIB.SendWSCommand(to_GoInt(connID), to_GoString(cmd))
    check_err_in_struct(r)
    uuid=r.uuid[:]
    # freeMem(r.uuid)
    return uuid


def GamePacketBytesAsIsJsonStr(pktBytes: bytes) -> str:
    r = LIB.GamePacketBytesAsIsJsonStr(to_GoByteSlice(pktBytes))
    check_err_in_struct(r)
    jsonStr=to_PyString(r.jsonStr)
    # freeMem(r.jsonStr)
    return jsonStr


def JsonStrAsIsGamePacketBytes(packetID: int,jsonStr:str) -> bytes:
    r = LIB.JsonStrAsIsGamePacketBytes(to_GoInt(packetID),to_GoString(jsonStr))
    check_err_in_struct(r)
    bs=r.pktBytes[:r.l]
    freeMem(r.pktBytes)
    return bs

def inspectPacketID(packet:bytes):
    return packet[0]

if __name__ == '__main__':
    # 首先启动 FB: fastbuilder --listen-external 0.0.0.0:3456

    # 连接到 FB
    connID = ConnectFB("localhost:8000")

    # 发送 FB 命令
    #SendFBCommand(connID, "set 0 0 0")

    # 发送MC命令 (以 Setting Command 发出，无返回值)
    #SendNoResponseCommand(connID,"time set day")

    # 发送MC命令 (以用户身份发出，返回 uuid 值)
    #print(SendMCCommand(connID, "tp @a @s"))

    # 发送MC命令 (以Websocket身份发出，返回 uuid 值)
    #print(SendWSCommand(connID, "tp @a @s"))

    # 发送 Text 类型游戏数据包： "你好，世界"
    # 你也可以发送别的数据包，例如移动啊，放置方块啊，向命令块内写入信息啊什么的
    bs=b'\t\x01\x00\x062401PT\x0f\xe4\xbd\xa0\xe5\xa5\xbd\xef\xbc\x8c\xe4\xb8\x96\xe7\x95\x8c\x00\x00\x02\x08PlayerId\t-12345678'
    SendGamePacketBytes(connID,bs)

    while True:
        # 接收游戏数据包
        bytesPkt = RecvGamePacket(connID)
        packetType=inspectPacketID(bytesPkt)
        if packetType == 39 or packetType == 40 or packetType == 111 or packetType == 123 or packetType == 58:
            continue
        print("-------------")        # 解析数据包格式并转为json字符串（警告！效率低下！）
        jsonPkt=GamePacketBytesAsIsJsonStr(bytesPkt)
        #if (not("EntityRuntimeID" in jsonPkt)) and (not("SoundType" in jsonPkt)):
            #print(jsonPkt)
        print(jsonPkt)

        # 将Json形式的数据包转为游戏数据包（警告！效率低下！）
        # asIsbytesPkt=JsonStrAsIsGamePacketBytes(
        #     inspectPacketID(bytesPkt),
        #     jsonPkt
        # )
        #print(asIsbytesPkt)
