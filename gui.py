import ast
import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, TextArea, Tree

from db import DataBase
from utils import Utils


def build_tree(node, data, mode=1):
    """
    ARGS(node, data,
    mode(
        *project -- 1,
        save -- 2
    ))
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if mode == 1:
                new_node = node.add(" " + key)
                build_tree(new_node, value)
            elif mode == 2:
                if key == "files" and isinstance(value, list):
                    build_tree(node, value, 2)
                else:
                    new_node = node.add(f" {key}")
                    new_node.data = node.data + [key]
                    build_tree(new_node, value, 2)

    elif isinstance(data, list):
        for item in data:
            if mode == 1:
                leaf = node.add_leaf(" " + f"ID {item[0]} v")
                leaf.data = {"data": item}
            elif mode == 2:
                leaf = node.add_leaf(f" {item}")


def transform_to_nested(flat_data):
    try:
        nested_tree = {}
        root_path = flat_data[0][0]

        for path, dirs, files in flat_data:
            relative_path = os.path.relpath(path, root_path)

            if relative_path == ".":
                current_level = nested_tree
            else:
                current_level = nested_tree
                for part in relative_path.split(os.sep):
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

            for file in files:
                if "files" not in current_level:
                    current_level["files"] = []
                current_level["files"].append(file)

        return nested_tree
    except Exception as e:
        return {}


def get_blob_id_by_path(path: str, file: str, data: list):
    for p, f, id in data:
        if path == p and file == f:
            return id

    return -1


class ChillTree(Widget):
    def __init__(self, db: DataBase, project_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.utils = Utils()
        self.db = db
        self.project_id = project_id

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("󱥸 Project")
        build_tree(tree.root, self.utils.get_flows(self.db, self.project_id))
        yield tree


class ProjectTree(Widget):
    def __init__(self, db: DataBase, save_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db
        self.save_id = save_id
        self.data = []

    tree_id = reactive(-1)

    def get_save_data_by_id(self, current_id: int) -> dict:
        try:
            res = self.db.get_tree_by_id(current_id)
            res = ast.literal_eval(str(res[2]))
            self.data = res[0]
            return transform_to_nested(res[1])
        except Exception as e:
            self.notify(f"Xato: {str(e)}")
            return {}

    def compose(self) -> ComposeResult:
        yield Tree(" /", id="internal-tree")

    def watch_tree_id(self, old_id: int, new_id: int) -> None:
        if new_id == -1:
            return

        try:
            tree_widget = self.query_one("#internal-tree", Tree)
        except Exception:
            return

        tree_data = self.get_save_data_by_id(new_id)
        tree_widget.clear()
        tree_widget.root.data = []
        build_tree(tree_widget.root, tree_data, 2)
        tree_widget.root.expand()
        self.notify(f"ID {new_id} yuklandi")


class ChillFile(Widget):
    def __init__(self, db: DataBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db

    blob_data = reactive((-1, ""))

    def get_text_data_by_id(self, blob_id: int):
        try:
            blob = self.db.get_blob_by_id(blob_id)
            path = os.path.join(
                os.path.expanduser("~"), ".ChillManager", "objects", blob
            )
            with open(path, "r") as file:
                res = "".join(file.readlines())

            return res
        except Exception as e:
            self.notify(f"Xato: {str(e)}")
            return ""

    def compose(self) -> ComposeResult:
        text_area = TextArea("", read_only=True, language="", id="ChillTextArea")
        yield text_area

    def watch_blob_data(self, old_data: tuple, new_data: tuple) -> None:
        new_id = new_data[0]
        if new_id == -1:
            return

        text = self.get_text_data_by_id(new_id)
        text_area = self.query_one("#ChillTextArea", TextArea)
        text_area.show_line_numbers = True
        text_area.language = self.blob_data[1]
        text_area.load_text(text)


class ChillTui(App):
    def __init__(self, db: DataBase, path: str):
        super().__init__()
        self.utils = Utils()
        self.db = db
        self.path = path

    TITLE = "Chill Tui App"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="trees-container"):
            yield ChillTree(
                self.db, self.db.get_project_id(self.utils.clear_path(self.path))[0]
            )
            yield ProjectTree(self.db, -1)
            yield ChillFile(self.db)
        yield Footer()

    def on_key(self, event):
        if event.key == "backspace":
            pass

    def on_tree_node_selected(self, event: Tree) -> None:
        node = event.node
        label = str(node.label)
        data = [""]
        try:
            data = node.parent.data
        except:
            pass

        if label[0] == "":
            self.query_one(ProjectTree).tree_id = node.data["data"][2]
        elif label[0] == "":
            sub_path: str = (
                os.path.join(*data) if isinstance(data, list) and len(data) > 0 else ""
            )
            blob_path: str = (
                os.path.join(self.utils.clear_path(self.path), sub_path)
                if len(sub_path) > 0
                else self.utils.clear_path(self.path)
            )
            blobs_data = self.query_one(ProjectTree).data
            blob_id = get_blob_id_by_path(blob_path, label[2:], blobs_data)

            self.query_one(ChillFile).blob_data = (
                int(blob_id),
                str(label.split(".")[-1]),
            )

    CSS = """
        ChullTui{
            background: green;
        }
        Tree{
            padding: 1;
            background: transparent;
        }
        ChillTree, ProjectTree{
            background: transparent;
            padding: 1;
            border: dashed gray;
            width: 2fr;
        }
        ProjectTree{
            width: 3fr;
        }
        ChillFile{
            width: 7fr;
        }
    """
