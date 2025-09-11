import os


class Vfs:
    volumes: dict[str, "VfsItem"]
    cwd: "VfsItem"

    def __init__(self) -> None:
        self.cwd = VfsItem(self, "~", None)
        self.volumes = {"~": self.cwd}

    def init(self, path: str):
        path = os.path.abspath(path)
        if not os.path.exists(path) or os.path.isfile(path):
            return False
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
        path = self.path()
        if os.path.exists(path):
            for name in os.listdir(path):
                is_file = os.path.isfile(os.path.join(path, name))
                item = VfsItem(self.vfs, name, self, is_file=is_file)
                self.__children__[name] = item
        return self.__children__

    def follow_path(self, path: str | list[str]) -> "VfsItem | None":
        parts = [p.strip() for p in path.replace("\\", "/").split("/")] \
            if isinstance(path, str) else path
        if len(parts) > 0 and ":" in parts[0]:
            disc, *parts = parts
            if disc in self.vfs.volumes:
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

    def path(self):
        if not self.parent:
            return self.name + os.path.sep
        cur = self
        path = [cur.name]
        while cur.parent:
            cur = cur.parent
            path.append(cur.name)
        return os.path.sep.join(reversed(path))
