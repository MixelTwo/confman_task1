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
            item.__file_mod_date__ = datetime.now()
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

    def get(self, fname: str):
        file = self.cwd.follow_path(fname)
        if not file:
            raise Exception(f"cannot open '{fname}' for reading: No such file or directory")
        return file

    def find(self, fname: str):
        return self.cwd.follow_path(fname)

    def exists(self, path: str):
        return self.find(path) is not None

    def is_file(self, path: str):
        item = self.find(path)
        return item.is_file if item else False

    def is_dir(self, path: str):
        item = self.find(path)
        return item.is_dir if item else False

    def create_file(self, fname: str):
        file = self.cwd.follow_path(fname)
        if file:
            return file
        rem = []
        d = self.cwd.follow_path(fname, rem=rem)
        if not d or len(rem) != 1:
            raise Exception(f"cannot create '{fname}': No such directory")
        return d.add_file(rem[0])

    def mkdir(self, dname: str):
        d = self.cwd.follow_path(dname)
        if d:
            return d
        rem = []
        d = self.cwd.follow_path(dname, rem=rem)
        if not d or len(rem) == 0:
            raise Exception(f"cannot create '{dname}': No such directory")
        for name in rem:
            d = d.add_dir(name)
        return d


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
        path = self.__real_path__()
        if os.path.exists(path):
            for name in os.listdir(path):
                is_file = os.path.isfile(os.path.join(path, name))
                item = VfsItem(self.vfs, name, self, is_file=is_file)
                self.__children__[name] = item
        return self.__children__

    def follow_path(self, path: str | list[str], rem: list[str] | None = None) -> "VfsItem | None":
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
                return root.__follow_path__(parts, rem)

            if disc not in self.vfs.volumes:
                if VMODE:
                    return None
                p = os.path.abspath(disc)
                if not os.path.exists(p):
                    return None
                item = VfsItem(self.vfs, disc, None)
                self.vfs.volumes[disc] = item

            return self.vfs.volumes[disc].__follow_path__(parts, rem)
        return self.__follow_path__(parts, rem)

    def __follow_path__(self, path: list[str], rem: list[str] | None) -> "VfsItem | None":
        if len(path) == 0:
            return self
        p, *rest = path
        if p == ".":
            return self.__follow_path__(rest, rem)
        if p == "..":
            if not self.parent:
                if rem is not None:
                    rem.extend(path)
                    return self
                return None
            return self.parent.__follow_path__(rest, rem)
        if p not in self.children:
            if rem is not None:
                rem.extend(path)
                return self
            return None
        return self.children[p].__follow_path__(rest, rem)

    def __real_path__(self):
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

    __file_content__: bytes | None = None

    def read(self):
        return self.read_bytes().decode("utf8")

    def read_lines(self):
        return self.read().split("\n")

    def read_bytes(self):
        if self.__file_content__ is not None:
            return self.__file_content__
        if not self.is_file:
            raise Exception("Is a directory")
        path = self.__real_path__()
        if not os.path.exists(path):
            raise Exception("No such file or directory")
        with open(path, "rb") as f:
            self.__file_content__ = f.read()
            return self.__file_content__

    __file_mod_date__: datetime | None = None

    def write(self, data: str, append: bool = False):
        self.write_bytes(data.encode("utf8"), append)

    def write_bytes(self, data: bytes, append: bool = False):
        if append and self.__file_content__:
            self.__file_content__ += data
        else:
            self.__file_content__ = data
        self.__file_mod_date__ = datetime.now()

    def get_mod_date(self):
        if self.__file_mod_date__:
            return self.__file_mod_date__
        modt = os.path.getmtime(self.__real_path__())
        return datetime.fromtimestamp(modt)

    def add_file(self, fname: str):
        if "/" in fname or "\\" in fname:
            raise Exception("filename cant contain slashes")
        item = VfsItem(self.vfs, fname, self, is_file=True)
        item.__file_mod_date__ = datetime.now()
        self.children[fname] = item
        return item

    def add_dir(self, dname: str):
        if "/" in dname or "\\" in dname:
            raise Exception("dirname cant contain slashes")
        item = VfsItem(self.vfs, dname, self, is_file=False)
        item.__file_mod_date__ = datetime.now()
        self.children[dname] = item
        return item

    def listdir(self):
        return list(self.children.values()) if self.is_dir else []

    def copy_to(self, dest: "VfsItem", recursive: bool = False, overwrite: bool = True,
                interactive: bool = False, verbose: bool = False, overwrite_name: str | None = None):
        from console import input, print
        sep = "/" if VMODE else os.path.sep
        if self.is_file:
            if self.name in dest.children:
                if not overwrite:
                    if verbose:
                        print(f"cp: not overwriting '{dest.path()}{sep}{self.name}'")
                    return
                if interactive:
                    ans = input(f"cp: overwrite '{dest.path()}{sep}{self.name}'? [y/N] ")
                    if ans.lower() != "y":
                        return

            f = dest.add_file(overwrite_name or self.name)
            f.write(self.read())

            if verbose:
                print(f"'{self.path()}' -> '{f.path()}'")

        else:
            if not recursive:
                raise ValueError(f"Cannot copy directory '{self.path()}' without recursive flag")

            name = overwrite_name or self.name
            if name in dest.children and dest.children[name].is_dir:
                new_dir = dest.children[name]
            else:
                new_dir = dest.add_dir(name)

            if verbose:
                print(f"'{self.path()}{sep}' -> '{new_dir.path()}{sep}'")

            for child in self.children.values():
                child.copy_to(new_dir, recursive=recursive, overwrite=overwrite, interactive=interactive, verbose=verbose)
