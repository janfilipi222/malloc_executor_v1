from infrastructure.tcp_server import TCPServer
from services.serial_service import SerialService


class BgApp:

    running = False

    def __init__(self, server: TCPServer, serial_service: SerialService):
        self.server: TCPServer = server
        self.serial: SerialService = serial_service


    def start(self):
        self.running = True
        self.server.fire()
        self.serial.start()
        self._loop()



    def _loop(self):

        while self.running:
            
            pass


    def stop(self):
        self.running = False
        self.server.stop()

        self.serial.stop()
