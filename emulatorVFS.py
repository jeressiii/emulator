import shlex
import os

# VFS в памяти
class SimpleVFS:
    def __init__(self):
        self.current_dir = "/"
        self.fs = {
            "/": {
                "type": "dir",
                "name": "",
                "children": {
                    "home": {
                        "type": "dir",
                        "name": "home",
                        "children": {}
                    },
                    "etc": {
                        "type": "dir",
                        "name": "etc",
                        "children": {}
                    }
                }
            }
        }

    def get_current_node(self):
        # Получить текущую директорию
        path_parts = [p for p in self.current_dir.split("/") if p]
        node = self.fs["/"]
        for part in path_parts:
            if part in node["children"]:
                node = node["children"][part]
            else:
                return None
        return node

    def vfs_ls(self):
        # Список файлов в текущей директории VFS
        node = self.get_current_node()
        if not node or node["type"] != "dir":
            return "Error: Directory not found"

        if not node["children"]:
            return "Directory is empty"

        return list(node["children"].keys())

    def vfs_cd(self, path):
        # Смена директории в VFS
        if path == "..":
            # Подняться на уровень выше
            if self.current_dir != "/":
                parts = [p for p in self.current_dir.split("/") if p]
                if parts:
                    parts.pop()
                self.current_dir = "/" + "/".join(parts)
                if self.current_dir == "":
                    self.current_dir = "/"
            return f"Changed to: {self.current_dir}"

        if path == "/":
            self.current_dir = "/"
            return "Changed to root"

        # Проверим существует ли целевая директория
        target_path = self.current_dir + "/" + path if self.current_dir != "/" else "/" + path
        path_parts = [p for p in target_path.split("/") if p]

        node = self.fs["/"]
        for part in path_parts:
            if part in node["children"] and node["children"][part]["type"] == "dir":
                node = node["children"][part]
            else:
                return f"Directory not found: {path}"

        self.current_dir = target_path
        return f"Changed to: {self.current_dir}"

    def vfs_pwd(self):
        # Текущая директория в VFS
        return self.current_dir

    def vfs_mkdir(self, dirname):
        # Создать директорию в VFS
        node = self.get_current_node()
        if not node or node["type"] != "dir":
            return "Error: Not in a directory"

        if dirname in node["children"]:
            return f"Directory already exists: {dirname}"

        node["children"][dirname] = {
            "type": "dir",
            "name": dirname,
            "children": {}
        }
        return f"Directory created: {dirname}"

    def vfs_touch(self, filename):
        # Создать файл в VFS
        node = self.get_current_node()
        if not node or node["type"] != "dir":
            return "Error: Not in a directory"

        if filename in node["children"]:
            return f"File already exists: {filename}"

        node["children"][filename] = {
            "type": "file",
            "name": filename,
            "content": ""
        }
        return f"File created: {filename}"


# Инициализация VFS
vfs = SimpleVFS()
vfs_name = os.getlogin()
exit_cmd = "exit"


def act(a):
    parts = shlex.split(a)
    if a == exit_cmd:
        exit()
    if len(parts) == 0:
        print("")
        return

    # VFS команды (заменяют реальные системные команды)
    if parts[0] == 'ls':
        result = vfs.vfs_ls()
        print(result)

    elif parts[0] == 'cd':
        if len(parts) > 1:
            result = vfs.vfs_cd(parts[1])
            print(result)
        else:
            result = vfs.vfs_cd("/")
            print(result)

    elif parts[0] == 'pwd':
        result = vfs.vfs_pwd()
        print(result)

    elif parts[0] == 'mkdir':
        if len(parts) > 1:
            result = vfs.vfs_mkdir(parts[1])
            print(result)
        else:
            print("Error: Directory name required")

    elif parts[0] == 'touch':
        if len(parts) > 1:
            result = vfs.vfs_touch(parts[1])
            print(result)
        else:
            print("Error: File name required")

    elif parts[0] == 'test':
        try:
            with open('test_vfs.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        print(f'{vfs_name}$ {line}')
                        act(line)
        except FileNotFoundError:
            print("test_fixed.txt: file not found")

    else:
        print(f'{parts[0]}: command not found')


if __name__ == "__main__":
    print("=== VFS Emulator ===")
    print("Доступные команды: ls, cd, pwd, mkdir, touch, test, exit")
    print(f"Текущая VFS директория: {vfs.vfs_pwd()}")

    while True:
        command = input(f'{vfs_name}$ ')
        act(command)