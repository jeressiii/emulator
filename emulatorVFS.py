import shlex
import os
import datetime
import time
import fnmatch  # для поддержки поиска


# VFS в памяти
class SimpleVFS:
    def __init__(self):
        self.current_dir = "/"
        self.fs = {
            "/": {
                "type": "dir",
                "name": "",
                "permissions": "755",  # права доступа
                "children": {
                    "home": {
                        "type": "dir",
                        "name": "home",
                        "permissions": "755",  # права доступа
                        "children": {
                            "user": {
                                "type": "dir",
                                "name": "user",
                                "permissions": "755",  # права доступа
                                "children": {
                                    "documents": {
                                        "type": "dir",
                                        "name": "documents",
                                        "permissions": "755",  # права доступа
                                        "children": {
                                            "file1.txt": {
                                                "type": "file",
                                                "name": "file1.txt",
                                                "content": "Line 1: Hello World\nLine 2: This is a test\nLine 3: VFS example\nLine 4: Python is great\nLine 5: End of file",
                                                "permissions": "644"  # права доступа
                                            },
                                            "file2.txt": {
                                                "type": "file",
                                                "name": "file2.txt",
                                                "content": "First line\nSecond line\nThird line",
                                                "permissions": "644"  # права доступа
                                            },
                                            "data.csv": {
                                                "type": "file",
                                                "name": "data.csv",
                                                "content": "name,age\nJohn,25\nJane,30",
                                                "permissions": "644"  # права доступа
                                            }
                                        }
                                    },
                                    "logs": {
                                        "type": "dir",
                                        "name": "logs",
                                        "permissions": "755",  # права доступа
                                        "children": {
                                            "app.log": {
                                                "type": "file",
                                                "name": "app.log",
                                                "content": "2024-01-01 ERROR: Something went wrong\n2024-01-01 INFO: Application started\n2024-01-02 WARNING: Low memory\n2024-01-02 INFO: User logged in\n2024-01-03 DEBUG: Processing data",
                                                "permissions": "644"  # права доступа
                                            },
                                            "error.txt": {
                                                "type": "file",
                                                "name": "error.txt",
                                                "content": "Critical error occurred",
                                                "permissions": "644"  # права доступа
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "etc": {
                        "type": "dir",
                        "name": "etc",
                        "permissions": "755",  # права доступа
                        "children": {
                            "config.txt": {
                                "type": "file",
                                "name": "config.txt",
                                "content": "host=localhost\nport=8080\ndebug=true\nversion=1.0",
                                "permissions": "644"  # права доступа
                            },
                            "settings.conf": {
                                "type": "file",
                                "name": "settings.conf",
                                "content": "theme=dark\nlanguage=en",
                                "permissions": "644"  # права доступа
                            },
                            "shadow": {  # файл с ограниченными правами
                                "type": "file",
                                "name": "shadow",
                                "content": "encrypted:password:data",
                                "permissions": "600"  # только владелец может читать/писать
                            }
                        }
                    },
                    "var": {
                        "type": "dir",
                        "name": "var",
                        "permissions": "755",  # права доступа
                        "children": {
                            "log.txt": {
                                "type": "file",
                                "name": "log.txt",
                                "content": "Startup complete\nUser connected\nData processed\nShutdown initiated",
                                "permissions": "644"  # права доступа
                            }
                        }
                    },
                    "tmp": {
                        "type": "dir",
                        "name": "tmp",
                        "permissions": "777",  # полные права для /tmp
                        "children": {}
                    }
                }
            }
        }

    def normalize_path(self, path):
        # нормализует путь, убирая лишние слеши
        if not path:
            return "/"

        # убираем множественные слеши
        parts = [p for p in path.split("/") if p]

        # обрабатываем
        result_parts = []
        for part in parts:
            if part == "..":
                if result_parts:
                    result_parts.pop()
            elif part != ".":
                result_parts.append(part)

        return "/" + "/".join(result_parts) if result_parts else "/"

    def get_current_node(self):
        # получаем текущую директорию
        path_parts = [p for p in self.current_dir.split("/") if p]
        node = self.fs["/"]
        for part in path_parts:
            if part in node["children"]:
                node = node["children"][part]
            else:
                return None
        return node

    def get_node_by_path(self, path):
        # получаем узел по абсолютному пути
        if path == "/":
            return self.fs["/"]

        path_parts = [p for p in path.split("/") if p]
        node = self.fs["/"]

        for part in path_parts:
            if part in node["children"]:
                node = node["children"][part]
            else:
                return None
        return node

    def vfs_ls(self, detailed=False):
        # список файлов в текущей директории VFS
        node = self.get_current_node()
        if not node or node["type"] != "dir":
            return "Error: Directory not found"

        if not node["children"]:
            return "Directory is empty"

        if detailed:
            # подробный вывод с правами
            result = []
            for name, child in node["children"].items():
                perm = child.get("permissions", "644")
                if child["type"] == "dir":
                    result.append(f"d{perm} {name}/")
                else:
                    result.append(f"-{perm} {name}")
            return "\n".join(result)
        else:
            return list(node["children"].keys())

    def vfs_cd(self, path):
        # смена директории в VFS
        if not path:
            return "Error: Path required"

        if path == "~":
            path = "/home"

        # абсолютный путь
        if path.startswith("/"):
            target_path = self.normalize_path(path)
        # относительный путь
        else:
            if self.current_dir == "/":
                target_path = self.normalize_path("/" + path)
            else:
                target_path = self.normalize_path(self.current_dir + "/" + path)

        # проверим существует ли целевая директория
        node = self.get_node_by_path(target_path)
        if not node or node["type"] != "dir":
            return f"Directory not found: {path}"

        self.current_dir = target_path
        return f"Changed to: {self.current_dir}"

    def vfs_pwd(self):
        # текущая директория в VFS
        return self.current_dir

    # mkdir с поддержкой рекурсивного создания
    def vfs_mkdir(self, dirname, recursive=False):
        # создаем директорию в VFS
        if not dirname:
            return "Error: Directory name required"

        # абсолютный или относительный путь
        if dirname.startswith("/"):
            target_path = self.normalize_path(dirname)
        else:
            if self.current_dir == "/":
                target_path = self.normalize_path("/" + dirname)
            else:
                target_path = self.normalize_path(self.current_dir + "/" + dirname)

        parts = [p for p in target_path.split("/") if p]
        if not parts:
            return "Error: Cannot create root directory"

        # если не рекурсивно, создаем только последнюю директорию
        if not recursive:
            dir_name = parts[-1]
            parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"

            parent = self.get_node_by_path(parent_path)
            if not parent or parent["type"] != "dir":
                return f"Error: Parent directory not found: {parent_path}"

            if dir_name in parent["children"]:
                return f"Directory already exists: {dir_name}"

            parent["children"][dir_name] = {
                "type": "dir",
                "name": dir_name,
                "permissions": "755",  # стандартные права для директории
                "children": {}
            }
            return f"Directory created: {target_path}"

        else:
            # рекурсивное создание всех недостающих директорий
            current = self.fs["/"]
            current_path = "/"

            for i, part in enumerate(parts):
                if part in current["children"]:
                    if current["children"][part]["type"] != "dir":
                        return f"Error: Path component is not a directory: {part}"
                    current = current["children"][part]
                    current_path = current_path + part + "/" if current_path != "/" else "/" + part + "/"
                else:
                    # создаем недостающую директорию
                    current["children"][part] = {
                        "type": "dir",
                        "name": part,
                        "permissions": "755",
                        "children": {}
                    }
                    current = current["children"][part]
                    current_path = current_path + part + "/" if current_path != "/" else "/" + part + "/"

            return f"Directories created recursively: {target_path}"

    def vfs_touch(self, filename):
        # создаем файл в VFS
        if not filename:
            return "Error: File name required"

        node = self.get_current_node()
        if not node or node["type"] != "dir":
            return "Error: Not in a directory"

        if filename in node["children"]:
            return f"File already exists: {filename}"

        node["children"][filename] = {
            "type": "file",
            "name": filename,
            "content": "",
            "permissions": "644"  # стандартные права для файла
        }
        return f"File created: {filename}"

    def vfs_chmod(self, mode, target):
        # изменение прав доступа файла/директории в VFS
        if not mode or not target:
            return "Error: Mode and target required"

        # валидация режима
        if not (mode.isdigit() and len(mode) == 3 and all(0 <= int(c) <= 7 for c in mode)):
            return f"Error: Invalid mode format: {mode}. Use octal notation (e.g., 755, 644)"

        # абсолютный или относительный путь
        if target.startswith("/"):
            target_path = self.normalize_path(target)
        else:
            if self.current_dir == "/":
                target_path = self.normalize_path("/" + target)
            else:
                target_path = self.normalize_path(self.current_dir + "/" + target)

        node = self.get_node_by_path(target_path)
        if not node:
            return f"Error: Target not found: {target}"

        # применяем новые права
        node["permissions"] = mode

        return f"Changed permissions of '{target_path}' to {mode}"

    def vfs_tail(self, filename, lines=10):
        # выводим последние строки файла
        if not filename:
            return "Error: File name required"

        # абсолютный или относительный путь
        if filename.startswith("/"):
            file_path = self.normalize_path(filename)
        else:
            if self.current_dir == "/":
                file_path = self.normalize_path("/" + filename)
            else:
                file_path = self.normalize_path(self.current_dir + "/" + filename)

        node = self.get_node_by_path(file_path)
        if not node:
            return f"File not found: {filename}"

        if node["type"] != "file":
            return f"Not a file: {filename}"

        content = node.get("content", "")
        if not content:
            return f"File is empty: {filename}"

        # разбиваем на строки и берем последние N
        all_lines = content.split('\n')
        start_line = max(0, len(all_lines) - lines)
        result_lines = all_lines[start_line:]

        return '\n'.join(result_lines)

    def vfs_find(self, start_path="/", name=None, type_filter=None):
        # поиск файлов и директорий
        if not start_path or start_path == ".":
            start_path = self.current_dir
        elif start_path == "..":
            # поднимаемся на уровень выше
            if self.current_dir == "/":
                start_path = "/"
            else:
                parts = [p for p in self.current_dir.split("/") if p]
                if parts:
                    parts.pop()
                start_path = "/" + "/".join(parts) if parts else "/"

        start_node = self.get_node_by_path(self.normalize_path(start_path))
        if not start_node:
            return f"Directory not found: {start_path}"

        results = []

        def search_recursive(node, current_path):
            # проверяем совпадение по имени
            match_found = False
            if name:
                if fnmatch.fnmatch(node["name"], name):
                    match_found = True
            else:
                match_found = True

            # проверяем фильтр по типу
            type_match = True
            if type_filter:
                if type_filter == "f" and node["type"] != "file":
                    type_match = False
                elif type_filter == "d" and node["type"] != "dir":
                    type_match = False

            # добавляем в результаты если все условия выполнены
            if match_found and type_match:
                full_path = current_path + node["name"]
                results.append(full_path)

            # рекурсивно ищем в дочерних элементах для директорий
            if node["type"] == "dir" and "children" in node:
                for child_name, child_node in node["children"].items():
                    # формируем путь для дочернего элемента
                    if current_path == "/":
                        child_current_path = "/"
                    else:
                        child_current_path = current_path + node["name"] + "/"
                    search_recursive(child_node, child_current_path)

        # запускаем поиск
        search_path = start_path if start_path.endswith("/") else start_path + "/"
        if search_path == "//":  # исправляем двойной слеш для корня
            search_path = "/"
        search_recursive(start_node, search_path)

        return results


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

    # VFS команды
    if parts[0] == 'ls':
        detailed = '-l' in parts
        result = vfs.vfs_ls(detailed)
        print(result)

    elif parts[0] == 'cd':
        if len(parts) > 1:
            result = vfs.vfs_cd(parts[1])
            print(result)
        else:
            result = vfs.vfs_cd("~")
            print(result)

    elif parts[0] == 'pwd':
        result = vfs.vfs_pwd()
        print(result)

    elif parts[0] == 'mkdir':
        if len(parts) < 2:
            print("Error: Directory name required")
            return

        recursive = '-p' in parts
        dirnames = [p for p in parts[1:] if p != '-p']

        for dirname in dirnames:
            result = vfs.vfs_mkdir(dirname, recursive)
            print(result)

    elif parts[0] == 'touch':
        if len(parts) > 1:
            result = vfs.vfs_touch(parts[1])
            print(result)
        else:
            print("Error: File name required")

    elif parts[0] == 'chmod':
        if len(parts) < 3:
            print("Write the complete command")
            return

        mode = parts[1]
        target = parts[2]
        result = vfs.vfs_chmod(mode, target)
        print(result)

    elif parts[0] == 'tail':
        lines = 10  # по умолчанию 10 строк
        filename = None

        # обработка аргументов
        i = 1
        while i < len(parts):
            if parts[i] == '-n' and i + 1 < len(parts):
                try:
                    lines = int(parts[i + 1])
                    i += 2
                except ValueError:
                    print("Error: Invalid number of lines")
                    return
            else:
                filename = parts[i]
                i += 1

        if not filename:
            print("Error: File name required")
            return

        result = vfs.vfs_tail(filename, lines)
        print(result)

    elif parts[0] == 'date':
        if len(parts) > 1 and parts[1] == '+%Y-%m-%d':
            # форматированная дата
            print(datetime.datetime.now().strftime("%Y-%m-%d"))
        elif len(parts) > 1 and parts[1] == '+%H:%M:%S':
            # форматированное время
            print(datetime.datetime.now().strftime("%H:%M:%S"))
        else:
            # стандартный вывод
            print(datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"))

    elif parts[0] == 'find':
        start_path = "."
        name_pattern = None
        type_filter = None

        i = 1
        while i < len(parts):
            if parts[i] == '-name' and i + 1 < len(parts):
                name_pattern = parts[i + 1]
                i += 2
            elif parts[i] == '-type' and i + 1 < len(parts):
                type_filter = parts[i + 1]
                i += 2
            else:
                start_path = parts[i]
                i += 1

        results = vfs.vfs_find(start_path, name_pattern, type_filter)
        if isinstance(results, list):
            if results:
                for result in results:
                    print(result)
            else:
                print("No files found")
        else:
            print(results)

    elif parts[0] == 'test':
        try:
            with open('test_vfs.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        print(f'{vfs_name}$ {line}')
                        act(line)
        except FileNotFoundError:
            print("test_vfs.txt: file not found")

    else:
        print(f'{parts[0]}: command not found')


if __name__ == "__main__":
    print("=== VFS Emulator with Permissions ===")
    print("Доступные команды: ls, cd, pwd, mkdir, touch, chmod, tail, date, find, test, exit")
    print(f"Текущая VFS директория: {vfs.vfs_pwd()}")

    while True:
        command = input(f'{vfs_name}$ ')
        act(command)