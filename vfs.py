import os
from datetime import datetime

VMODE = True


class Vfs:
    volumes: dict[str, "VfsItem"]
    cwd: "VfsItem"

    def __init__(self) -> None:
        self.cwd = VfsItem(self, "/", None)
        self.volumes = {"/": self.cwd}

    def init(self, path: str):
        path = os.path.abspath(path)
        if not os.path.exists(path) or os.path.isfile(path):
            return False
        if VMODE:
            disc = path
            item = VfsItem(self, disc, None)
            cur = item
        else:
            disc, *parts = path.replace("\\", "/").split("/")
            item = VfsItem(self, disc, None)
            cur = item.follow_path(parts)
            if not cur:
                return False
        self.cwd = cur
        self.volumes = {disc: item}
        return True

    def getcwd(self):
        return self.cwd.path()

    def read_file(self, fname: str):
        from console import print
        file = self.cwd.follow_path(fname)
        if not file:
            print(f"file not found: {fname}")
            return None
        content, r = file.read_file()
        if r == 0:
            return content
        elif r == 1:
            print(f"path is folder: {fname}")
        elif r == 2:
            print(f"file not found: {fname}")
        else:
            print(f"can't read file: {fname}")


class VfsItem:
    vfs: Vfs
    name: str
    parent: "VfsItem | None"
    is_file: bool = False

    @property
    def is_dir(self):
        return not self.is_file

    def __init__(self, vfs: Vfs, name: str, parent: "VfsItem | None", *, is_file: bool = False):
        self.vfs = vfs
        self.name = name
        self.parent = parent
        self.is_file = is_file

    __children__: dict[str, "VfsItem"] | None = None

    @property
    def children(self) -> dict[str, "VfsItem"]:
        if self.__children__:
            return self.__children__
        self.__children__ = {}
        if self.is_file:
            return self.__children__
        path = self.real_path()
        if os.path.exists(path):
            for name in os.listdir(path):
                is_file = os.path.isfile(os.path.join(path, name))
                item = VfsItem(self.vfs, name, self, is_file=is_file)
                self.__children__[name] = item
        return self.__children__

    def follow_path(self, path: str | list[str]) -> "VfsItem | None":
        if isinstance(path, str):
            path = path.replace("\\", "/").strip()
            parts = [p.strip() for p in path.split("/")]
            if path == "/":
                parts = ["/"]
            elif path.startswith("/"):
                parts[0] = "/"
        else:
            parts = path
        if len(parts) > 0 and (":" in parts[0] or parts[0] == "/"):
            disc, *parts = parts  # add new disc if exist
            if disc == "/":
                root = self
                while root.parent:
                    root = root.parent
                return root.__follow_path__(parts)

            if disc not in self.vfs.volumes:
                if VMODE:
                    return None
                p = os.path.abspath(disc)
                if not os.path.exists(p):
                    return None
                item = VfsItem(self.vfs, disc, None)
                self.vfs.volumes[disc] = item

            return self.vfs.volumes[disc].__follow_path__(parts)
        return self.__follow_path__(parts)

    def __follow_path__(self, path: list[str]) -> "VfsItem | None":
        if len(path) == 0:
            return self
        p, *rest = path
        if p == ".":
            return self.__follow_path__(rest)
        if p == "..":
            if not self.parent:
                return None
            return self.parent.__follow_path__(rest)
        if p not in self.children:
            return None
        return self.children[p].__follow_path__(rest)

    def real_path(self):
        if not self.parent:
            return self.name + os.path.sep
        cur = self
        path = [cur.name]
        while cur.parent:
            cur = cur.parent
            path.append(cur.name)
        return os.path.sep.join(reversed(path))

    def path(self):
        if not self.parent:
            if VMODE:
                return "/"
            return self.name + os.path.sep
        cur = self
        path = [cur.name]
        while cur.parent:
            cur = cur.parent
            path.append(cur.name)
        if VMODE:
            path[-1] = ""
        r = os.path.sep.join(reversed(path))
        if VMODE:
            r = r.replace("\\", "/")
        return r

    def read_file(self):
        if self.is_dir:
            return "", 1
        path = self.real_path()
        if not os.path.exists(path):
            return "", 2
        try:
            with open(path, "r", encoding="utf8") as f:
                return f.read(), 0
        except Exception:
            return "", 3

    def get_mod_date(self):
        modt = os.path.getmtime(self.real_path())
        return datetime.fromtimestamp(modt)
