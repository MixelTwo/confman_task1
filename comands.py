from datetime import datetime, timezone

import dateparser

from console import Args, Tags, clear_console, command, console_size, get_console_history, has_input, input, pause, print, print_err, vfs


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
        file = vfs.find(fname)
        if not file:
            print(f"cannot open '{fname}' for reading: No such file or directory")
            continue
        try:
            print(file.read())
        except Exception as x:
            print(f"cannot open '{fname}' for reading: {x}")


@command("pause")
def cmd_pause(args: Args):
    print("Press any key to continue . . .")
    pause()


@command()
def echo(args: Args):
    print(" ".join(args))


@command()
def clear(args: Args):
    clear_console()


@command()
def stat(args: Args):
    """
    Usage: stat FILE...
    Display file or file system status.
    """
    if len(args) == 0:
        print("specify file")
        return
    for fname in args:
        file = vfs.find(fname)
        if not file:
            print(f"cannot open '{fname}' for reading: No such file or directory")
            continue
        try:
            fmt = "%Y-%m-%d %H:%M:%S.%f %z"
            print(f"  File: {file.name}")
            print(f"Access: {file.get_acc_date().strftime(fmt)}")
            print(f"Modify: {file.get_mod_date().strftime(fmt)}")
        except Exception as x:
            print(f"cannot open '{fname}' for reading: {x}")


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
      > date --date='2147483647'

    Show relative date
      > date --date='in 2 days'
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
        content = vfs.get(argv.file).read()
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


@command()
def cp(args: Args):
    """
    Usage: cp [OPTION]... [-T] SOURCE DEST
      or:  cp [OPTION]... SOURCE... DIRECTORY
      or:  cp [OPTION]... -t DIRECTORY SOURCE...
    Copy SOURCE to DEST, or multiple SOURCE(s) to DIRECTORY.

    Mandatory arguments to long options are mandatory for short options too.
      -i, --interactive            prompt before overwrite
      -n, --no-clobber             do not overwrite an existing file and do not fail.
      -R, -r, --recursive          copy directories recursively
      -t, --target-directory=DIRECTORY  copy all SOURCE arguments into DIRECTORY
      -T, --no-target-directory    treat DEST as a normal file
      -v, --verbose                explain what is being done
          --help        display this help and exit
    """
    args.add_argument("sources", nargs="+")
    g = args.add_mutually_exclusive_group()
    g.add_argument("-i", "--interactive", action="store_true")
    g.add_argument("-n", "--no-clobber", action="store_true")
    args.add_argument("-r", "-R", "--recursive", action="store_true")
    args.add_argument("-t", "--target-directory")
    args.add_argument("-T", "--no-target-directory", action="store_true")
    args.add_argument("-v", "--verbose", action="store_true")

    argv = args.parse_args()

    dest = None
    if argv.target_directory:
        dest = argv.target_directory
    elif len(argv.sources) > 1:
        *argv.sources, dest = argv.sources

    if not dest:
        print("cp: missing destination file operand")
        return

    dest_item = vfs.find(dest)

    def do_copy(src: str, dest_path: str):
        src = src.replace("\\", "/")
        dest_path = dest_path.replace("\\", "/").rstrip("/")
        src_item = vfs.find(src.rstrip("/"))
        if not src_item:
            print(f"cp: cannot stat '{src}': No such file or directory")
            return

        trailing_slash = src.endswith("/") and src_item.is_dir

        if dest_item and dest_item.is_dir and not argv.no_target_directory:
            if src_item.is_file or not trailing_slash:
                src_item.copy_to(dest_item, recursive=argv.recursive, overwrite=not argv.no_clobber,
                                 interactive=argv.interactive, verbose=argv.verbose)
            else:
                for child in src_item.listdir():
                    child.copy_to(dest_item, recursive=argv.recursive, overwrite=not argv.no_clobber,
                                  interactive=argv.interactive, verbose=argv.verbose)
        else:
            *dest_parent_path, new_name = dest_path.split("/")
            dest_parent_path = "/".join(dest_parent_path) or "."
            dest_parent = vfs.find(dest_parent_path)
            if not dest_parent or dest_parent.is_file:
                print(f"cp: target '{dest_path}' is not a valid directory")
                return

            if src_item.is_dir and not argv.recursive:
                print(f"cp: -r not specified; omitting directory '{src}'")
                return
            src_item.copy_to(dest_parent, overwrite_name=new_name, recursive=argv.recursive,
                             overwrite=not argv.no_clobber, interactive=argv.interactive, verbose=argv.verbose)

    if len(argv.sources) > 1:
        if not dest_item or dest_item.is_file or argv.no_target_directory:
            print(f"cp: target '{dest}' is not a directory")
            return
        for src in argv.sources:
            do_copy(src, dest)
    else:
        do_copy(argv.sources[0], dest)


@command()
def touch(args: Args):
    """
    Usage: touch [OPTION]... FILE...
    Update the access and modification times of each FILE to the current time.

    A FILE argument that does not exist is created empty, unless -c or -h
    is supplied.

    Mandatory arguments to long options are mandatory for short options too.
      -a                     change only the access time
      -c, --no-create        do not create any files
      -d, --date=STRING      parse STRING and use it instead of current time
      -m                     change only the modification time
      -r, --reference=FILE   use this file's times instead of current time
      -t STAMP               use [[CC]YY]MMDDhhmm[.ss] instead of current time
          --time=WORD        change the specified time:
                               WORD is access, atime, or use: equivalent to -a
                               WORD is modify or mtime: equivalent to -m
          --help        display this help and exit

    Note that the -d and -t options accept different time-date formats.
    """
    args.add_argument("files", nargs="+")
    g1 = args.add_mutually_exclusive_group()
    g1.add_argument("-a", action="store_true")
    g1.add_argument("-m", action="store_true")
    g1.add_argument("--time", choices=["access", "atime", "use", "modify", "mtime"])
    g2 = args.add_mutually_exclusive_group()
    g2.add_argument("-d", "--date", default=None)
    g2.add_argument("-r", "--reference", default=None)
    g2.add_argument("-t", default=None)
    args.add_argument("-c", "--no-create", action="store_true")

    argv = args.parse_args()

    now = datetime.now()

    if argv.reference:
        ref_item = vfs.find(argv.reference)
        if not ref_item:
            print(f"touch: cannot stat '{argv.reference}': No such file or directory")
            return
        now = ref_item.get_mod_date()

    elif argv.date:
        now = dateparser.parse(argv.date)
        if not now:
            print(f"touch: invalid date string '{argv.date}'")
            return

    elif argv.t:
        # [[CC]YY]MMDDhhmm[.ss]
        try:
            tstr = argv.t
            if "." in tstr:
                tmain, tsec = tstr.split(".")
            else:
                tmain, tsec = tstr, "00"
            tlen = len(tmain)
            if tlen == 12:  # CCYYMMDDhhmm
                dt = datetime.strptime(tmain, "%Y%m%d%H%M")
            elif tlen == 10:  # YYMMDDhhmm
                dt = datetime.strptime(tmain, "%y%m%d%H%M")
            else:
                raise ValueError
            dt = dt.replace(second=int(tsec))
            now = dt
        except ValueError:
            print(f"touch: invalid time stamp '{argv.t}'")
            return

    if argv.time:
        update_acc = argv.time in ("access", "atime", "use")
        update_mod = argv.time in ("modify", "mtime")
    else:
        update_acc = argv.a or not argv.m
        update_mod = argv.m or not argv.a

    for fpath in argv.files:
        item = vfs.find(fpath)
        if not item:
            if argv.no_create:
                continue
            item = vfs.create_file(fpath)
        if update_mod:
            item.set_mod_date(now)
        if update_acc:
            item.set_acc_date(now)
