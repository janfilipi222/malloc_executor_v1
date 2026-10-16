from dataclasses import dataclass


class MallocCMD:
    pass




@dataclass(frozen=True)
class SetPWM(MallocCMD):
    value: int

@dataclass(frozen=True)
class Home(MallocCMD):
    pass

@dataclass(frozen=True)
class SetZero(MallocCMD):
    pass

@dataclass(frozen=True)
class SetAcc(MallocCMD):
    state: bool

@dataclass(frozen=True)
class SetEnable(MallocCMD):
    state: bool

@dataclass(frozen=True)
class MoveAbsAcc(MallocCMD):
    joint_index: int
    angle: int


@dataclass(frozen=True)
class GoToPos4DOFTimed(MallocCMD):
    x: int
    y: int
    z: int
    pitch: int
    time_ms: int

@dataclass(frozen=True)
class GoTo4DOFIndependent(MallocCMD):
    x: int
    y: int
    z: int
    pitch: int

@dataclass(frozen=True)
class GoTo4dot5DOFTimed(MallocCMD):
    x: int
    y: int
    z: int
    p: float
    a: float
    time_ms: int

@dataclass(frozen=True)
class GoToPos3DOF3ManualTimed(MallocCMD):
    x: int
    y: int
    z: int
    a: int
    b: int
    c: int
    time_ms: int

@dataclass(frozen=True)
class GoToPos6Manual(MallocCMD):
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int

@dataclass(frozen=True)
class WaitTillDone(MallocCMD):
    pass



