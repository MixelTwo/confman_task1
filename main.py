from time import sleep

import donut
from console import clear_console, command, console_size, has_input, input, print, run


@command("donut")
def cmd_donut(args: list[str]):
    A = 1
    B = 1
    while not has_input():
        w, h = console_size()
        donut.screen_size = min(w, h)
        hshift = " " * ((w - donut.screen_size * 2) // 2)
        A += donut.theta_spacing
        B += donut.phi_spacing
        frame = donut.render_frame(A, B)
        frames = "\n".join(hshift + " ".join(row) for row in frame) + "\nPress Enter to exit"
        clear_console(frames)
        sleep(0.02)
    clear_console()
    print("Thanks to Denbergvanthijs for the donut code!")
    print("https://gist.github.com/Denbergvanthijs/7f6936ca90a683d37216fd80f5750e9c")


@command()
def ls(args: list[str]):
    print("ls", args)


@command()
def cd(args: list[str]):
    print("cd", args)


run()
