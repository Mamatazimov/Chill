import ast
import hashlib
import json
import os
import shutil
import sqlite3
import traceback
from pathlib import Path
from sqlite3.dbapi2 import Timestamp
from typing import Any, Tuple
from uuid import uuid4

from db import DataBase


class Utils:
    color_data = {
        "blue": "\033[36m",
        "black": "\033[0m",
        "red": "\033[31m",
        "green": "\033[32m",
    }

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
            f"Project have {self.colored_print(str(len(flows.keys())), self.color_data['blue'])} flows!"
        ]

        for flow, saves in flows.items():
            row = f"{self.colored_print(flow, self.color_data['blue'])} ==> {self.colored_print(str(len(saves)), self.color_data['blue'])} saves"
            response.append(row)

        return "\n".join(response), True

    def save(
        self, db: DataBase, message: str = "", path: str = "."
    ) -> Tuple[str, bool]:
        path = self.clear_path(path)
        print(path)
        if not db.project_exists(path):
            return "Project not found!", False

        project_id: int
        project_flow: str
        parent_id: int

        project_id, project_flow, parent_id, *_data = db.get_project_id(path)

        uid = str(uuid4())
        db.create_tree(uid)
        tree_id: int = db.get_tree_id(uid)
        self.chillignore: dict = {
            "left": set(),
            "mid": set(),
            "right": set(),
            "full": set(),
            "folders": {".chillbek", ".venv"},
            "changed": False,
        }

        saves: list[tuple] = db.get_list_saves_by_project(project_id)
        saves = [save for save in saves if save[-1] == project_flow]
        tree: list[list] = [[], []]
        for root, dirs, files in os.walk(path):
            if root == path and ".chillignore" in files:
                is_success: bool
                self.chillignore, is_success = self.get_chillignore(
                    os.path.join(path, ".chillignore")
                )
                self.chillignore["changed"] = True
                if not is_success:
                    return self.chillignore["error"], False

            if self.is_folder_ignored(
                set(Path(root.replace(path, "", count=1)).parts), self.chillignore
            ):
                continue

            tree_root = Path(root).relative_to(Path(path)).as_posix()
            saved_files = []
            for file in files:
                if self.chillignore["changed"] and self.is_file_ignored(
                    file, self.chillignore
                ):
                    continue

                file_path = os.path.join(root, file)
                hash: str = self.hashing_file(file_path)
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
                                file_path,
                                os.path.join(dst, hash_path),
                                follow_symlinks=False,
                            )
                    except Exception as e:
                        print(f"Error in moving file {path} :", str(e))
                        pass

                item_id = db.get_blob_id(hash_path)
                saved_files.append(file)
                tree[0].append([tree_root, file, item_id])

            _dirs: set = self.chillignore["folders"].copy()
            dirs = [dir for dir in dirs if len(dirs) == len(_dirs | set(dir))]
            tree[1].append([tree_root, dirs, saved_files])

        tree_hash = hashlib.sha256(str(str(tree) + project_flow).encode()).hexdigest()
        if db.tree_exists(tree_hash):
            db.delete_tree(tree_id)
            tree_id = db.get_tree_id(tree_hash)
            if self.search_tree(db, project_flow, project_id):
                return "This tree already has in this flow", False

        else:
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
            if os.path.exists(base_path):
                shutil.rmtree(base_path)
            for root, file, blob_id in tree_dict[0]:
                root = os.path.join(base_path, root)
                os.makedirs(os.path.join(base_path, root), exist_ok=True)
                blob: str = db.get_blob_by_id(int(blob_id))
                from_path: str = os.path.join(chill_base_path, blob)
                to_path: str = os.path.join(root, file)

                if not os.path.exists(root):
                    print(f"Unexpected path found [{root}]")
                    continue

                shutil.copy2(from_path, to_path)

            for root, *other in tree_dict[1]:
                os.makedirs(os.path.join(base_path, root), exist_ok=True)

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

        project_id, project_flow, save_head, *_data = db.get_project_id(path)

        response: list = [
            f"Current flow [ {self.colored_print(project_flow, self.color_data['blue'])} ] and current save id [ {self.colored_print(str(save_head), self.color_data['blue'])} ]"
        ]

        flows: dict = self.get_flows(db, project_id)

        for flow in flows.keys():
            flow_data = flows[
                flow
            ]  # id, project_id, tree_id, parent_id, comment, time, flow
            for f in flow_data:
                row: str = f"[ save's flow  | {self.colored_print(f[-1], self.color_data['blue'])} ] [ save id  | {self.colored_print(f[0], self.color_data['blue'])} ] [ parent save id  | {self.colored_print(f[3], self.color_data['blue'])} ] [ save's comment  | {self.colored_print(f[4], self.color_data['blue'])} ] [ time  | {self.colored_print(f[5], self.color_data['blue'])} ]"
                response.append(row)

        return "\n".join(response), True

    def change_flow(self, db: DataBase, flow_name: str, project_id: int) -> tuple:
        try:
            project_data: tuple = db.get_project_by_id(
                project_id
            )  # id path flow head_save flow_data
            if flow_name == project_data[2]:
                return "Current flow and this flow are same!", True

            db.update_project_head(project_id, 0)
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
            flow_data[flow_name] = 0
            db.update_project_flow_data(project_id, str(flow_data))

            return "Flow created!", True

        except Exception as e:
            traceback.print_exc()
            return e, False

    def clear_base(self, db: DataBase):
        try:
            data = {
                "projects": set(),
                "trees": set(),
                "blobs": set(),
            }

            projects: list = db.get_list_projects()
            for row in projects:
                data["projects"].add(int(row[0]))

            projects_len: int = len(data["projects"])
            saves: list = db.get_list_saves()
            for row in saves:
                pr_id = row[1]
                pr_data: set = data["projects"].copy()
                pr_data.add(pr_id)
                if len(pr_data) > projects_len:
                    db.delete_save(row[0])
                    print("Save: ", row[0])
                    projects_len += 1
                    continue
                data["trees"].add(row[2])

            trees: list = db.get_list_trees()
            in_use_trees: set = data["trees"]
            all_trees: set = set([row[0] for row in trees])
            deleting_tree: set = all_trees - in_use_trees

            for id in deleting_tree:
                db.delete_tree(id)
                print("Tree: ", id)

            for row in trees:
                raw_tree: str = row[2]
                rb_tree: list = ast.literal_eval(raw_tree)

                blobs: list = rb_tree[0]
                for blob in blobs:
                    data["blobs"].add(blob[2])

            in_use_blobs: set = data["blobs"]
            all_blobs: set = set([row[0] for row in db.get_list_blobs()])
            deleting_blobs: set = all_blobs - in_use_blobs
            for id in deleting_blobs:
                db.delete_blob(id)
                print("Blob: ", id)

            return "Success", True

        except Exception as e:
            return e, False

    def export_project(self, db: DataBase, project_id: int) -> tuple:
        try:
            # id, path, flow, head_save, flow_data
            project_data: tuple = db.get_project_by_id(project_id)
            chill_base_path: str = os.path.join(
                os.path.expanduser("~"), ".ChillManager", "objects"
            )
            chillbek_path: str = os.path.join(project_data[1], ".chillbek")
            blob_files_path: str = os.path.join(chillbek_path, "blobs")

            if os.path.exists(chillbek_path):
                shutil.rmtree(chillbek_path)
            os.makedirs(blob_files_path)

            data: dict = {"project": project_data}

            saves: list = db.get_list_saves(project_id)
            blobs: set = set()
            trees: list = []

            for save in saves:
                tree_data: tuple = db.get_tree_by_id(save[2])
                tree: list = ast.literal_eval(tree_data[2])
                for blob_data in tree[0]:
                    blob: str = db.get_blob_by_id(int(blob_data[-1]))
                    blobs.add((int(blob_data[-1]), blob))

                    from_path: str = os.path.join(chill_base_path, blob)
                    to_path: str = os.path.join(blob_files_path, blob)
                    os.makedirs(os.path.join(blob_files_path, blob[:3]), exist_ok=True)
                    try:
                        shutil.copy2(from_path, to_path)
                    except Exception as e:
                        print("Problem with this file!", from_path)
                        continue

                for file_data in tree[1]:
                    file_data[0] = str(file_data[0]).replace(
                        str(project_data[1]), ".", 1
                    )

                trees.append((tree_data[0], tree_data[1], tree))

            data["saves"] = saves
            data["trees"] = trees
            data["blobs"] = list(blobs)

            with open(os.path.join(chillbek_path, "data.json"), "w") as outfile:
                json.dump(data, outfile)

            return "Project ready for export!", True

        except Exception as e:
            traceback.print_exc()
            return e, False

    def import_project(self, db: DataBase, path: str) -> tuple:
        try:
            path = self.clear_path(path)
            chillbek_path = os.path.join(path, ".chillbek")
            data_file = os.path.join(chillbek_path, "data.json")

            if not os.path.exists(data_file):
                return "No export data found in .chillbek folder!", False

            with open(data_file, "r") as f:
                data = json.load(f)

            if db.project_exists(path):
                inp = input(
                    "Project already exists in database!\nChoose (Y)es for delete and importing or Other for stop protcess!"
                )
                if inp.lower() == "yes" or inp.lower() == "y":
                    db.delete_project(db.get_project_id(path)[0])
                    self.clear_base(db)
                else:
                    return "Protcess stopped!", False

            chill_base_path = os.path.join(
                os.path.expanduser("~"), ".ChillManager", "objects"
            )
            blob_files_path = os.path.join(chillbek_path, "blobs")

            blob_id_map = {}
            for blob in data["blobs"]:
                blob_hash_path = blob[1]
                from_path = os.path.join(blob_files_path, blob_hash_path)
                to_path = os.path.join(chill_base_path, blob_hash_path)
                if os.path.exists(from_path):
                    os.makedirs(os.path.dirname(to_path), exist_ok=True)
                    try:
                        shutil.copy2(from_path, to_path)
                    except Exception as e:
                        print("Error: ", str(e))
                        continue
                if not db.blob_exists(blob_hash_path):
                    db.create_blob(blob_hash_path)
                new_id = db.get_blob_id(blob_hash_path)
                blob_id_map[blob[0]] = new_id

            p_info = data["project"]
            db.create_project(
                path, flow=p_info[2], flow_data=ast.literal_eval(p_info[4])
            )
            project_id = db.get_project_id(path)[0]

            tree_id_map = {}
            for tree_item in data["trees"]:
                content = tree_item[2]
                for item in content[0]:
                    try:
                        item[-1] = blob_id_map[item[-1]]
                    except KeyError:
                        print("This item blob not found:", item)
                        continue

                uid = str(uuid4())
                db.create_tree(uid)
                new_tree_id = db.get_tree_id(uid)
                db.update_tree(uid, str(tree_item[2]), new_tree_id)
                tree_id_map[tree_item[0]] = new_tree_id

            save_id_map = {}
            for s in data["saves"]:
                # s: id, project_id, tree_id, parent_id, comment, time, flow
                old_id = s[0]
                new_tree_id = tree_id_map.get(s[2], 0)
                tree: tuple = db.get_tree_by_id(new_tree_id)
                new_tree_hash: str = hashlib.sha256(
                    str(str(tree[2]) + s[6]).encode()
                ).hexdigest()
                try:
                    db.update_tree(new_tree_hash, tree[2], tree[0])
                except sqlite3.IntegrityError:
                    if new_tree_id != -1:
                        db.delete_tree(new_tree_id)
                        new_tree_id = db.get_tree_id(new_tree_hash)

                db.create_save(project_id, new_tree_id, 0, s[4], s[5], s[6])

                new_save_id = db.get_save_id(
                    project_id, new_tree_id, 0, s[4], s[5], s[6]
                )[0]
                save_id_map[old_id] = new_save_id

            for s in data["saves"]:
                old_id = s[0]
                old_parent_id = s[3]
                if old_parent_id and old_parent_id != -1:
                    new_parent_id = save_id_map.get(old_parent_id, 0)
                    db.update_save_parent(save_id_map[old_id], new_parent_id)

            new_head = save_id_map.get(p_info[3], 0)
            db.update_project_head(project_id, new_head)

            old_flow_data = ast.literal_eval(p_info[4])
            new_flow_data = {
                flow: save_id_map.get(sid, -1) for flow, sid in old_flow_data.items()
            }
            db.update_project_flow_data(project_id, str(new_flow_data))

            return "Project successfully imported!", True

        except Exception as e:
            traceback.print_exc()
            return str(e), False

    def is_folder_ignored(self, folders, data):
        return True if len(set(data["folders"]) & set(folders)) > 0 else False

    def is_file_ignored(self, file, data):
        def sliding_window(text, ln):
            res = set()
            for i in range(len(text) - ln + 1):
                res.add(text[i : i + ln])
            return res

        lst: list = [
            set([file[:i] for i in range(len(file))]),  # l
            set([file[i:] for i in range(len(file))]),  # r
            set(),
        ]
        if len(data["left"] & lst[0]) > 0 or len(data["right"] & lst[1]) > 0:
            return True

        if len(set([file]) & data["full"]) == 1:
            return True

        mid_lens: set = set([len(f) for f in data["mid"]])
        for mid_len in mid_lens:
            lst[2] |= sliding_window(file, mid_len)

        if len(lst[2] & data["mid"]) > 0:
            return True

        return False

    def get_chillignore(self, path: str):
        try:
            res: dict = {
                "left": set(),
                "mid": set(),
                "right": set(),
                "full": set(),
                "folders": {".chillbek", ".venv"},
            }

            with open(path, "r") as file:
                lst: list[str] = file.read().splitlines()

            for line in lst:
                if line == "*":
                    continue
                if line[-1] == "/":
                    res["folders"].add(line[:-1])
                elif line.startswith("*") and line.endswith("*"):
                    res["mid"].add(line[1:-1])
                elif line.startswith("*"):
                    res["right"].add(line[1:])
                elif line.endswith("*"):
                    res["left"].add(line[:-1])
                else:
                    res["full"].add(line)

            return res, True
        except Exception as e:
            return {"error": e}, False

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

    def search_tree(self, db: DataBase, project_flow, project_id):
        saves = db.get_list_saves_by_project(int(project_id))

        for save in saves:
            if save[-1] == project_flow:
                return True

        return False

    def colored_print(self, data: str, color: str) -> str:
        return color + str(data) + self.color_data["black"]
