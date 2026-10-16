import threading
from queue import Empty
from multiprocessing import Queue


class QueueEventBus:
    def __init__(self, outgoing_queue: Queue, incoming_queue: Queue):
        self._outgoing_queue = outgoing_queue
        self._incoming_queue = incoming_queue
        self._callbacks = []
        self._lock = threading.Lock()
        self._listener_started = False

    def emit(self, event):
        self._outgoing_queue.put(event)

    def subscribe(self, event_type, callback):
        with self._lock:
            self._callbacks.append((event_type, callback))

            if not self._listener_started:
                self._listener_started = True
                # print("STARTING QUEUE LISTENER")
                threading.Thread(
                    target=self._listen,
                    daemon=True,
                ).start()

    def _listen(self):
        # print("QUEUE LISTENER RUNNING")

        while True:
            try:
                event = self._incoming_queue.get(timeout=0.2)
                # print("RECEIVED:", type(event), event)
            except Empty:
                continue

            with self._lock:
                callbacks = self._callbacks.copy()

            for event_type, callback in callbacks:
                if isinstance(event, event_type):
                    # print("CALLING:", callback)
                    callback(event)