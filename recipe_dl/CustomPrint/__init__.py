import sys, traceback
#import argparse

class ansi_colors:
    # Reset
    Reset='\033[0m'       # Text Reset

    # Regular Colors
    Black='\033[0;30m'        # Black
    Red='\033[0;31m'          # Red
    Green='\033[0;32m'        # Green
    Yellow='\033[0;33m'       # Yellow
    Blue='\033[0;34m'         # Blue
    Purple='\033[0;35m'       # Purple
    Cyan='\033[0;36m'         # Cyan
    White='\033[0;37m'        # White

    # Bold
    BBlack='\033[1;30m'       # Black
    BRed='\033[1;31m'         # Red
    BGreen='\033[1;32m'       # Green
    BYellow='\033[1;33m'      # Yellow
    BBlue='\033[1;34m'        # Blue
    BPurple='\033[1;35m'      # Purple
    BCyan='\033[1;36m'        # Cyan
    BWhite='\033[1;37m'       # White

    # Underline
    UBlack='\033[4;30m'       # Black
    URed='\033[4;31m'         # Red
    UGreen='\033[4;32m'       # Green
    UYellow='\033[4;33m'      # Yellow
    UBlue='\033[4;34m'        # Blue
    UPurple='\033[4;35m'      # Purple
    UCyan='\033[4;36m'        # Cyan
    UWhite='\033[4;37m'       # White

    # Background
    On_Black='\033[40m'       # Black
    On_Red='\033[41m'         # Red
    On_Green='\033[42m'       # Green
    On_Yellow='\033[43m'      # Yellow
    On_Blue='\033[44m'        # Blue
    On_Purple='\033[45m'      # Purple
    On_Cyan='\033[46m'        # Cyan
    On_White='\033[47m'       # White

    # High Intensity
    IBlack='\033[0;90m'       # Black
    IRed='\033[0;91m'         # Red
    IGreen='\033[0;92m'       # Green
    IYellow='\033[0;93m'      # Yellow
    IBlue='\033[0;94m'        # Blue
    IPurple='\033[0;95m'      # Purple
    ICyan='\033[0;96m'        # Cyan
    IWhite='\033[0;97m'       # White

    # Bold High Intensity
    BIBlack='\033[1;90m'      # Black
    BIRed='\033[1;91m'        # Red
    BIGreen='\033[1;92m'      # Green
    BIYellow='\033[1;93m'     # Yellow
    BIBlue='\033[1;94m'       # Blue
    BIPurple='\033[1;95m'     # Purple
    BICyan='\033[1;96m'       # Cyan
    BIWhite='\033[1;97m'      # White

    # High Intensity backgrounds
    On_IBlack='\033[0;100m'   # Black
    On_IRed='\033[0;101m'     # Red
    On_IGreen='\033[0;102m'   # Green
    On_IYellow='\033[0;103m'  # Yellow
    On_IBlue='\033[0;104m'    # Blue
    On_IPurple='\033[0;105m'  # Purple
    On_ICyan='\033[0;106m'    # Cyan
    On_IWhite='\033[0;107m'   # White

class bcolors:
    HEADER = '\033[95m'
    DEBUG = '\033[94m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ERROR = '\033[91m'
    RESET = ansi_colors.Reset
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def breadcrumbs(limit = None):
    def function_name(stack_lines):
        import re

        name = stack_lines.split('\n')[1].strip()
        name = re.sub('\([^\)]*\)', '', name)
        name = re.sub('[^=]*=', '', name).strip()

        return name

    breadcrumb=''
    seperator=' > '
    stack = traceback.format_stack()
    ignore = 3
    if len(stack) >= ignore:
        if limit is None:
            start = 0
        else:
            start = len(stack) - ignore - limit
        if start <= len(stack) - ignore:
            for trace_idx in range(start, len(stack) - ignore):
                function = function_name(stack[trace_idx])
                if trace_idx > start:
                    breadcrumb = breadcrumb + seperator
                breadcrumb = breadcrumb + function
    if breadcrumb.strip() != '':
        breadcrumb = ': ' + breadcrumb
    return breadcrumb


# Print to concole function is different between windows and *nix systems
try: # Windows
    from msvcrt import putwch

    def print_to_console(message):
        for c in message:
            putwch(c)
        # newline
        putwch('\r')
        putwch('\n')
except ImportError: # *nix
    import os

    fd = os.open('/dev/tty', os.O_WRONLY | os.O_NOCTTY)
    tty = os.fdopen(fd, 'w', 1)
    del fd
    def print_to_console(message, *, _file=tty):
        print(message, file=_file)
    del tty

def print_info(args, msg):
    if args is None or not args.quiet:
        print_to_console (msg)

def print_debug(args, msg):
    if args is None or args.debug:
        breadcrumb=breadcrumbs()
        print_info(args, f'[{bcolors.DEBUG} DEBUG{breadcrumb} {bcolors.RESET}] {msg}')

def print_warning(args, msg):
    if not args is None and not args.quiet:
        breadcrumb = ''
        if args.debug:
            breadcrumb=breadcrumbs()
    print_info(args, f'[{bcolors.WARNING} WARNING{breadcrumb} {bcolors.RESET}] {msg}')

def print_error(args, msg):
    breadcrumb = ''
    if args is None or args.debug:
        breadcrumb=breadcrumbs()
    else:
        breadcrumb=breadcrumbs(limit=1)
    print(f'[{bcolors.ERROR} ERROR{breadcrumb} {bcolors.RESET}] {msg}', file=sys.stderr)
