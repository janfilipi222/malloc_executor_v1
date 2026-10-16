import importlib.abc
import importlib.util
import sys

from types import ModuleType
from pathlib import Path
from importlib.machinery import ModuleSpec


class MallibFinder(importlib.abc.MetaPathFinder):
    def __init__(self, robot_impl):
        self.robot_impl = robot_impl

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "mallib":
            return None

        return importlib.util.spec_from_loader(
            fullname,
            MallibLoader(self.robot_impl),
        )


class MallibLoader(importlib.abc.Loader):
    def __init__(self, robot_impl):
        self.robot_impl = robot_impl

    def create_module(self, spec):
        module = ModuleType(spec.name)
        module.Robot = self.robot_impl
        return module

    def exec_module(self, module):
        pass


def load_module(
    file_path: str | Path,
) -> tuple[ModuleType, ModuleSpec]:

    path = Path(file_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(
        "robot_script",
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")

    module = importlib.util.module_from_spec(spec)

    return module, spec 