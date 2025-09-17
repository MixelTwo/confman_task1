import os
import platform
import re
import sys
import threading
import tkinter as tk
import tkinter.font as tkFont
from typing import Callable
import unicodedata

import pyperclip

from args import Args
from vfs import VMODE, Vfs

stdinput = input
stdprint = print

username = os.getlogin()
hostname = platform.node()

folder = "data"
try:
    folder = os.path.join(sys._MEIPASS, folder)  # type: ignore
except Exception:
    pass


def is_windows_11():
    if sys.platform == "win32":
        return sys.getwindowsversion().build >= 22000
    return False


def dark_title_bar():
    if not is_windows_11():
        return
    import ctypes as ct
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ct.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2
    value = ct.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))


window = tk.Tk()
window.title(f"Emulator - {username}@{hostname}")
window.iconbitmap(os.path.join(folder, "favicon.ico"))
window.config(bg="#0c0c0c")
w, h = 900, 500
x = (window.winfo_screenwidth() - w) // 2
y = (window.winfo_screenheight() - h) // 2
window.geometry(f"{w}x{h}+{x}+{y}")
try:
    dark_title_bar()
except Exception:
    pass

event = threading.Event()
event_anykey = threading.Event()
event_anykey_toset = False
event_anykey.set()
lock = threading.Lock()

console_text = ""
console_tags: list[tuple[int, int, str]] = []
input_buffer = ""


def on_text_change(e):
    global console_text, input_buffer
    if text.edit_modified():
        if lock.locked():
            text.edit_modified(False)
            return
        with lock:
            new_text = text.get("1.0", tk.END)[:-1]
            changed_text = new_text[:len(console_text)]
            to_end = False
            if console_text == changed_text:
                input_buffer = new_text[len(console_text):]
            else:
                old_text = console_text + input_buffer
                oldl = len(old_text)
                newl = len(new_text)
                si, ei = 0, 1
                while si < oldl and si < newl and old_text[si] == new_text[si]:
                    si += 1
                while oldl - ei > 0 and newl - ei > 0 and old_text[oldl - ei] == new_text[newl - ei]:
                    ei += 1
                input_buffer = new_text[si:newl - ei + 1]
                to_end = True
            if "\n" in input_buffer:
                event.set()
            update_console_text()
            if to_end:
                text.mark_set("insert", "end")
            text.edit_modified(False)


def update_console_text():
    pos = text.index(tk.INSERT)
    nl = "\n" if input_buffer.endswith("\n") else ""
    inp = input_buffer.split("\n")[0] + nl if not event.is_set() else ""
    text.replace("1.0", tk.END, console_text + inp)
    text.see(tk.END)
    text.mark_set("insert", pos)
    for (s, e, tag) in console_tags:
        text.tag_add(tag, f"1.0+{s} chars", f"1.0+{e} chars")


def on_key_release(event):
    global history_i, input_buffer, autocomplete_moveto, ctrl_backspace_moveto, event_anykey_toset
    if event.state & 0x4 and event.keysym == "w":
        window.destroy()
        return
    if not event_anykey.is_set():
        if event_anykey_toset:
            event_anykey_toset = False
            event_anykey.set()
        return
    if event.keysym == "Return":
        with lock:
            input_buffer += "\n"
            update_console_text()
    elif event.keysym in ("Up", "Down"):
        pos = get_cursor_input_char_position()
        if pos < 0:
            return
        if not history_enabled:
            text.mark_set("insert", "end")
            return
        if event.keysym == "Up":
            history_i -= 1
        else:
            history_i += 1
        history_i = max(min(history_i, len(history) - 1), 0)
        if len(history) > 0:
            with lock:
                input_buffer = history[history_i]
                update_console_text()
        text.mark_set("insert", "end")
    elif event.state & 0x4 and event.keysym == "Left":
        pos = get_cursor_input_char_position()
        if pos < 0:
            if "\n" not in console_text[pos:]:
                text.mark_set("insert", f"1.0+{len(console_text)} chars")
    elif event.keysym == "Escape":
        with lock:
            history_i = len(history)
            input_buffer = ""
            update_console_text()
        text.mark_set("insert", "end")
    elif event.keysym == "Tab":
        if autocomplete_moveto >= 0:
            text.mark_set("insert", f"1.0+{len(console_text) + autocomplete_moveto} chars")
            autocomplete_moveto = -1
    elif event.state & 0x4 and event.keysym == "BackSpace":
        if ctrl_backspace_moveto >= 0:
            text.mark_set("insert", f"1.0+{len(console_text) + ctrl_backspace_moveto} chars")
            ctrl_backspace_moveto = -1
    elif event.keysym == "Home":
        pos = get_cursor_input_char_position()
        if pos >= 0:
            text.mark_set("insert", f"1.0+{len(console_text)} chars")


def on_key_press(event):
    global autocomplete, autocomplete_start, autocomplete_i, input_buffer, autocomplete_moveto, event_anykey_toset
    if not event_anykey.is_set():
        event_anykey_toset = True
        return "break"
    if event.keysym != "Tab":
        autocomplete = None
    if event.keysym == "Return":
        return "break"
    if event.keysym in ("Up", "Down", "Home"):
        pos = get_cursor_input_char_position()
        if pos >= 0:
            return "break"
        return
    if event.keysym in ("Left", "BackSpace"):
        pos = get_cursor_input_char_position()
        if pos == 0:
            return "break"
        return
    if not autocomplete_enabled:
        return
    if event.keysym != "Tab":
        return
    cpos = get_cursor_input_char_position()
    if cpos < 0:
        return "break"
    if autocomplete is None:
        autocomplete = ""
        quote = False
        quoteI = 0
        for i in range(min(cpos - 1, len(input_buffer))):
            if input_buffer[i] == '"':
                quoteI = i
                quote = not quote
        if quote:
            autocomplete = input_buffer[quoteI:cpos]
            autocomplete_start = quoteI
        else:
            i = cpos - 1
            while i >= 0 and i < len(input_buffer) and input_buffer[i] != " ":
                autocomplete += input_buffer[i]
                i -= 1
            autocomplete_start = i + 1
            autocomplete = autocomplete[::-1]
        autocomplete_i = -1
        autocomplete = autocomplete.replace("\\", "/")
    startswith = autocomplete.strip('"')
    prefix = ""
    item = vfs.cwd
    if "/" in autocomplete:
        sw = startswith
        *path, startswith = startswith.split("/")
        sep = "/" if VMODE else os.path.sep
        prefix = sep.join(path) + sep
        if sw.startswith("/"):
            path[0] = "/"
        try:
            item = item.follow_path(path)
        except Exception as x:
            print(x)
            return "break"
        if not item:
            return "break"
    try:
        items = sorted(it for it in item.children.keys() if it.startswith(startswith))
    except Exception as x:
        print(x)
        return "break"
    if len(items) == 0:
        return "break"
    autocomplete_i = (autocomplete_i + 1) % len(items)
    item = prefix + items[autocomplete_i]
    if " " in item:
        if not autocomplete.startswith('"'):
            autocomplete = '"' + autocomplete
        item = f'"{item}"'
    with lock:
        end = cpos
        if cpos < len(input_buffer) and input_buffer[cpos] == '"':
            end += 1
        input_buffer = input_buffer[:autocomplete_start] + item + input_buffer[end:]
        autocomplete_moveto = autocomplete_start + len(item)
        if len(item) > 0 and item[-1] == '"':
            autocomplete_moveto -= 1
        update_console_text()
    return "break"


def get_cursor_char_position():
    insert_index = text.index(tk.INSERT)
    char_position = text.count("1.0", insert_index, "chars")
    if char_position:
        return char_position[0]
    return 0


def get_cursor_input_char_position():
    add = sum(1 for ch in console_text if unicodedata.east_asian_width(ch) == "W")
    console_text_len = len(console_text) + add
    return get_cursor_char_position() - console_text_len


ctrl_backspace_moveto = -1
ctrl_backspace_chars = (" ", "_", "/", "\\")


def ctrl_backspace(event):
    global input_buffer, ctrl_backspace_moveto
    pos = get_cursor_input_char_position()
    if pos < 0:
        return "break"
    start = pos - 1
    sp = start >= 0 and start < len(input_buffer) and input_buffer[start] in ctrl_backspace_chars
    spch = input_buffer[start] if sp else ""
    while start >= 0 and start < len(input_buffer) and (
            (sp and input_buffer[start] == spch) or (not sp and input_buffer[start] not in ctrl_backspace_chars)):
        start -= 1
    start += 1
    with lock:
        input_buffer = input_buffer[:start] + input_buffer[pos:]
        update_console_text()
        ctrl_backspace_moveto = start
    return "break"


def ctrl_delete(event):
    global input_buffer, ctrl_backspace_moveto
    pos = get_cursor_input_char_position()
    if pos < 0:
        return "break"
    end = pos
    sp = end < len(input_buffer) and input_buffer[end] in ctrl_backspace_chars
    spch = input_buffer[end] if sp else ""
    while end < len(input_buffer) and (
            (sp and input_buffer[end] == spch) or (not sp and input_buffer[end] not in ctrl_backspace_chars)):
        end += 1
    with lock:
        input_buffer = input_buffer[:pos] + input_buffer[end:]
        update_console_text()
    return "break"


def on_right_click(e):
    sel_start, sel_end = text.tag_ranges("sel")
    if sel_start and sel_end:
        selected_text = text.get(sel_start, sel_end)
        pyperclip.copy(selected_text)
        text.tag_remove("sel", "1.0", tk.END)


font = tkFont.Font(family="Consolas", size=11)
char_width = font.measure("0")
char_height = font.metrics()["linespace"]
text = tk.Text(window,
               bg="#0c0c0c",
               fg="#f3f3f3",
               insertbackground="#f3f3f3",
               selectbackground="#f3f3f3",
               selectforeground="#0c0c0c",
               font=font,
               )
text.bind("<<Modified>>", on_text_change)
text.bind("<KeyRelease>", on_key_release)
text.bind('<KeyPress>', on_key_press)
text.bind("<Control-BackSpace>", ctrl_backspace)
text.bind("<Control-Delete>", ctrl_delete)
text.bind("<Button-3>", on_right_click)
text.pack(expand=True, fill="both")

text.tag_config("red", foreground="#ff0000")
text.tag_config("green", foreground="#00ff00")
text.tag_config("blue", foreground="#1d58ff")


class Tags:
    red = "red"
    green = "green"
    blue = "blue"


def input(prompt: str = "", tags: str | list[str] | None = None) -> str:
    global console_text, input_buffer
    print(prompt, end="", tags=tags)
    if "\n" not in input_buffer:
        text.mark_set("insert", "end")
        event.clear()
        with lock:
            update_console_text()
        event.wait()
    with lock:
        i = input_buffer.index("\n")
        r = input_buffer[:i]
        console_text += r + "\n"
        input_buffer = input_buffer[i + 1:]
        update_console_text()
    return r


def has_input():
    return "\n" in input_buffer


def print(*values: object, sep: str = " ", end: str = "\n", tags: str | list[str] | None = None):
    global console_text
    with lock:
        l = len(console_text)
        console_text += sep.join(map(str, values)) + end
        if tags:
            tags = [tags] if isinstance(tags, str) else tags
            for tag in tags:
                console_tags.append((l, len(console_text), tag))
        update_console_text()


def print_err(*values: object, sep: str = " ", end: str = "\n", tags: str | list[str] | None = None):
    if not tags:
        tags = []
    tags = [tags] if isinstance(tags, str) else tags
    tags.append(Tags.red)
    print(*values, sep=sep, end=end, tags=tags)


def console_size():
    return text.winfo_width() // char_width - 1, text.winfo_height() // (char_height + 1)


def clear_console(new_text: str = ""):
    global console_text, console_tags
    with lock:
        console_text = new_text
        console_tags = []
        update_console_text()


def to_new_line():
    global console_text
    with lock:
        if not console_text.endswith("\n"):
            console_text += "\n"
        update_console_text()


def pause():
    event_anykey.clear()
    event_anykey.wait()


def run():
    t = threading.Thread(target=run_cmd)
    t.daemon = True
    t.start()
    text.focus_set()
    window.mainloop()
    sys.exit()


commands: dict[str, Callable[[Args], None]] = {}
commands_help: dict[str, str | None] = {}
commands_aliases: dict[str, list[str]] = {}
history: list[str] = []
history_i = 0
history_enabled = False
autocomplete: str | None = None
autocomplete_enabled = False
autocomplete_i = -1
autocomplete_start = 0
autocomplete_moveto = -1

vfs = Vfs()


def command(name: str | None = None, *, alias: str | tuple[str] | None = None, doc: str | None = None):
    aliases: list[str] = []
    if alias:
        if isinstance(alias, str):
            aliases = [alias]
        else:
            aliases = list(alias)

    def decorator(fn: Callable[[Args], None]):
        aliases.append(name if name is not None else fn.__name__)
        help = doc if doc is not None else fn.__doc__
        if help:
            help = remove_doc_indent(help)
        for cname in aliases:
            if cname in commands:
                raise Exception(f'Command with name "{cname}" already registered')
            commands[cname] = fn
            commands_help[cname] = help
            commands_aliases[cname] = aliases
        return fn
    return decorator


def run_cmd():
    try:
        cmd()
    except Exception as x:
        print_err("Error")
        print_err(x)
        input()
    window.destroy()


def cmd():
    global history_i, history_enabled, autocomplete_enabled
    start_script = ""
    args = sys.argv[1:]
    err = False
    if len(args) >= 1:
        if not vfs.init(args[0]):
            err = True
            print_err(f'Cant open folder: "{args[0]}"')
    elif not vfs.init(os.getcwd()):
        err = True
        print_err("Unexpected error")
    if len(args) >= 2:
        start_script = args[1]
    if not err and start_script:
        err = not _load_start_script(start_script)

    if err:
        print("Press Enter to exit")
    else:
        print("Hello world!")

    while True:
        history_i = len(history)
        history_enabled = True
        autocomplete_enabled = True
        to_new_line()
        print(vfs.getcwd(), end="", tags=Tags.green)
        line = input("> ", tags=Tags.blue).strip()
        history_enabled = False
        autocomplete_enabled = False
        if err or line == "exit":
            return
        if line == "":
            continue
        if line in history:
            history.remove(line)
        history.append(line)

        try:
            args = Args.parse(line)
        except Exception as x:
            print_err(x)
            continue
        if args.cmd not in commands:
            print(f'Unknown command: "{args.cmd}"')
            continue

        if args.has("/?", "/h", "-h", "--help"):
            help = commands_help.get(args.cmd, None)
            aliases = commands_aliases.get(args.cmd, [args.cmd])
            if help:
                if len(aliases) > 1:
                    help = "Aliases: " + ", ".join(aliases) + "\n" + help
                print(help + "\n")
            else:
                print("No help for this command")
            continue

        try:
            commands[args.cmd](args)
        except Exception as x:
            print_err(x)


def _load_start_script(path: str):
    global input_buffer
    try:
        with open(path, "r", encoding="utf8") as f:
            with lock:
                input_buffer = f.read() + "\n"
                event.set()
                update_console_text()
    except Exception:
        print(f'Cant open script file: "{path}"')
        return False
    return True


def remove_doc_indent(doc: str):
    lines = doc.strip("\n").replace("\t", "    ").split("\n")
    min_indent = 9999
    for line in lines:
        if line.strip() == "":
            continue
        i = 0
        while i < len(line) and line[i] == " ":
            i += 1
        min_indent = min(min_indent, i)
    if lines[-1].strip() == "":
        lines.pop()
    return "\n".join(line[min_indent:] for line in lines)
