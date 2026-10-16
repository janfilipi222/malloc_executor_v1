from pathlib import Path
import sys

from implementation.robot_impl import RobotImpl
from infrastructure.file_loader import load_module, MallibFinder
from workers.queue_event_bus import QueueEventBus


def execute_process(path: str, event_queue, command_queue):
    bus = QueueEventBus(event_queue, command_queue)
    impl = RobotImpl(bus)

    module, spec = load_module(Path(path))

    original_mallib = sys.modules.pop("mallib", None)
    finder = MallibFinder(impl)
    sys.meta_path.insert(0, finder)

    try:
        spec.loader.exec_module(module)
    finally:
        sys.meta_path.remove(finder)

        if original_mallib is not None:
            sys.modules["mallib"] = original_mallib