from dataclasses import dataclass



@dataclass(slots=True)
class JointHardware:
    steps_per_revolution: int
    gear_ratio: float


    
@dataclass(slots=True)
class Joint:
    length: float
    axis: str
    angle: float
    min_angle: float
    max_angle: float




@dataclass(slots=True)
class ArmModel:
    joints: tuple[Joint] = (
        Joint(185, "y", 0, -135, 135),
        Joint(177, "z", 0, -30, 89),
        Joint(87, "z", 0, -30, 120),
        Joint(112, "y", 0, -90, 90),
        Joint(72, "z", 0, -90, 90),
        Joint(0, "y", 0, -90, 90)
    )

    hardware: tuple[JointHardware] = (
        JointHardware(3200, 4),
        JointHardware(3200, 25),
        JointHardware(3200, 25),
        JointHardware(200, 20.25),
        JointHardware(200, 32),
        JointHardware(200, 16)
    )
