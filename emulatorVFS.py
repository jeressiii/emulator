import shlex
import os
import datetime
import time
import fnmatch
import stat
from pathlib import Path


# Реальная файловая система
class RealVFS:
    def __init__(self, base_path="C:/test_vfs"):
        self.base_path = Path(base_path)
        self.current_dir = self.base_path

        # Создаем базовую структуру, если она не существует
        self._initialize_filesystem()

    def _initialize_filesystem(self):
        """Создает базовую структуру директорий если они не существуют"""
        try:
            # Создаем основную директорию
            self.base_path.mkdir(exist_ok=True)

            # Создаем поддиректории
            folders = ['folder1', 'folder2', 'folder3']
            for folder in folders:
                folder_path = self.base_path / folder
                folder_path.mkdir(exist_ok=True)

                # Создаем несколько тестовых файлов в каждой папке
                test_files = {
                    'file1.txt': 'Line 1: Hello World\nLine 2: This is a test\nLine 3: VFS example\nLine 4: Python is great\nLine 5: End of file',
                    'file2.txt': 'First line\nSecond line\nThird line',
                    'data.csv': 'name,age\nJohn,25\nJane,30'
                }

                for filename, content in test_files.items():
                    file_path = folder_path / filename
                    if not file_path.exists():
                        file_path.write_text(content, encoding='utf-8')

            # Создаем несколько дополнительных файлов в корне
            root_files = {
                'config.txt': 'host=localhost\nport=8080\ndebug=true\nversion=1.0',
                'readme.md': '# Test VFS Directory\n\nThis is a test directory for VFS operations.'
            }

            for filename, content in root_files.items():
                file_path = self.base_path / filename
                if not file_path.exists():
                    file_path.write_text(content, encoding='utf-8')

        except Exception as e:
            print(f"Warning: Could not initialize filesystem: {e}")

    def normalize_path(self, path):
        """Нормализует путь"""
        if not path:
            return self.current_dir

        path_obj = Path(path)

        # Если путь абсолютный
        if path_obj.is_absolute():
            # Убедимся, что путь находится внутри base_path для безопасности
            try:
                relative_path = path_obj.relative_to(self.base_path)
                return self.base_path / relative_path
            except ValueError:
                # Если путь вне base_path, возвращаем base_path
                return self.base_path
        else:
            # Относительный путь
            return self.current_dir / path_obj

    def get_permissions_string(self, path):
        """Получает строку прав доступа в формате Unix"""
        try:
            file_stat = path.stat()
            permissions = stat.filemode(file_stat.st_mode)
            return permissions[1:]  # убираем первый символ типа файла
        except:
            return "755"  # значение по умолчанию при ошибке

    def vfs_ls(self, detailed=False):
        """Список файлов в текущей директории"""
        try:
            if not self.current_dir.exists() or not self.current_dir.is_dir():
                return "Error: Directory not found"

            items = list(self.current_dir.iterdir())
            if not items:
                return "Directory is empty"

            if detailed:
                result = []
                for item in sorted(items):
                    try:
                        perm = self.get_permissions_string(item)
                        if item.is_dir():
                            result.append(f"d{perm} {item.name}/")
                        else:
                            result.append(f"-{perm} {item.name}")
                    except:
                        result.append(f"?????? {item.name}")
                return "\n".join(result)
            else:
                return [item.name for item in sorted(items)]

        except Exception as e:
            return f"Error: {e}"

    def vfs_cd(self, path):
        """Смена директории"""
        if not path:
            return "Error: Path required"

        try:
            if path == "~":
                target_path = self.base_path
            elif path.startswith("/"):
                # Абсолютный путь относительно base_path
                rel_path = path[1:]  # убираем начальный слеш
                target_path = self.base_path / rel_path
            else:
                # Относительный путь
                target_path = self.current_dir / path

            # Разрешаем путь (обрабатываем .. и .)
            target_path = target_path.resolve()

            # Убедимся, что целевой путь находится внутри base_path
            try:
                target_path.relative_to(self.base_path)
            except ValueError:
                return "Error: Access denied - path outside base directory"

            if not target_path.exists():
                return f"Directory not found: {path}"
            if not target_path.is_dir():
                return f"Not a directory: {path}"

            self.current_dir = target_path
            return f"Changed to: {self.current_dir}"

        except Exception as e:
            return f"Error: {e}"

    def vfs_pwd(self):
        """Текущая директория"""
        try:
            # Возвращаем путь относительно base_path
            if self.current_dir == self.base_path:
                return "/"
            else:
                relative_path = self.current_dir.relative_to(self.base_path)
                return "/" + str(relative_path).replace("\\", "/")
        except:
            return "/"

    def vfs_mkdir(self, dirname, recursive=False):
        """Создает директорию"""
        if not dirname:
            return "Error: Directory name required"

        try:
            target_path = self.normalize_path(dirname)

            # Убедимся, что путь находится внутри base_path
            try:
                target_path.relative_to(self.base_path)
            except ValueError:
                return "Error: Access denied - path outside base directory"

            if recursive:
                target_path.mkdir(parents=True, exist_ok=True)
                return f"Directories created recursively: {target_path}"
            else:
                if target_path.exists():
                    return f"Directory already exists: {dirname}"
                target_path.mkdir(parents=False)
                return f"Directory created: {target_path}"

        except Exception as e:
            return f"Error: {e}"

    def vfs_touch(self, filename):
        """Создает файл"""
        if not filename:
            return "Error: File name required"

        try:
            file_path = self.current_dir / filename

            # Убедимся, что путь находится внутри base_path
            try:
                file_path.relative_to(self.base_path)
            except ValueError:
                return "Error: Access denied - path outside base directory"

            if file_path.exists():
                # Обновляем время модификации существующего файла
                file_path.touch(exist_ok=True)
                return f"File timestamp updated: {filename}"
            else:
                # Создаем новый файл
                file_path.touch()
                return f"File created: {filename}"

        except Exception as e:
            return f"Error: {e}"

    def vfs_chmod(self, mode, target):
        """Изменяет права доступа (эмуляция для Windows)"""
        if not mode or not target:
            return "Error: Mode and target required"

        # В Windows нет настоящих прав Unix, поэтому эмулируем
        if not (mode.isdigit() and len(mode) == 3 and all(0 <= int(c) <= 7 for c in mode)):
            return f"Error: Invalid mode format: {mode}. Use octal notation (e.g., 755, 644)"

        try:
            target_path = self.normalize_path(target)

            if not target_path.exists():
                return f"Error: Target not found: {target}"

            # В реальной системе Windows мы не можем изменить права Unix-style
            # Но можем установить базовые атрибуты
            if mode == "000":
                # Только для демонстрации - устанавливаем как скрытый
                import subprocess
                subprocess.run(['attrib', '+H', str(target_path)], shell=True, capture_output=True)

            return f"Changed permissions of '{target}' to {mode} (simulated on Windows)"

        except Exception as e:
            return f"Error: {e}"

    def vfs_tail(self, filename, lines=10):
        """Выводит последние строки файла"""
        if not filename:
            return "Error: File name required"

        try:
            file_path = self.current_dir / filename

            if not file_path.exists():
                return f"File not found: {filename}"
            if not file_path.is_file():
                return f"Not a file: {filename}"

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            if not content:
                return f"File is empty: {filename}"

            all_lines = content.split('\n')
            start_line = max(0, len(all_lines) - lines)
            result_lines = all_lines[start_line:]

            return '\n'.join(result_lines)

        except Exception as e:
            return f"Error reading file: {e}"

    def vfs_find(self, start_path=".", name=None, type_filter=None):
        """Поиск файлов и директорий"""
        try:
            if start_path == ".":
                search_path = self.current_dir
            elif start_path == "..":
                search_path = self.current_dir.parent
            else:
                search_path = self.normalize_path(start_path)

            if not search_path.exists() or not search_path.is_dir():
                return f"Directory not found: {start_path}"

            results = []

            def search_recursive(path):
                try:
                    for item in path.iterdir():
                        # Проверяем совпадение по имени
                        name_match = True
                        if name:
                            name_match = fnmatch.fnmatch(item.name, name)

                        # Проверяем фильтр по типу
                        type_match = True
                        if type_filter:
                            if type_filter == "f" and not item.is_file():
                                type_match = False
                            elif type_filter == "d" and not item.is_dir():
                                type_match = False

                        # Добавляем в результаты если все условия выполнены
                        if name_match and type_match:
                            try:
                                relative_path = item.relative_to(self.base_path)
                                results.append("/" + str(relative_path).replace("\\", "/"))
                            except ValueError:
                                # Пропускаем файлы вне base_path
                                pass

                        # Рекурсивно ищем в поддиректориях
                        if item.is_dir():
                            search_recursive(item)
                except (PermissionError, OSError):
                    pass  # Пропускаем директории без доступа

            search_recursive(search_path)
            return results

        except Exception as e:
            return f"Error: {e}"


# Инициализация VFS
vfs = RealVFS("C:/test_vfs")
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
        if isinstance(result, list):
            for item in result:
                print(item)
        else:
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
    elif parts[0] == 'test1':
        try:
            with open('test_vfs1.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        print(f'{vfs_name}$ {line}')
                        act(line)
        except FileNotFoundError:
            print("test_vfs1.txt: file not found")
    elif parts[0] == 'test2':
        try:
            with open('test_vfs2.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        print(f'{vfs_name}$ {line}')
                        act(line)
        except FileNotFoundError:
            print("test_vfs2.txt: file not found")

    else:
        print(f'{parts[0]}: command not found')


if __name__ == "__main__":
    print("=== Real Filesystem VFS Emulator ===")
    print(f"Базовая директория: {vfs.base_path}")
    print("Доступные команды: ls, cd, pwd, mkdir, touch, chmod, tail, date, find, test, exit")
    print(f"Текущая VFS директория: {vfs.vfs_pwd()}")

    while True:
        command = input(f'{vfs_name}$ ')
        act(command)