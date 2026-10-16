import time
import threading
from typing import Callable, Optional
import serial

class SerialWorker(threading.Thread):
    def __init__(
        self,
        port: str,
        baudrate: int,
        on_receive: Callable[[bytes], None],
        timeout: float = 1.0,
    ):
        super().__init__(daemon=True)
        self.port = port
        self.baudrate = baudrate
        self.on_receive = on_receive
        self.timeout = timeout

        self._stop_event = threading.Event()
        self._serial: Optional[serial.Serial] = None

    def run(self) -> None:
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            while not self._stop_event.is_set():
                # Zjištění počtu dostupných bajtů ve vstupním bufferu
                waiting_bytes = self._serial.in_waiting
                if waiting_bytes > 0:
                    data = self._serial.read(waiting_bytes)
                    if data and self.on_receive:
                        self.on_receive(data)
                else:
                    # Krátká pauza, aby se nevytěžovalo CPU, když nepřicházejí žádná data
                    time.sleep(0.01)

        except serial.SerialException as e:
            print(f"Chyba sériového portu: {e}")
        finally:
            if self._serial and self._serial.is_open:
                self._serial.close()

    def send_bytes(self, data: bytes) -> None:
        """
        Odeslání pole bajtů přes sériovou linku.
        """
        if self._serial and self._serial.is_open:
            self._serial.write(data)
        else:
            raise RuntimeError("Sériový port není otevřen.")

    def stop(self) -> None:
        """
        Bezpečné zastavení vlákna a uzavření portu.
        """
        self._stop_event.set()
