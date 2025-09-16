from console import clear_console, command, console_size, has_input, input, print, run, vfs


@command(alias="dir")
def ls(args: list[str]):
    """
    Usage: ls [directory]

    > ls
    List current directory contents

    > ls <directory>
    List specified directory contents
    """
    if len(args) > 1:
        print("too many params")
        return
    item = vfs.cwd
    if len(args) == 1:
        path = args[0]
        item = vfs.cwd.follow_path(path)
        if not item:
            print(f"path not found: {path}")
            return
        elif item.is_file:
            print(f"path not folder: {path}")
            return
    for name in item.children.keys():
        print(name)


@command()
def cd(args: list[str]):
    """
    Usage: cd <directory>
    Change the working directory
    """
    if len(args) == 0:
        print(vfs.cwd.path())
        return
    if len(args) > 1:
        print("too many params")
        return
    path = args[0]
    nwd = vfs.cwd.follow_path(path)
    if not nwd:
        print(f"path not found: {path}")
    elif nwd.is_file:
        print(f"path not folder: {path}")
    else:
        vfs.cwd = nwd
