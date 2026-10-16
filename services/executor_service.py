from domain.model.actions import *
from domain.model.malloc_cmds import *
from workers.execution_worker import ExecutionWorker
from infrastructure.file_loader import load_module
from infrastructure.file_loader import MallibFinder
from implementation.robot_impl import RobotImpl
from pathlib import Path
import sys
from domain.motion import IK
from application.event_bus import EventBus
import math
from domain.hardware.hardware_model import ArmModel

class ExecutorService:

    def __init__(self, event_bus: EventBus, execution_worker: ExecutionWorker):
        self.execution_worker: ExecutionWorker = execution_worker
        self._bus = event_bus
        self._bus.subscribe(ScriptedEnded, self._handle_script_ended)
        self._bus.subscribe(TCPMsg, self._handle_tcp_msg)

        self.joints = ArmModel.joints

    def _handle_script_ended(self, action: ScriptedEnded):
        print("\033[94mfrom handler script ended\033[0m")

    def _handle_tcp_msg(self, action: TCPMsg):
        print("tcp msg action: ", action.msg)
        self._parse_msg(action.msg)



    def _parse_msg(self, msg: dict):

        handlers = {
            "fire": self._fire_handler,
            "run": self._handle_run,
            "test": self._test,
            "stop": self._handle_stop
        }

        if "action" in msg:
            msg_action = msg["action"]
            handler = handlers.get(msg_action)
            if handler:
                handler(msg)

    def _handle_stop(self, msg: dict):
        print("handle stop")
        self.execution_worker.stop()


    def _handle_run(self, cmd: dict):
        print("handel run: ", cmd)

        run_type = cmd.get("type")
        if run_type is None: return

        if run_type == "file":
            path: str = cmd.get("path")
            if path is None: return
            path = path.strip()
            print("path: ", path)

            if path.startswith("~"):
                path = "D:/malloc_scripts/" + path[1:]

            self.execution_worker.set_script(path)

        elif run_type == "manual_command":
            command = cmd.get("command")
            if command is None: return

            command = command.strip()
            cmds = command.split(" ")


            l = len(cmds)
            if l >= 1:
                match cmds[0]:
                    case "g":   # gripper
                        if l >= 2:
                            value = int(cmds[1])
                            print("cli move gripper to: ", value)
                            self._bus.emit(SendSerialCMD(SetPWM(value)))

                    case "h":   # homing
                        print("homing")
                        self._bus.emit(SendSerialCMD(Home()))

                    case "f": # set acc
                        if l >= 2:
                            state = True if int(cmds[1]) else False
                            print("setting acc to: ", state)
                            self._bus.emit(SendSerialCMD(SetAcc(state)))

                    case "z": # set zero
                        self._bus.emit(SendSerialCMD(SetZero()))

                    case "e": # set enable
                        if l >= 2:
                            state = True if int(cmds[1]) else False
                            print("setting enable to: ", state)
                            self._bus.emit(SendSerialCMD(SetEnable(state)))

                    case "w": # move abs acc
                        if l >= 3:
                            index = int(cmds[1])
                            angle = int(cmds[2])
                            print(f"moving joint: {index} to pos: {angle}")
                            self._bus.emit(SendSerialCMD(MoveAbsAcc(index, angle)))

                    case "q": # move 4dof timed
                        if l >= 6:
                            x = int(cmds[1])
                            y = int(cmds[2])
                            z = int(cmds[3])
                            pitch = float(cmds[4])
                            time_ms = int(cmds[5])

                            self._bus.emit(SendSerialCMD(GoToPos4DOFTimed(x, y, z, pitch, time_ms)))

                    case "a": # move 4.5dof timed
                        if l >= 7:
                            x = int(cmds[1])
                            y = int(cmds[2])
                            z = int(cmds[3])
                            p = int(cmds[4])
                            a = int(cmds[5])
                            time_ms = int(cmds[6])

                            self._bus.emit(SendSerialCMD(GoTo4dot5DOFTimed(x, y, z, p, a, time_ms)))

                    case "g": # move 3+3dof timed
                        if l >= 8:
                            x = int(cmds[1])
                            y = int(cmds[2])
                            z = int(cmds[3])
                            a = int(cmds[4])
                            b = int(cmds[5])
                            c = int(cmds[6])
                            time_ms = int(cmds[7])

                            self._bus.emit(SendSerialCMD(GoToPos3DOF3ManualTimed(x, y, z, a, b, c, time_ms)))




                

    def _test(self, msg: dict):
        print("testing: ", msg)
        self._bus.emit(SendSerialCMD(SetPWM(100)))

    def _fire_handler(self, msg: dict):
        print("fire handler")
        params = ("path")

        print("keys: ", msg.keys())
        if not self._validate_params(params, msg):
            print("not all params")
            return

        print("firing script")
        path = msg["path"]
        print("path: ", msg["path"])

    





    def _validate_params(self, params: list, msg: dict):
        return all(key == "action" or key in params for key in msg.keys())
