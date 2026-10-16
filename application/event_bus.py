from collections import defaultdict
from typing import Callable, Any
from domain.model.actions import Action


class EventBus:
    def __init__(self):
        self._listeners: dict[type[Action], list[Callable[[Action], None]]] = defaultdict(list)

    def subscribe(self, action: type[Action], callback: Callable[[Any], None]):
        self._listeners[action].append(callback)

    def unsubscribe(self, action: type[Action], callback: Callable[[Any], None]):
        self._listeners[action].remove(callback)

    def emit(self, action: Action):
        for callback in self._listeners[type(action)]:
            callback(action)