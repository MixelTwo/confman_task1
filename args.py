import argparse
import shlex


class Args:
    cmd: str
    raw: list[str]
    parser: argparse.ArgumentParser

    def __init__(self, args: list[str]):
        cmd, *args = args
        self.cmd = cmd
        self.raw = args
        self.parser = argparse.ArgumentParser(exit_on_error=False)
        self.add_argument = self.parser.add_argument
        self.add_mutually_exclusive_group = self.parser.add_mutually_exclusive_group

    @staticmethod
    def parse(line: str):
        args = shlex.split(line)
        return Args(args)

    def __getitem__(self, i: int):
        return self.raw[i]

    def __len__(self):
        return len(self.raw)

    def has(self, *items: str):
        return any(v in items for v in self.raw)

    def parse_args(self):
        return self.parser.parse_args(self.raw)
