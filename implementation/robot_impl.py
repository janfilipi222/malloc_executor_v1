import threading

from mallib import Robot

from domain.model.actions import (
    SendToTCP,
    SendSerialCMD,
    RobotDone,
    Action,
    RobotAck,
)
from domain.model.malloc_cmds import *
from application.event_bus import EventBus


class RobotImpl(Robot):

    def __init__(self, event_bus: EventBus):
        self._bus = event_bus

        self._ack_condition = threading.Condition()
        self._ack = False
        self._done = False

        self._bus.subscribe(RobotDone, self._handle_wait)
        self._bus.subscribe(RobotAck, self._handle_ack)

    def _handle_wait(self, action: RobotDone):
        print("from lib, handle done")
        with self._ack_condition:
            self._done = True
            self._ack_condition.notify_all()

    def _handle_ack(self, action: RobotAck):
        print("from lib, handle ack")
        with self._ack_condition:
            self._ack = False
            self._ack_condition.notify_all()

    def _send_and_wait(self, action: Action):
        with self._ack_condition:
            self._ack = True

        self._bus.emit(action)

        with self._ack_condition:
            self._ack_condition.wait_for(lambda: not self._ack)

    def my_print(self, msg: str):
        print("msg: ", msg)

    def move(self, x: int):
        print(f"moving to {x}")

    def calib_soft(self):
        print("soft calibrate")

    def calib_hard(self):
        print("hard calibrate")

    def home(self):
        self._send_and_wait(SendSerialCMD(Home()))

    def send_msg(self, msg: dict):
        self._send_and_wait(SendToTCP(msg))

    def set_pwm(self, value: int):
        self._send_and_wait(SendSerialCMD(SetPWM(value)))

    def set_zero(self):
        self._send_and_wait(SendSerialCMD(SetZero()))

    def set_acc(self, state: bool):
        self._send_and_wait(SendSerialCMD(SetAcc(state)))

    def set_enable(self, state: bool):
        self._send_and_wait(SendSerialCMD(SetEnable(state)))

    def move_abs_acc(self, joint_index: int, angle: int):
        self._send_and_wait(
            SendSerialCMD(MoveAbsAcc(joint_index, angle))
        )

    def go_to_pos_4dof_timed(
        self, x: int, y: int, z: int, pitch: int, time_ms: int
    ):
        self._send_and_wait(
            SendSerialCMD(
                GoToPos4DOFTimed(x, y, z, pitch, time_ms)
            )
        )

    def go_to_4dof_independent(
        self, x: int, y: int, z: int, pitch: int
    ):
        self._send_and_wait(
            SendSerialCMD(
                GoTo4DOFIndependent(x, y, z, pitch)
            )
        )

    def go_to_4dot5dof_timed(
        self,
        x: int,
        y: int,
        z: int,
        p: float,
        a: float,
        time_ms: int,
    ):
        self._send_and_wait(
            SendSerialCMD(
                GoTo4dot5DOFTimed(x, y, z, p, a, time_ms)
            )
        )

    def go_to_pos_3dof_3_manual_timed(
        self,
        x: int,
        y: int,
        z: int,
        a: int,
        b: int,
        c: int,
        time_ms: int,
    ):
        self._send_and_wait(
            SendSerialCMD(
                GoToPos3DOF3ManualTimed(
                    x, y, z, a, b, c, time_ms
                )
            )
        )

    def go_to_pos_6_manual(
            self,
            a: int,
            b: int,
            c: int,
            d: int,
            e: int,
            f: int
    ):
        self._send_and_wait(
            SendSerialCMD(
                GoToPos6Manual(a, b, c, d, e, f)
            )
        )

    def wait_till_done(self):
        with self._ack_condition:
            self._done = False

        self._bus.emit(
            SendSerialCMD(WaitTillDone())
        )

        with self._ack_condition:
            self._ack_condition.wait_for(lambda: self._done)