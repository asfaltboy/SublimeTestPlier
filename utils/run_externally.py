""" Run simple applescript to launch iTerm2 with given command """
import os
import shlex
import subprocess
import sys


def main():
    os.environ['TEST_CMD'] = os.environ.get('TEST_CMD', ' '.join(sys.argv[1:]))
    CUR_DIR = os.path.abspath(os.path.dirname(__file__))
    applescript = os.path.join(CUR_DIR, 'launch_in_iterm.applescript')
    cmd = 'osascript "%s"' % applescript
    print(cmd)
    full_cmd = shlex.split(cmd)
    print(full_cmd)
    subprocess.Popen(full_cmd).wait()


if __name__ == '__main__':
    main()
