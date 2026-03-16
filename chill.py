import ast
import hashlib
import os
import shutil
import traceback
from pathlib import Path
from sqlite3.dbapi2 import Timestamp
from typing import Any, Tuple
from uuid import uuid4

from db import DataBase

color_data = {
    "blue": "\033[36m",
    "black": "\033[0m",
    "red": "\033[31m",
    "green": "\033[32m",
}


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

    def gui(self):
        pass


class Utils:
    def init_new_project(self, db: DataBase, path: str = ".") -> Tuple[str, bool]:
        path = self.clear_path(path)

        if db.project_exists(path):
            return "Project already exists!", False

        if os.path.expanduser("~") not in path:
            return "Chill cannot work with system files!", False

        db.create_project(path)
        return "Project created!", True

    def show_project_info(self, db: DataBase, path: str = ".") -> Tuple[str, bool]:
        path = self.clear_path(path)

        if not db.project_exists(path):
            return "Project not found!", False

        project_id: int

        project_id, *_ = db.get_project_id(path)

        flows: dict = self.get_flows(db, project_id)
        response: list = [
            f"Project have {self.colored_print(str(len(flows.keys())), color_data['blue'])} flows!"
        ]

        for flow, saves in flows.items():
            row = f"{self.colored_print(flow, color_data['blue'])} ==> {self.colored_print(str(len(saves)), color_data['blue'])} saves"
            response.append(row)

        return "\n".join(response), True

    def save(
        self, db: DataBase, message: str = "", path: str = "."
    ) -> Tuple[str, bool]:
        path = self.clear_path(path)
        if not db.project_exists(path):
            return "Project not found!", False

        project_id: int
        project_flow: str
        parent_id: int

        project_id, project_flow, parent_id = db.get_project_id(path)

        uid = str(uuid4())
        db.create_tree(uid)
        tree_id: int = db.get_tree_id(uid)

        saves: list[tuple] = db.get_list_saves_by_project(project_id)
        saves = [save for save in saves if save[-1] == project_flow]

        tree: list[list] = [[], []]
        for root, dirs, files in os.walk(path):
            for file in files:
                path = os.path.join(root, file)
                hash: str = self.hashing_file(path)
                hash_path: str = os.path.join(hash[:3], hash[3:])

                if not db.blob_exists(hash):
                    dst: str = os.path.join(
                        os.path.expanduser("~"), ".ChillManager", "objects"
                    )
                    os.makedirs(os.path.join(dst, hash[:3]), exist_ok=True)
                    db.create_blob(hash_path)
                    try:
                        if not os.path.exists(os.path.join(dst, hash_path)):
                            shutil.copy2(
                                path,
                                os.path.join(dst, hash_path),
                                follow_symlinks=False,
                            )
                    except shutil.SameFileError:
                        pass

                item_id = db.get_blob_id(hash_path)

                tree[0].append([root, file, item_id])

            tree[1].append([root, dirs, files])

        tree_hash = hashlib.sha256(str(str(tree) + project_flow).encode()).hexdigest()
        if db.tree_exists(tree_hash):
            db.delete_tree(tree_id)
            return "This tree already have!", False
        db.update_tree(tree_hash, str(tree), tree_id)

        if message == "":
            message = f"Version 0.{len(saves) if len(saves) > 0 else 1}v and flow {project_flow}"
        time: str = str(Timestamp.now())

        db.create_save(project_id, tree_id, parent_id, message, time, project_flow)
        save_id = db.get_save_id(
            project_id, tree_id, parent_id, message, time, project_flow
        )
        db.update_project_head(project_id, save_id[0])

        return f"New save created with {save_id[0]} id!", True

    def build(self, db: DataBase, save_id: int):
        try:
            save: tuple = db.get_save_by_id(
                save_id
            )  # id, project_id, tree_id, parent_id, comment, time, flow
            project: tuple = db.get_project_by_id(save[1])  # id, path, flow, head_save
            tree: tuple = db.get_tree_by_id(save[2])  # id, hash, tree

            base_path: str = project[1]
            tree_dict: list = ast.literal_eval(tree[2])
            chill_base_path: str = os.path.join(
                os.path.expanduser("~"), ".ChillManager", "objects"
            )

            shutil.rmtree(base_path)
            for root, file, blob_id in tree_dict[0]:
                os.makedirs(root, exist_ok=True)
                blob: str = db.get_blob_by_id(int(blob_id))
                from_path: str = os.path.join(chill_base_path, blob)
                to_path: str = os.path.join(root, file)
                if not root.startswith(base_path):
                    print(f"Unexpected path found [{root}]")
                    continue

                shutil.copy2(from_path, to_path)

            for root, *other in tree_dict[1]:
                os.makedirs(root, exist_ok=True)

            db.update_project_head(project[0], save_id)

            return (
                f"Project path [{base_path}], flow [{save[-1]}], save id [{save[0]}] built!",
                True,
            )

        except Exception as e:
            traceback.print_exc()
            return e, False

    def project_data(self, db: DataBase, path: str = "."):
        path = self.clear_path(path)
        if not db.project_exists(path):
            return "Project not found!", False

        project_id: int
        project_flow: str
        save_head: int

        project_id, project_flow, save_head = db.get_project_id(path)

        response: list = [
            f"Current flow [ {self.colored_print(project_flow, color_data['blue'])} ] and current save id [ {self.colored_print(str(save_head), color_data['blue'])} ]"
        ]

        flows: dict = self.get_flows(db, project_id)

        for flow in flows.keys():
            flow_data = flows[
                flow
            ]  # id, project_id, tree_id, parent_id, comment, time, flow
            for f in flow_data:
                row: str = f"[ save's flow  | {self.colored_print(f[-1], color_data['blue'])} ] [ save id  | {self.colored_print(f[0], color_data['blue'])} ] [ parent save id  | {self.colored_print(f[3], color_data['blue'])} ] [ save's comment  | {self.colored_print(f[4], color_data['blue'])} ] [ time  | {self.colored_print(f[5], color_data['blue'])} ]"
                response.append(row)

        return "\n".join(response), True

    def change_flow(self, db: DataBase, flow_name: str, project_id: int) -> tuple:
        try:
            project_data: tuple = db.get_project_by_id(
                project_id
            )  # id path flow head_save flow_data
            save = db.get_save_by_id(
                project_data[3]
            )  # id, project_id, tree_id, parent_id, comment, time, flow

            if flow_name == project_data[2]:
                return "Current flow and this flow are same!", True

            flow_data: dict = ast.literal_eval(project_data[-1])
            old_tree: tuple = db.get_tree_by_id(save[2])

            tree_hash: str = hashlib.sha256(
                str(str(old_tree[-1]) + flow_name).encode()
            ).hexdigest()

            db.create_tree(tree_hash)
            tree_id = db.get_tree_id(tree_hash)
            db.update_tree(tree_hash, old_tree[-1], tree_id)

            flow_data[project_data[2]] = int(project_data[3])
            db.update_project_flow_data(project_id, flow_data)

            db.update_project_head(project_id, flow_data[flow_name])
            db.update_project_flow(project_id, flow_name)

            return "Flow changed!", True

        except Exception as e:
            traceback.print_exc()
            return e, False

    def create_flow(self, db: DataBase, flow_name: str, project_id: int) -> tuple:
        try:
            project_data: tuple = db.get_project_by_id(
                project_id
            )  # id path flow head_save flow_data

            flow_data: dict = ast.literal_eval(project_data[-1])

            new_save_id: int = self.copy_save(db, project_data[3], flow_name)
            flow_data[flow_name] = new_save_id
            db.update_project_flow_data(project_id, str(flow_data))

            return "Flow created!", True

        except Exception as e:
            traceback.print_exc()
            return e, False

    def hashing_file(self, path: str) -> str:
        with open(path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    def get_flows(self, db: DataBase, project_id: int) -> dict[str, list[Any]]:
        saves: list = db.get_list_saves_by_project(project_id)
        flows: dict = {flow: [] for flow in set([save[-1] for save in saves])}
        for save in saves:
            flow: str = save[-1]
            flows[flow].append(save)
        return flows

    def clear_path(self, path: str) -> str:
        path = path.replace("~", str(os.path.expanduser("~")))
        filter_path = Path(path)
        path = str(filter_path.resolve())
        return path

    def copy_save(self, db: DataBase, save_id: int, flow_name: str):
        save_data: list = list(db.get_save_by_id(save_id))[
            1:
        ]  # id, project_id, tree_id, parent_id, comment, time, flow
        save_data[2], save_data[3], save_data[4], save_data[-1] = (
            0,
            f"Version 0.1v and flow {flow_name}",
            str(Timestamp.now()),
            flow_name,
        )
        db.create_save(*save_data)
        return db.get_save_id(*save_data)[0]

    def colored_print(self, data: str, color: str) -> str:
        return color + str(data) + color_data["black"]
