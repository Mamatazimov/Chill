import os

from db import DataBase
from gui import ChillTui
from utils import Utils

color_data = Utils.color_data


class Chill:
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser("~"), ".ChillManager", "db")
        os.makedirs(self.db_path, exist_ok=True)
        self.db = DataBase(os.path.join(self.db_path, "database.sqlite3"))
        self.db.init_db()
        self.utils = Utils()

    def chill(self, path: str = "."):
        path = self.utils.clear_path(path)
        if not os.path.exists(path):
            print(
                f"{self.utils.colored_print('This path is incorrect:', color_data['red'])} [{path}]"
            )
            return
        message, is_success = (
            self.utils.show_project_info(self.db, path)
            if self.db.project_exists(path)
            else self.utils.init_new_project(self.db, path)
        )
        msg = (
            f"{self.utils.colored_print('Successful:', color_data['green'])} {message}"
            if is_success
            else f"{self.utils.colored_print('Something went wrong:', color_data['red'])} {message}"
        )
        print(msg)

    def save(self, message: str = "", path: str = "."):
        path = self.utils.clear_path(path)
        message, is_success = self.utils.save(self.db, message, path)
        msg = (
            f"{self.utils.colored_print('Successful:', color_data['green'])} [{message}]"
            if is_success
            else f"{self.utils.colored_print('Something went wrong:', color_data['red'])} [{message}]"
        )
        print(msg)

    def back(self, id: int = -1, path: str = "."):
        path = self.utils.clear_path(path)
        if not self.db.project_exists(path):
            print(
                f"Project not found in this directory [{self.utils.colored_print(path, color_data['red'])}]"
            )
            return

        project_data: tuple = self.db.get_project_id(path)
        flows: dict = self.utils.get_flows(self.db, project_data[0])
        if project_data[1] not in list(flows.keys()):
            print(
                f"This flow [{self.utils.colored_print(project_data[1], color_data['blue'])}] not found in this project flows [{self.utils.colored_print(str(list(flows.keys())), color_data['blue'])}]!"
            )
            return

        if id == -1:
            id = self.db.get_save_by_id(project_data[2])[3]

        if id == -1:
            print(
                self.utils.colored_print(
                    "This save's parent not found!", color_data["blue"]
                )
            )

        is_have = (
            True
            if 1 == len([1 for data in flows[project_data[1]] if data[0] == id])
            else False
        )

        if not is_have:
            print(
                f"This save id [{self.utils.colored_print(str(id), color_data['blue'])}] not found in this flow [{self.utils.colored_print(flows[project_data[1]], color_data['blue'])}]"
            )
            return

        message, is_success = self.utils.build(self.db, id)
        msg = (
            f"{self.utils.colored_print('Successful:', color_data['green'])} [{message}]"
            if is_success
            else f"{self.utils.colored_print('Something went wrong:', color_data['red'])} [{message}]"
        )
        print(msg)

    def list(self, path: str = "."):
        path = self.utils.clear_path(path)
        if not self.db.project_exists(path):
            print(
                f"Project not found in this directory [{self.utils.colored_print(path, color_data['red'])}]"
            )
            return

        message, is_success = self.utils.project_data(self.db, path)
        msg = (
            f"{message}"
            if is_success
            else f"{self.utils.colored_print('Something went wrong:', color_data['red'])} {message}"
        )
        print(msg)

    def flow(self, flow_name: str, path: str = "."):
        path = self.utils.clear_path(path)
        if not self.db.project_exists(path):
            print(
                f"Project not found in this directory [{self.utils.colored_print(path, color_data['red'])}]"
            )
            return

        project_data: tuple = self.db.get_project_id(path)
        flows: dict = self.utils.get_flows(self.db, project_data[0])

        message, is_success = (
            self.utils.change_flow(self.db, flow_name, project_data[0])
            if flow_name in list(flows.keys())
            else self.utils.create_flow(self.db, flow_name, project_data[0])
        )
        msg = (
            f"{self.utils.colored_print('Successful:', color_data['green'])} {message}"
            if is_success
            else f"{self.utils.colored_print('Something went wrong:', color_data['red'])} {message}"
        )
        print(msg)

    def tui(self, path: str = "."):
        app = ChillTui(self.db, path)
        app.run()
