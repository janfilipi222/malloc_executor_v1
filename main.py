from infrastructure.tcp_server import TCPServer
from app.bg_app import BgApp
from time import sleep
from implementation.robot_impl import RobotImpl
from infrastructure.file_loader import load_module
from pathlib import Path
import sys
from infrastructure.file_loader import MallibFinder
from services.executor_service import ExecutorService
from workers.execution_worker import ExecutionWorker
from application.event_bus import EventBus
from services.serial_service import SerialService

def main():

    HOST = "127.0.0.1"
    PORT = 49152

    bus = EventBus()

    print("\033[90mTento text je šedý\033[0m")

    execution_worker = ExecutionWorker(bus)
    executor_service = ExecutorService(bus, execution_worker)
    serial_service = SerialService("COM6", 115200, bus)
    server = TCPServer(bus, HOST, PORT)
    bg_app = BgApp(server, serial_service)

    bg_app.start()


if __name__ == "__main__":

    main()


