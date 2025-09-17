from datetime import datetime, timezone
import time

import dateparser

from console import Args, clear_console, command, console_size, has_input, input, pause, print, print_err, run, vfs


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
def cd(args: Args):
    """
    Usage: cd [directory]
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
        file = vfs.read_file(fname)
        if file:
            print(file)


@command("pause")
def cmd_pause(args: Args):
    print("Press any key to continue . . .")
    pause()


@command()
def clear(args: Args):
    clear_console()


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
        file = vfs.read_file(argv.file)
        if not file:
            return
        for line in file.strip().split("\n"):
            print(conver_date(line.strip()))
    elif argv.reference:
        file = vfs.cwd.follow_path(argv.reference)
        if not file:
            print(f"file not found: {argv.reference}")
            return
        date = file.get_mod_date()
        print(conver_date(date))
    else:
        print(conver_date(argv.date))
