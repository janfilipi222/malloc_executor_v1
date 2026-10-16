import time
from typing import Callable, Optional
from workers.serial_worker import SerialWorker
from application.event_bus import EventBus
from domain.model.actions import *
from domain.model.malloc_cmds import *
from domain.hardware.hardware_model import ArmModel
import math
import struct
from domain.motion import IK

class SerialService:
    def __init__(
        self,
        port: str,
        baudrate: int,
        bus: EventBus,
        timeout: float = 1.0,
    ):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._bus = bus

        self._worker: Optional[SerialWorker] = None

        self._bus.subscribe(SendSerialCMD, self._send_packet)

        self.arm_model = ArmModel()
        self.hardware = self.arm_model.hardware
        self.joints = self.arm_model.joints

    def start(self) -> None:
        print("start")
        if self.is_running():
            print("SerialService již běží.")
            return

        self._worker = SerialWorker(
            port=self._port,
            baudrate=self._baudrate,
            on_receive=self._receive_bytes,
            timeout=self._timeout,
        )
        print("spousteni workera")
        self._worker.start()

    def _send_packet(self, action: SendSerialCMD):
        # print(action)
        cmd = action.cmd
        match cmd:
            case SetPWM():
                print("sending set pwm:", cmd.value)
                payload = bytes([cmd.value])
                # print("payload: ", payload)
                packet = self._build_packet(ord("p"), payload, 6)
                self._send_packet_confirm(packet)

            case Home():
                print("homing")
                
                packet = self.build_packet_v3(ord("a"), ord("a"), (0,), 1)
                self._send_packet_confirm(packet)

            case SetEnable():
                print("setting ena")
                state = cmd.state
                packet = self.build_packet_v3(ord("e"), ord("a"), (state,), 1)
                self._send_packet_confirm(packet)

            case SetAcc():
                print("setting acc")
                state = cmd.state
                
                data = self.build_packet_v3(ord("f"), ord("a"), (state,), 1)
                self._send_packet_confirm(data)

            case SetZero():
                print("setting zero")
                packet = self.build_packet_v3(ord("z"), ord("a"), (0,), 1)
                self._send_packet_confirm(packet)


            case MoveAbsAcc():
                print("setting acc")
                value = cmd.angle
                index = cmd.joint_index

                j = self.hardware[index]

                steps = int((j.steps_per_revolution * j.gear_ratio) * (value / 360))

                # print("manual index:", cmd.joint_index, "  value:", steps)

                data = self.build_packet_v3(ord("w"), index, (steps,), 1)
                self._send_packet_confirm(data)
                # print("sent")

            case GoToPos4DOFTimed():
                x = cmd.x
                y = cmd.y
                z = cmd.z
                pitch = math.radians(cmd.pitch)
                time_ms = cmd.time_ms

                packet = self._handle_4DoF_Move(x, y, z, pitch, time_ms, 1)
                self._send_packet_confirm(packet)

            case GoTo4dot5DOFTimed():
                x = cmd.x
                y = cmd.y
                z = cmd.z
                p = math.radians(cmd.p)
                a = math.radians(cmd.a)
                time_ms = cmd.time_ms

                packet = self._handle_4dot5DOF_move(x, y, z, p, a, time_ms)
                self._send_packet_confirm(packet)

            case GoToPos3DOF3ManualTimed():
                x = cmd.x
                y = cmd.y
                z = cmd.z
                a = math.radian(cmd.a)
                b = math.radian(cmd.b)
                c = math.radian(cmd.c)
                time_ms = cmd.time_ms

                packet = self._handle_3DOF_3manual_move(x, y, z, a, b, c, time_ms)
                self._send_packet_confirm(packet)

            case GoToPos6Manual():
                a = cmd.a
                b = cmd.b
                c = cmd.c
                d = cmd.d
                e = cmd.e
                f = cmd.f

                packet = self._handle_6_manual(a, b, c, d, e, f, 2)
                self._send_packet_confirm(packet)



            case WaitTillDone():
                print("sending wait until done")
                
                packet = self.build_packet_v3(ord("W"), 0, (0,), 1)
                self._send_packet_confirm(packet)

            case GoTo4DOFIndependent():
                print("independent")
                x = cmd.x
                y = cmd.y
                z = cmd.z
                p = math.radians(cmd.pitch)

                data: bytearray = self._handle_4DoF_Move(x, y, z, p, -1, seq=1)
                self._send_packet_confirm(data)





                
    def _handle_4DoF_Move(self, x: float, y: float, z: float, pitch: float, time_ms: float, seq: int):
        print("4dof")
        
        a, b, c, d = IK.calculate_4DoF_IK([x, y, z], pitch, self.joints)
        steps = [a, b, c, 0, d, 0]
        converted_steps = []
        for i, x in enumerate(steps):
            converted_steps.append(
                int((x / (2 * math.pi)) * (self.hardware[i].steps_per_revolution * self.hardware[i].gear_ratio))
            )
        steps = converted_steps
        print("steps: ", steps)

        if time_ms > 0:
            packet_data = self.build_packet_v3(ord("T"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], int(time_ms)), seq)
        else:
            packet_data = self.build_packet_v3(ord("I"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], 0), seq)

        return packet_data

    
    def _handle_4dot5DOF_move(self, x: float, y: float, z: float, pitch: float, alpha: float, time_ms: float, seq: int=1):
        print("4.5 dof move")
        
        a, b, c, d = IK.calculate_4DoF_IK([x, y, z], pitch, self.joints)
        alpha = a + alpha
        print("alpha: ", alpha)
        steps = [a, b, c, 0, d, alpha]
        converted_steps = []
        for i, x in enumerate(steps):
            converted_steps.append(
                int((x / (2 * math.pi)) * (self.hardware[i].steps_per_revolution * self.hardware[i].gear_ratio))
            )
            # print(converted_steps[i])
        steps = converted_steps


        if time_ms > 0:
            packet_data = self.build_packet_v3(ord("T"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], int(time_ms)), seq)
        else:
            packet_data = self.build_packet_v3(ord("I"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], 0), seq)


        return packet_data

    
    def _handle_3DOF_3manual_move(self, x: float, y: float, z: float, a: float, b: float, c: float, time_ms: float, seq: int=1):
        print("33 dof")

        x, y, z = IK._calculate_3Dof_IK([x, y, z], self.joints)

        a = math.radians(a)
        b = math.radians(b)
        c = math.radians(c)

        print(a, b, c)

        steps = [x, y, z, a, b, c]
        converted_steps = []
        for i, x in enumerate(steps):
            converted_steps.append(
                int((x / (2 * math.pi)) * (self.hardware[i].steps_per_revolution * self.hardware[i].gear_ratio))
            )
        steps = converted_steps

        
        if time_ms > 0:
            packet_data = self.build_packet_v3(ord("T"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], int(time_ms)), seq)
        else:
            packet_data = self.build_packet_v3(ord("I"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], 0), seq)

        return packet_data

    

    
    def _handle_6_manual(self, a: int, b: int, c: int, d: int, e: int, f: int, seq: int):
        print("6 manual")

        a = math.radians(a)
        b = math.radians(b)
        c = math.radians(c)
        d = math.radians(d)
        e = math.radians(e)
        f = math.radians(f)

        print(a, b, c)

        steps = [a, b, c, d, e, f]
        converted_steps = []
        for i, x in enumerate(steps):
            converted_steps.append(
                int((x / (2 * math.pi)) * (self.hardware[i].steps_per_revolution * self.hardware[i].gear_ratio))
            )
        steps = converted_steps

        
        packet_data = self.build_packet_v3(ord("I"), 0, (steps[0], steps[1], steps[2], steps[3], steps[4], steps[5], 0), seq)

        return packet_data

    


    def _send_packet_confirm(self, packet: bytes):
        try:
            self.send_bytes(packet)
            packet = self._build_packet(0, bytes(0), 5)
            self.send_bytes(packet)
        except Exception as e:
            print("\033[38;5;208m" + str(e) + "\033[0m")


    def _build_packet(self, header: int, payload_bytes: bytes, seq: int) -> bytes:
        PAYLOAD_SIZE = 7 * 4

        payload_bytes = payload_bytes.ljust(PAYLOAD_SIZE, b'\x00')

        packet = bytearray()

        packet.append(0xAA)                    # HDR1
        packet.append(0x55)                    # HDR2
        packet.append(header)                  # CMD
        packet.append(0x00)     # STAFF
        packet.extend(payload_bytes)          # PAYLOAD
        packet.append(seq)                     # SEQ

        cs = sum(packet) + 1
        cs = cs & 0xFF
        packet.append(cs)

        return bytes(packet)

    def stop(self) -> None:
        if self._worker and self._worker.is_alive():
            self._worker.stop()
            self._worker.join()
            self._worker = None
                
    def _receive_bytes(self, data: bytes):
        for line in data.split(b"\n"):
            print(f"\033[32m{line}\033[0m")
            if b"\xaaU\xf0\x05" in line:
                # print("ack emit")
                self._bus.emit(RobotAck())
            elif b'\xaaU\xff\x00' in line:
                # print("done emit")
                self._bus.emit(RobotDone())

    def send_bytes(self, data: bytes) -> None:
        # print("sending bytes: ", data)
        if not self.is_running() or self._worker is None:
            raise RuntimeError("Serial is not running, cant send the data")

        self._worker.send_bytes(data)

    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()



    def build_packet_v3(self, header: int, staff: int, data: list[int], seq_index: int):

        data = tuple(data) + (0,) * (7 - len(data))
        data = data[:7]

        start_1 = 0xAA
        start_2 = 0x55

        # print("building v3: ", seq_index)

        packet = struct.pack(
            "<BBBB7iB",
            start_1,
            start_2,
            header,
            staff,
            *data,
            seq_index
        )

        control_sum = (sum(packet) - start_1 - start_2) & 0xFF

        packet = packet + struct.pack("B", control_sum)

        # print(packet)
        # print(len(packet))
        return packet