import os
import platform
import sys
import threading
import tkinter as tk
import tkinter.font as tkFont
from typing import Callable

import pyperclip

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
w, h = 600, 400
x = (window.winfo_screenwidth() - w) // 2
y = (window.winfo_screenheight() - h) // 2
window.geometry(f"{w}x{h}+{x}+{y}")
try:
    dark_title_bar()
except Exception:
    pass

event = threading.Event()
lock = threading.Lock()

console_text = ""
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
            if "\n" in input_buffer:
                event.set()
            update_console_text()
            text.edit_modified(False)


def update_console_text():
    text.delete("1.0", tk.END)
    text.insert("1.0", console_text + input_buffer)
    text.see(tk.END)


def on_key_release(event):
    global history_i, input_buffer
    if event.keysym in ("Up", "Down"):
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
    elif event.keysym == "Escape":
        with lock:
            history_i = len(history)
            input_buffer = ""
            update_console_text()
        text.mark_set("insert", "end")
    elif event.state & 0x4 and event.keysym == "w":
        window.destroy()


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
text.bind("<Button-3>", on_right_click)
text.pack(expand=True, fill="both")


def input(prompt: str = "") -> str:
    global console_text, input_buffer
    print(prompt, end="")
    if "\n" not in input_buffer:
        event.clear()
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


def print(*values: object, sep: str = " ", end: str = "\n"):
    global console_text
    with lock:
        console_text += sep.join(map(str, values)) + end
        update_console_text()


def console_size():
    return text.winfo_width() // char_width - 1, text.winfo_height() // (char_height + 1)


def clear_console(new_text: str = ""):
    global console_text
    with lock:
        console_text = new_text
        update_console_text()


def run():
    t = threading.Thread(target=cmd)
    t.daemon = True
    t.start()
    window.mainloop()
    sys.exit()


commands = {}
history = []
history_i = 0
history_enabled = False


def command(name: str | None = None):
    def decorator(fn: Callable[[list[str]], None]):
        cname = name if name is not None else fn.__name__
        if cname in commands:
            raise Exception(f'Command with name "{cname}" already registered')
        commands[cname] = fn
        return fn
    return decorator


def cmd():
    global history_i, history_enabled
    print("Hello world!")
    while True:
        history_i = len(history)
        history_enabled = True
        line = input("> ").strip()
        history_enabled = False
        if line == "":
            continue
        if line == "exit":
            break
        if line in history:
            history.remove(line)
        history.append(line)
        args = []
        arg = ""
        quote = None
        for ch in line:
            if not quote and ch == " ":
                if arg != "":
                    args.append(arg)
                    arg = ""
            elif ch == quote:
                quote = None
                args.append(arg)
                arg = ""
            elif ch in ('"', "'"):
                quote = ch
            else:
                arg += ch
        args.append(arg)
        if quote:
            print("err: quote not closed")
        else:
            cname = args[0]
            if cname in commands:
                commands[cname](args[1:])
            else:
                print(f'Unknown command: "{cname}"')
    window.destroy()
