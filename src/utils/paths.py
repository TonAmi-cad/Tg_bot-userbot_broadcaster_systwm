import os
from typing import Optional


def get_project_root() -> str:
    # Этот файл находится в src/utils/paths.py → поднимаемся к корню проекта
    # root = <project_root>
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_msg_dir() -> str:
    return os.path.join(get_project_root(), "src", "msg")


def get_package_dir(package_name: str) -> str:
    return os.path.join(get_msg_dir(), package_name)
