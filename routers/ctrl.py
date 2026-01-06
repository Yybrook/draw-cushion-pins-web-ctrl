import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
import json
from pathlib import Path

from ulity.tcp_client import TCPClient

router = APIRouter()
tcp = TCPClient()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "statics")

@router.get("/")
async def root():
    file_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(file_path, media_type="text/html")


@router.get("/connect")
async def connect(host: str, port: int):
    return tcp.connect(host, port)


@router.get("/disconnect")
async def disconnect():
    tcp.disconnect()
    return {"res": True}


@router.get("/enum_devices")
async def enum_devices():
    cmd = {"command": "enum device"}
    resp = tcp.send(message=json.dumps(cmd))
    if not resp["res"]:
        return resp

    resp = tcp.recv(timeout=5)
    if resp is None:
        return {"res": False, "info": f"get resp timeout"}

    try:
        resp = json.loads(resp)
    except:
        return {"res": False, "info": f"resp[{resp}] load as json error"}

    if "result" not in resp:
        return {"res": False, "info": f"invalid resp[{resp}]"}

    result = resp["result"]
    if result == "enum error":
        return {"res": False, "info": "enum error"}
    elif result == "enum none":
        return {"res": False, "info": "enum none"}
    # uid1^_^uid2^_^uid3
    uids = result.split("^_^")
    return {"res": True, "info": uids}


@router.get("/enum_lines")
async def enum_lines():
    cmd = {"command": "enum line"}
    resp = tcp.send(message=json.dumps(cmd))
    if not resp["res"]:
        return resp

    resp = tcp.recv(timeout=5)
    if resp is None:
        return {"res": False, "info": f"get resp timeout"}

    try:
        resp = json.loads(resp)
    except:
        return {"res": False, "info": f"resp[{resp}] load as json error"}

    if "result" not in resp:
        return {"res": False, "info": f"invalid resp[{resp}]"}

    result = resp["result"]
    # line1^_^line2^_^line3
    lines = result.split("^_^")
    return {"res": True, "info": lines}


@router.get("/enum_parts")
async def enum_parts(line: str):
    cmd = {"command": "enum part", "line": line}
    resp = tcp.send(message=json.dumps(cmd))
    if not resp["res"]:
        return resp

    resp = tcp.recv(timeout=5)
    if resp is None:
        return {"res": False, "info": f"get resp timeout"}

    try:
        resp = json.loads(resp)
    except:
        return {"res": False, "info": f"resp[{resp}] load as json error"}

    if "result" not in resp:
        return {"res": False, "info": f"invalid resp[{resp}]"}

    result = resp["result"]
    # part1^_^part2^_^part3
    parts = result.split("^_^")
    return {"res": True, "info": parts}


@router.get("/check")
async def check(device: str, line: str, part: str):
    # {"command":"open and check","userDefined":"0","line":"5-100","model":"PART1"}
    cmd = {
        "command": "open and check",
        "userDefined": device,
        "line": line,
        "model": part
    }
    resp = tcp.send(message=json.dumps(cmd))
    if not resp["res"]:
        return resp

    resp = tcp.recv(timeout=5)
    if resp is None:
        return {"res": False, "info": f"get resp timeout"}

    if resp == "doing":
        resp = tcp.recv(timeout=5)
        # {"result":"check right","picture":".\\PinsCtrlData\\DetectionRecords\\DetectionPictures\\Detection_5-100_PART1_RIGHT_20260105102314728853.jpg"}
        if resp is None:
            return {"res": False, "info": f"get resp timeout"}

    try:
        resp = json.loads(resp)
    except:
        return {"res": False, "info": f"resp[{resp}] load as json error"}

    if "result" not in resp:
        return {"res": False, "info": f"invalid resp[{resp}]"}

    result = resp["result"]
    if result == "check right":
        picture_path = Path(resp["picture"])
        picture_url = f"/images/{picture_path.name}"
        return {"res": True, "checkResult": True, "picture": picture_url}
    elif result == "check wrong":
        picture_path = Path(resp["picture"])
        picture_url = f"/images/{picture_path.name}"
        return {"res": True, "checkResult": False, "picture": picture_url}
    elif result == "open failed":
        return {"res": False, "info": "open failed"}
    elif result == "check error":
        return {"res": False, "info": "check error"}
    else:
        return {"res": False, "info": f"invalid resp[{resp}]"}




