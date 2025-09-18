import time
from datetime import datetime, timezone

import dateparser

from console import Args, Tags, clear_console, command, console_size, get_console_history, has_input, input, pause, print, print_err, run, vfs


@command(alias="dir")
def ls(args: Args):
    """
    Usage: ls [directory]

    List current directory contents
      > ls

    List specified directory contents
      > ls directory
    """
    if len(args) > 1:
        print("too many arguments")
        return
    item = vfs.cwd
    if len(args) == 1:
        path = args[0]
        item = vfs.cwd.follow_path(path)
        if not item:
            print(f"{path}: No such file or directory")
            return
        if not item.is_dir:
            print(f"{path}: Not a directory")
            return
    for name in item.children.keys():
        print(name)


@command()
def cd(args: Args):
    """
    Usage: cd [directory]
    Change the working directory
    """
    if len(args) == 0:
        print(vfs.cwd.path())
        return
    if len(args) > 1:
        print("too many arguments")
        return
    path = args[0]
    nwd = vfs.cwd.follow_path(path)
    if not nwd:
        print(f"{path}: No such file or directory")
    elif not nwd.is_dir:
        print(f"{path}: Not a directory")
    else:
        vfs.cwd = nwd


@command()
def cat(args: Args):
    """
    Usage: cat [FILE]...
    Concatenate FILE(s) to standard output.
    """
    if len(args) == 0:
        print("specify file")
        return
    for fname in args:
        try:
            file = vfs.find(fname)
            print(file.read())
        except Exception as x:
            print(x)


@command("pause")
def cmd_pause(args: Args):
    print("Press any key to continue . . .")
    pause()


@command()
def clear(args: Args):
    clear_console()


@command()
def history(args: Args):
    """
    history: history [-c] [-d offset] [n]
          or history -anrw [filename]
          or history -s arg [arg...]
    Display or manipulate the history list.

    Display the history list with line numbers.
    An argument of N lists only the last N entries.

    Options:
      -c        clear the history list by deleting all of the entries
      -d offset delete the history entry at position OFFSET. Negative
                offsets count back from the end of the history list

      -a        append history lines from this session to the history file
      -n        read all history lines not already read from the history file
                and append them to the history list
      -r        read the history file and append the contents to the history
                list
      -w        write the current history to the history file

      -s        append the ARGs to the history list as a single entry
    """
    args.add_argument("N", nargs="?", default=-1, type=int)
    g = args.add_mutually_exclusive_group()
    g.add_argument("-c", action="store_true", required=False)
    g.add_argument("-d", required=False, type=int)
    g.add_argument("-a", required=False)
    g.add_argument("-n", required=False)
    g.add_argument("-r", required=False)
    g.add_argument("-w", required=False)
    g.add_argument("-s", nargs="+", required=False)
    argv = args.parse_args()
    history = get_console_history()
    if argv.c:
        history.clear()
        return
    if argv.d is not None:
        history.pop(argv.d)
        return
    if argv.s:
        for v in argv.s:
            history.append(v)
        return
    fname = argv.a or argv.n or argv.r
    if fname:
        item = vfs.cwd.follow_path(fname)
        if not item:
            print(f"{fname}: No such file or directory")
            return
        if not item.is_file:
            print(f"{fname}: Not a file")
            return
    if argv.a:
        for line in history:
            item.write(line + "\n", append=True)
        return
    if argv.n:
        for line in item.read_lines():
            if line not in history:
                history.append(line)
        return
    if argv.r:
        for line in item.read_lines():
            history.append(line)
        return
    if argv.w:
        item = vfs.create_file(argv.w)
        item.write("\n".join(history))
        return

    c = len(history) if argv.N < 0 else argv.N
    ml = len(str(len(history))) + 1
    for i, v in enumerate(history):
        if i >= len(history) - c:
            print(f"%{ml}d  " % i, end="", tags=Tags.blue)
            print(v)


@command()
def date(args: Args):
    """
    Usage: date [OPTION]... [+FORMAT]
    Display date and time in the given FORMAT.

    Mandatory arguments to long options are mandatory for short options too.
    -d, --date=STRING          display time described by STRING, not 'now'
    -f, --file=DATEFILE        like --date; once for each line of DATEFILE
    -I[FMT], --iso-8601[=FMT]  output date/time in ISO 8601 format.
                                FMT='date' for date only (the default),
                                'hours', 'minutes', 'seconds', or 'ns'
                                for date and time to the indicated precision.
                                Example: 2006-08-14T02:34:56-06:00
    -R, --rfc-email            output date and time in RFC 5322 format.
                                Example: Mon, 14 Aug 2006 02:34:56 -0600
        --rfc-3339=FMT         output date/time in RFC 3339 format.
                                FMT='date', 'seconds', or 'ns'
                                for date and time to the indicated precision.
                                Example: 2006-08-14 02:34:56-06:00
    -r, --reference=FILE       display the last modification time of FILE
    -u, --utc, --universal     print Coordinated Universal Time (UTC)
    -h, --help        display this help and exit

    All options that specify the date to display are mutually exclusive.
    I.e.: --date, --file, --reference.

    FORMAT controls the output.  Interpreted sequences are:

    %%   a literal %
    %a   locale's abbreviated weekday name (e.g., Sun)
    %A   locale's full weekday name (e.g., Sunday)
    %b   locale's abbreviated month name (e.g., Jan)
    %B   locale's full month name (e.g., January)
    %c   locale's date and time (e.g., Thu Mar  3 23:05:25 2005)
    %d   day of month (e.g., 01)
    %D   date; same as %m/%d/%y
    %h   same as %b
    %H   hour (00..23)
    %I   hour (01..12)
    %j   day of year (001..366)
    %m   month (01..12)
    %M   minute (00..59)
    %n   a newline
    %f   microsecond (000000..999999)
    %N   microsecond (000000..999999)
    %p   locale's equivalent of either AM or PM; blank if not known
    %R   24-hour hour and minute; same as %H:%M
    %s   seconds since the Epoch (1970-01-01 00:00 UTC)
    %S   second (00..60)
    %t   a tab
    %T   time; same as %H:%M:%S
    %U   week number of year, with Sunday as first day of week (00..53)
    %w   day of week (0..6); 0 is Sunday
    %W   week number of year, with Monday as first day of week (00..53)
    %x   locale's date representation (e.g., 12/31/99)
    %X   locale's time representation (e.g., 23:13:48)
    %y   last two digits of year (00..99)
    %Y   year
    %z   +hhmm numeric time zone (e.g., -0400)
    %Z   alphabetic time zone abbreviation (e.g., EDT)

    Examples:
    Convert seconds since the Epoch (1970-01-01 UTC) to a date
    $ date --date='2147483647'

    Show relative date
    $ date --date='in 2 days'
    """
    args.add_argument("FORMAT", default="%c", nargs="?")
    g1 = args.add_mutually_exclusive_group()
    g1.add_argument("-I", "--iso-8601", required=False, nargs="?", const="date",
                    choices=["date", "d", "hours", "h", "minutes", "m", "seconds", "s", "ns", "n"])
    g1.add_argument("-R", "--rfc-email", required=False, action="store_true")
    g1.add_argument("--rfc-3339", required=False, choices=["date", "d", "seconds", "s", "ns", "n", ])
    g1.add_argument("-u", "--utc", "--universal", required=False, action="store_true")
    g2 = args.add_mutually_exclusive_group()
    g2.add_argument("-d", "--date")
    g2.add_argument("-f", "--file")
    g2.add_argument("-r", "--reference")
    argv = args.parse_args()

    tz = datetime.now(timezone.utc).astimezone().tzinfo
    fmt: str = argv.FORMAT
    if argv.iso_8601:
        match argv.iso_8601[0]:
            case "d": fmt = "%Y-%m-%d"
            case "h": fmt = "%Y-%m-%dT%H%z"
            case "m": fmt = "%Y-%m-%dT%H:%M%z"
            case "s": fmt = "%Y-%m-%dT%H:%M:%S%z"
            case "n": fmt = "%Y-%m-%dT%H:%M:%S,%f%z"
    elif argv.rfc_email:
        fmt = "%a, %d %b %Y %H:%M:%S %z"
    elif argv.rfc_3339:
        match argv.rfc_3339[0]:
            case "d": fmt = "%Y-%m-%d"
            case "s": fmt = "%Y-%m-%d %H:%M:%S%z"
            case "n": fmt = "%Y-%m-%d %H:%M:%S.%f%z"
    elif argv.utc:
        fmt = "%a %b %d %H:%M:%S UTC %Y"

    fmt = fmt.replace("%D", "%m/%d/%y")
    fmt = fmt.replace("%n", "\n")
    fmt = fmt.replace("%N", "%f")
    fmt = fmt.replace("%R", "%H:%M")
    fmt = fmt.replace("%t", "\t")
    fmt = fmt.replace("%T", "%H:%M:%S")

    def conver_date(datev: str | datetime | None = None):
        if isinstance(datev, datetime):
            date = datev.replace(tzinfo=tz)
        elif datev:
            d = datev[1:] if datev.startswith("@") else datev
            date = dateparser.parse(d)
            if not date:
                return "can't parse date"
            if not date.tzinfo:
                date = date.replace(tzinfo=tz)
        else:
            date = datetime.now(tz)
        if "%s" in fmt:
            return str(int(date.timestamp()))
        return date.strftime(fmt)

    if argv.file:
        content = vfs.find(argv.file).read()
        if not content:
            return
        for line in content.strip().split("\n"):
            print(conver_date(line.strip()))
    elif argv.reference:
        file = vfs.cwd.follow_path(argv.reference)
        if not file:
            print(f"{argv.reference}: No such file or directory")
            return
        date = file.get_mod_date()
        print(conver_date(date))
    else:
        print(conver_date(argv.date))


@command()
def head(args: Args):
    """
    Usage: head [OPTION]... [FILE]...
    Print the first 10 lines of each FILE to standard output.
    With more than one FILE, precede each with a header giving the file name.

    Mandatory arguments to long options are mandatory for short options too.
    -c, --bytes=[-]NUM       print the first NUM bytes of each file;
                                with the leading '-', print all but the last
                                NUM bytes of each file
    -n, --lines=[-]NUM       print the first NUM lines instead of the first 10;
                                with the leading '-', print all but the last
                                NUM lines of each file
    -q, --quiet, --silent    never print headers giving file names
    -v, --verbose            always print headers giving file names

    NUM may have a multiplier suffix:
    b 512, kB 1000, K 1024, MB 1000*1000, M 1024*1024,
    GB 1000*1000*1000, G 1024*1024*1024, and so on for T, P, E, Z, Y, R, Q.
    Binary prefixes can be used, too: KiB=K, MiB=M, and so on.
    """
    args.add_argument("FILE", nargs="+")
    g1 = args.add_mutually_exclusive_group()
    g1.add_argument("-c", "--bytes", required=False)
    g1.add_argument("-n", "--lines", required=False)
    g2 = args.add_mutually_exclusive_group()
    g2.add_argument("-q", "--quiet", "--silent", action="store_true", required=False)
    g2.add_argument("-v", "--verbose", action="store_true", required=False)
    argv = args.parse_args()

    def parse_count(v: str, msg: str):
        try:
            return int(v)
        except Exception:
            pass
        i = 0
        while i < len(v) and (v[i].isdigit() or v[i] == "-"):
            i += 1
        num, suffix = v[:i], v[i:]
        try:
            num = int(num)
        except Exception:
            raise Exception(msg)
        suffix = suffix.lower()
        if suffix.endswith("ib"):
            suffix = suffix[:-2]
        mult = 1
        if suffix == "b":
            mult = 512
        else:
            base = 1024
            if suffix.endswith("b"):
                base = 1000
                suffix = suffix[:-1]
            units = ["k", "m", "g", "T", "P", "E", "Z", "Y", "R", "Q"]
            if suffix not in units:
                raise Exception(msg)
            mult = base ** (units.index(suffix) + 1)
        return num * mult

    if not argv.bytes:
        Count = parse_count(argv.lines, f"invalid number of lines: {argv.lines}") if argv.lines else 10
    else:
        Count = parse_count(argv.bytes, f"invalid number of bytes: {argv.bytes}")
    files: list[str] = argv.FILE
    for i, fname in enumerate(files):
        if i > 0:
            print()
        if (len(files) > 1 or argv.verbose) and not argv.quiet:
            if i > 0:
                print()
            print("==> ", end="", tags=Tags.blue)
            print(fname, end="", tags=Tags.green)
            print(" <==", tags=Tags.blue)
        item = vfs.cwd.follow_path(fname)
        if not item:
            print(f"{fname}: No such file or directory")
            continue
        if not item.is_file:
            print(f"{fname}: Not a file")
            continue
        try:
            count = Count
            if not argv.bytes:
                for line in item.read_lines()[:count]:
                    print(line)
            else:
                f = item.read_bytes()
                print(str(f[:count])[2:-1])
        except Exception as x:
            print(f"cannot open '{fname}' for reading: {x}")
