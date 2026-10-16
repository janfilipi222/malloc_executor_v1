import threading
import multiprocessing
from pathlib import Path
from queue import Empty

from workers.execution_process import execute_process
from domain.model.actions import ScriptedEnded, RobotDone, RobotAck
from application.event_bus import EventBus



class ExecutionWorker(threading.Thread):

    def __init__(self, event_bus: EventBus):
        super().__init__(target=self.run, daemon=True)

        self._bus = event_bus
        self._running_script = False
        self._script_path: str | None = None
        self._process: multiprocessing.Process | None = None

        self.lock = threading.Lock()
        self._running = True

        self._event_queue = multiprocessing.Queue()
        self._command_queue = multiprocessing.Queue()

        self._event_listener = threading.Thread(
            target=self._listen_events,
            daemon=True
        )
        self._event_listener.start()

        self._bus.subscribe(RobotDone, self._handle_robot_wait)
        self._bus.subscribe(RobotAck, self._handle_robot_ack)

        self.start()

    def _handle_robot_wait(self, action: RobotDone):
        # print("worker done")
        self.send_to_script(action)

    def _handle_robot_ack(self, action: RobotAck):
        # print("worker ack")
        self.send_to_script(action)


    def run(self):
        while self._running:
            with self.lock:
                running_script = self._running_script

            if running_script:
                self._execute()

                with self.lock:
                    self._running_script = False

    def _listen_events(self):
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.2)
                self._bus.emit(event)
            except Empty:
                continue

    def _execute(self):
        try:
            self._command_queue = multiprocessing.Queue()

            self._process = multiprocessing.Process(
                target=execute_process,
                args=(
                    self._script_path,
                    self._event_queue,
                    self._command_queue,
                ),
                daemon=True,
            )

            self._process.start()
            self._process.join()

        finally:
            self._process = None
            self._bus.emit(ScriptedEnded())

    def stop(self):
        process = self._process

        if process is not None and process.is_alive():
            process.terminate()
            process.join()

    def set_script(self, path: str):
        with self.lock:
            if self._running_script:
                print("cannot run 2 programs simultaneously")
                return

            self._script_path = str(Path(path))
            self._running_script = True

        print("starting")

    def send_to_script(self, event):
        if self._process is not None and self._process.is_alive():
            # print("putting")
            self._command_queue.put(event)
        # else:
            # print("process dead")