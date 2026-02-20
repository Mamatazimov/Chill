import os
import shutil
from pathlib import Path
from typing import Any, Tuple

from chill_crypt import SecureCoder

sc = SecureCoder("My secret chill key!")


class Chill:
    @staticmethod
    def save_version(version: str, is_opposite: bool = False, path: str = "."):
        if "~" == path[0]:
            path = os.path.join(os.path.expanduser("~"), path[1:])

        path = str(Path(path).resolve())

        if not os.path.exists(path):
            Utils.colored_print("Bunaday manzildagi path topilmadi!", "danger")

        tree: dict[str, Any]
        is_success: bool
        tree, is_success = Utils.get_tree(path)

        if not is_success:
            Utils.colored_print(
                "Manzilni tree shaklini olishda xatolik yuz berdi!", "danger"
            )
        Utils.colored_print(*Utils.save_chill(tree, version, is_opposite))

    @staticmethod
    def get_saves():
        chill_path: str = os.path.join(os.path.expanduser("~"), ".chill")
        projects: list = []
        if not os.path.exists(chill_path):
            Utils.colored_print(f"{chill_path} manzil topilmadi!", "danger")
            return
        projects = os.listdir(chill_path)
        for project in projects:
            versions = Utils.get_project_versions(os.path.join(chill_path, project))
            Utils.colored_print(f"[ {project} ] --> [ {' | '.join(versions)} ]")

    @staticmethod
    def get_versions(project):
        chill_path: str = os.path.join(os.path.expanduser("~"), ".chill")
        if not os.path.exists(chill_path):
            Utils.colored_print(f"{chill_path} manzil topilmadi!", "danger")
            return

        versions = Utils.get_project_versions(os.path.join(chill_path, project))
        Utils.colored_print(f"Ushbu [ {project} ] loyhada [ {' | '.join(versions)} ]")


class Utils:
    @staticmethod
    def get_project_versions(path: str):
        if not os.path.exists(path):
            Utils.colored_print(f"{path} manzil topilmadi!", "danger")
            return []
        folder_names = os.listdir(path)

        versions: list = []
        for folder in folder_names:
            crypted = list(folder.split("_"))[-1]
            version = sc.decrypt(crypted)
            versions.append(version)
        return versions

    @staticmethod
    def get_tree(path: str) -> tuple[dict[str, Any], bool]:
        try:

            def loop(path: str):
                files: list = []
                res: dict[str, Any] = {path: {"files": files, "dirs": {}}}
                for entry in os.scandir(path):
                    if entry.is_file():
                        files.append(entry.name)
                    elif entry.is_dir():
                        res[path]["dirs"][entry.name] = loop(
                            os.path.join(path, entry.name)
                        )

                return res

            return loop(path), True

        except Exception as e:
            Utils.colored_print(f"Error in Utils get_tree: {e}", "danger")
            return {path: {"files": [], "dirs": {}}}, False

    @staticmethod
    def save_file(path, data):
        with open(path, "wb") as file:
            file.write(data)

    @staticmethod
    def get_data(path):
        with open(path, "rb") as file:
            return file.read()

    @staticmethod
    def save_chill(
        tree: dict[str, Any], version: str, is_opposite: bool = False
    ) -> Tuple[str, str]:
        try:
            chill_path: str = os.path.join(os.path.expanduser("~"), ".chill")
            path: str = list(tree.keys())[0]
            pathlib_path: Path = Path(path)
            path_list: list = list(pathlib_path.parts)
            project_name: str = path_list[-1]
            crypted: str = sc.encrypt(version)
            folder_name: str = "_".join(path_list[1:]) + "_" + crypted
            chill_file_path: str = os.path.join(chill_path, project_name, folder_name)

            def loop(
                tree: dict[str, Any],
                from_path: str,
                to_path: str,
            ):
                files: list = tree[list(tree.keys())[0]]["files"]
                dirs: dict = tree[list(tree.keys())[0]]["dirs"]
                os.makedirs(to_path)

                for file in files:
                    to_file_path: str = os.path.join(to_path, file)
                    file_path: str = os.path.join(from_path, file)
                    Utils.colored_print(
                        f"Ushbu {file} fayl ushbu manzilga saqlandi {to_file_path}",
                        "info",
                    )
                    data: bytes = Utils.get_data(file_path)
                    Utils.save_file(to_file_path, data)

                for dir in dirs.keys():
                    curr_tree: dict[str, Any] = dirs[dir]
                    curr_path: str = list(curr_tree.keys())[0]
                    curr_to_path: str = os.path.join(to_path, dir)
                    loop(curr_tree, curr_path, curr_to_path)

            if is_opposite:
                chill_project_path = os.path.join(chill_path, project_name)
                if not os.path.exists(chill_project_path):
                    return f"Bunday loyha topilmadi {project_name} !", "danger"

                versions: list[str] = os.listdir(chill_project_path)
                if not versions:
                    return (
                        "Ushbu loyha bo'yicha umuman versiya fayllari topilmadi!",
                        "danger",
                    )

                project_path = os.path.join(*list(versions[0].split("_"))[:-1])

                if len(list([v for v in versions if v.endswith(crypted)])) != 1:
                    return (
                        "Fayl versiyasi topilmadi! Versiya xato emasligiga ishonch hosil qiling!",
                        "danger",
                    )

                forbidden = ["/", "C:\\", "C:\\Windows", os.path.expanduser("~")]
                if project_path in forbidden:
                    return (
                        "Ushbu manzil tizimga ziyon yetkazishi mumkin deb topilgani uchun bloklandi.",
                        "info",
                    )

                if os.path.exists(project_path):
                    shutil.rmtree(project_path)

                new_tree: dict[str, Any]
                is_success: bool
                new_tree, is_success = Utils.get_tree(chill_file_path)

                if not is_success:
                    return "Fayl versiyasi bilan xatolik yuz berdi!", "danger"

                loop(new_tree, chill_file_path, project_path)
                return "Fayl versiyasidan muvaffaqiyatli nusxa olindi!", "success"
            else:
                loop(tree, path, chill_file_path)
                return "Fayl versiyasi muvaffaqiyatli saqlab qo'yildi!", "success"

        except Exception as e:
            return f"Error in Utils save_chill: {e}", "danger"

    @staticmethod
    def colored_print(data: str, status: str = "default") -> None:
        color_data = {
            "default": "\033[0m",
            "danger": "\033[31m",
            "success": "\033[32m",
            "info": "\033[36m",
        }

        color = color_data.get(status, "\033[0m")
        print(color + data + color_data["default"])
