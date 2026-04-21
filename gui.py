import ast
import os

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    Static,
    TextArea,
    Tree,
)

from db import DataBase
from utils import Utils


def save_json_log(data_dict):
    import json

    log_file = "log.json"

    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
        except:
            logs = []

    logs.append(data_dict)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)


def build_tree(node, data, current_flow, mode):
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
                new_node = (
                    node.add(" [blue]" + key + "[/]")
                    if current_flow == key
                    else node.add(" " + key)
                )
                build_tree(new_node, value, current_flow, mode)
            elif mode == 2:
                if key == "files" and isinstance(value, list):
                    build_tree(node, value, current_flow, mode)
                else:
                    new_node = node.add(f" {key}")
                    new_node.data = node.data + [key]
                    build_tree(new_node, value, current_flow, mode)

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


def get_blob_id_by_path(path: str, file: str, data: list, project_path: str):

    for p, f, id in data:
        check_path = os.path.join(project_path, p) if p != "." else project_path

        if path == check_path and file == f:
            return id

    return -1


class ChillTree(Widget):
    def __init__(self, db: DataBase, project_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db
        self.project_id = int(project_id)
        self.border_subtitle = "1"
        self.border_title = "Chill"

    project_id = reactive(0)

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("󱥸 Project", id="project_tree")
        self.notify(str(self.project_id))
        flow = self.db.get_project_by_id(self.project_id)[2]
        build_tree(tree.root, self.utils.get_flows(self.db, self.project_id), flow, 1)
        yield tree

    def watch_project_id(self, old_id: int, new_id: int) -> None:
        if new_id == -1:
            return

        try:
            tree_widget = self.query_one("#project_tree", Tree)
        except Exception:
            return

        tree_widget.clear()
        flow = self.db.get_project_by_id(self.project_id)[2]
        tree_widget.root.data = []
        build_tree(
            tree_widget.root, self.utils.get_flows(self.db, self.project_id), flow, 1
        )
        tree_widget.root.expand()


class ProjectTree(Widget):
    def __init__(self, db: DataBase, save_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db
        self.save_id = save_id
        self.border_subtitle = "2"
        self.border_title = "Tree"
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
        build_tree(tree_widget.root, tree_data, "", 2)
        tree_widget.root.expand()


class ChillFile(Widget):
    def __init__(self, db: DataBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db
        self.border_subtitle = "3"
        self.border_title = "File"

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


class ProjectPaths(Widget):
    def __init__(self, db: DataBase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.utils = Utils()
        self.db = db
        self.all_path = self.db.get_list_projects()

    def compose(self) -> ComposeResult:
        yield Static("Opening New Project", id="PP_Header")
        yield ListView(
            *[ListItem(Label(f"ID {path[0]} {path[1]}")) for path in self.all_path],
            id="Paths",
        )

    def on_list_view_selected(self, event: ListView.Selected):
        node_childs = event.item.children
        label: Label = node_childs[0]
        app = self.app
        app.path = str(str(label.content).split(" ")[2])
        tree = self.app.query_one(ChillTree)
        tree.project_id = int(list(str(label.content).split(" "))[1])
        self.display = False

    DEFAULT_CSS = """
        ProjectPaths{
            display: none;
        }
        #PP_Header{
           background: gray;
           text-align: center;
           width: 100%;
           border: double white;
           text-style: bold;
        }
        ListView{
            padding: 1 3;
            text-align: center;
            text-style: bold;
        }
        Label{
            text-align: center;
            width: 100%;
        }
        ListItem{
            margin: 0 0 1 0;
        }
        ListItem:even{
            border: round gray;
            background: #212121;
            color: white;
        }
        ListItem:odd{
            background: gray;
            border: dashed #212121;
            color: black;
        }
    """


class ChillTui(App):
    def __init__(self, db: DataBase, path: str):
        super().__init__()
        self.utils = Utils()
        self.db = db
        self.path = path

    TITLE = "Chill Tui App"

    def compose(self) -> ComposeResult:
        yield Header(True)
        yield LoadingIndicator()
        with Horizontal(id="trees-container"):
            with Container(id="chill-tree") as c:
                c.data = "h"
                yield ChillTree(
                    self.db, self.db.get_project_id(self.utils.clear_path(self.path))[0]
                )
                yield ProjectTree(self.db, -1)
            yield ChillFile(self.db)
        yield ProjectPaths(self.db)
        yield Footer()
        self.notify(str(self.db.get_project_id(self.utils.clear_path(self.path))[0]))

    def on_key(self, event):
        if event.key == "1":
            self.query_one(ChillTree).display = not bool(
                self.query_one(ChillTree).display
            )
            self.query_one("#chill-tree").display = (
                False
                if self.query_one(ChillTree).display
                == self.query_one(ProjectTree).display
                == False
                else True
            )

        elif event.key == "2":
            self.query_one(ProjectTree).display = not bool(
                self.query_one(ProjectTree).display
            )
            self.query_one("#chill-tree").display = (
                False
                if self.query_one(ChillTree).display
                == self.query_one(ProjectTree).display
                == False
                else True
            )
        elif event.key == "3":
            self.query_one(ChillFile).display = not bool(
                self.query_one(ChillFile).display
            )

        if self.query_one(ProjectTree).display == bool(
            not self.query_one(ChillTree).display
        ):
            curr = ProjectTree if self.query_one(ProjectTree).display else ChillTree
            self.query_one(curr).styles.row_span = 2
            self.query_one(curr).styles.column_span = 2

        if (
            self.query_one(ProjectTree).display
            == self.query_one(ChillTree).display
            == True
        ):
            if self.query_one("#chill-tree").data == "h":
                self.query_one(ProjectTree).styles.column_span = 2
                self.query_one(ChillTree).styles.column_span = 2
                self.query_one(ProjectTree).styles.row_span = 1
                self.query_one(ChillTree).styles.row_span = 1
            else:
                self.query_one(ProjectTree).styles.column_span = 1
                self.query_one(ChillTree).styles.column_span = 1
                self.query_one(ProjectTree).styles.row_span = 2
                self.query_one(ChillTree).styles.row_span = 2

        if (
            self.query_one(ProjectTree).display
            == self.query_one(ChillTree).display
            == self.query_one(ChillFile).display
            == False
        ):
            self.query_one(LoadingIndicator).display = True
        else:
            self.query_one(LoadingIndicator).display = False

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
            self.query_one(ProjectTree).save_id = int(label.split(" ")[2])

        elif label[0] == "":
            sub_path: str = (
                os.path.join(*data) if isinstance(data, list) and len(data) > 0 else ""
            )
            self.notify(self.path)
            blob_path: str = (
                os.path.join(self.utils.clear_path(self.path), sub_path)
                if len(sub_path) > 0
                else self.utils.clear_path(self.path)
            )
            blobs_data = self.query_one(ProjectTree).data
            self.notify(f"{blob_path}, {label[2:]}")
            blob_id = get_blob_id_by_path(
                blob_path, label[2:], blobs_data, self.utils.clear_path(self.path)
            )
            if blob_id == -1:
                self.notify(f"Not found blob id for this file.", severity="error")
            chillfile = self.query_one(ChillFile)
            chillfile.blob_data = (int(blob_id), str(label.split(".")[-1]))

    def action_other_project(self):
        project_paths = self.query_one(ProjectPaths)
        project_paths.display = not bool(project_paths.display)

    def action_change_pos_1_2(self):
        self.notify("aaa")
        if self.query_one("#chill-tree").data == "h":
            self.query_one(ProjectTree).styles.column_span = 1
            self.query_one(ChillTree).styles.column_span = 1
            self.query_one(ProjectTree).styles.row_span = 2
            self.query_one(ChillTree).styles.row_span = 2
            self.query_one("#chill-tree").data = "v"
        else:
            self.query_one(ProjectTree).styles.column_span = 2
            self.query_one(ChillTree).styles.column_span = 2
            self.query_one(ProjectTree).styles.row_span = 1
            self.query_one(ChillTree).styles.row_span = 1
            self.query_one("#chill-tree").data = "h"

    def action_change_head(self):
        current_save_id = self.query_one(ProjectTree).save_id
        if current_save_id == -1:
            self.notify(
                f"Select [yellow] flow [/yellow] from Chill section",
                severity="warning",
            )
            return

        save = self.db.get_save_by_id(current_save_id)
        message, is_success = self.utils.change_flow(self.db, save[-1], int(save[1]))
        if is_success:
            dt = self.app.query_one(ChillTree).project_id
            self.app.query_one(ChillTree).project_id = -1
            self.app.query_one(ChillTree).project_id = dt
            self.notify(f"Flow changed to [blue]{save[-1]}[/]", severity="information")
        else:
            self.notify(message, severity="error")

    def action_change_head_save(self):
        current_save_id = self.query_one(ProjectTree).save_id
        if current_save_id == -1:
            self.notify(
                f"Select [yellow] flow [/yellow] from Chill section",
                severity="warning",
            )
            return

        save = self.db.get_save_by_id(current_save_id)
        project_data = self.db.get_project_by_id(save[1])

        if project_data[2] == save[-1]:
            self.db.update_project_head(int(save[1]), current_save_id)
            self.notify(f"Flow head updated!", severity="information")
        else:
            self.notify(
                f"Head does not changed!\nFlows are not same!", severity="error"
            )

    def action_build_selected_save(self):
        current_save_id = self.query_one(ProjectTree).save_id
        if current_save_id == -1:
            self.notify(
                f"Select [yellow] flow [/yellow] from Chill section",
                severity="warning",
            )
            return

        message, is_success = self.utils.build(self.db, current_save_id)
        if is_success:
            self.notify("Save [green]success[/] builded!", severity="information")
            self.exit()
            print("After building tui stop running!")
        else:
            self.notify(f"Error: {message}", severity="error")

    def action_new_save(self):
        current_save_id = self.query_one(ProjectTree).save_id
        if current_save_id == -1:
            self.notify(
                f"Select [yellow] flow [/yellow] from Chill section",
                severity="warning",
            )
            return

        save = self.db.get_save_by_id(current_save_id)
        project_data = self.db.get_project_by_id(save[1])

        message, is_success = self.utils.save(self.db, path=project_data[1])
        if is_success:
            self.notify(f"Message: {message}!", severity="information")
        else:
            self.notify(f"Error: {message}", severity="error")

    BINDINGS = [
        ("ctrl+1", "change_pos_1_2", "Chill ~ Tree"),
        ("^q", "quit", "Quit"),
        ("ctrl+o", "other_project", "Open Other Project"),
        ("ctrl+f", "change_head", "Change Flow"),
        ("ctrl+a", "change_head_save", "Change Flow Head"),
        ("ctrl+b", "build_selected_save", "Build Save"),
        ("ctrl+s", "new_save", "New Save"),
    ]

    CSS = """
        LoadingIndicator{
            display: none;
            width: 100%;
            height: 90%;
        }
        ChullTui{
            background: green;
        }
        Tree{
            padding: 1;
            background: transparent;
        }
        #chill-tree{
            width: 50fr;
            layout: grid;
            grid-size: 2 2;
        }
        ChillTree, ProjectTree{
            background: transparent;
            padding: 1;
            border: double gray;
            column-span: 2;
        }
        ChillFile{
            width: 70fr;
            border: double gray;
        }
    """
