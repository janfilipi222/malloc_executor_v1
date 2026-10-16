from dataclasses import dataclass
from domain.model.malloc_cmds import *

class Action:
    pass


@dataclass(frozen=True)
class TCPMsg(Action):
    owner_id: str
    msg: dict

@dataclass(frozen=True)
class ScriptedEnded(Action):
    pass

@dataclass(frozen=True)
class SendToTCP(Action):
    msg: dict


@dataclass(frozen=True)
class SendSerialCMD(Action):
    cmd: MallocCMD

@dataclass(frozen=True)
class RobotDone(Action):
    pass

@dataclass(frozen=True)
class RobotAck(Action):
    pass