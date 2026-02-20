import os
from pathlib import Path


def chill_init():
    home_path = os.path.expanduser("~")
    current_path = Path.cwd()
    path_list = list(current_path.parts)
    chill_path = os.path.join(home_path, ".chill")

    if ".chill" not in os.listdir(home_path):
        os.mkdir(chill_path)

    if path_list[-1] not in os.listdir(chill_path):
        os.mkdir(os.path.join(chill_path, path_list[-1]))
