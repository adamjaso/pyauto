import os
import sys
import difflib
from six.moves import input as raw_input
from collections import OrderedDict

try:
    from colorama import Fore, Back, Style, init

    init()
    colored_output = True
except ImportError:
    # fallback so the imported classes always exist
    class ColorFallback(object):
        def __getattr__(self, name):
                return ''

    Fore = Back = Style = init = ColorFallback()
    colored_output = False


class Diff(object):
    def __init__(self, name, fromvalue, tovalue):
        self.name = name
        self.fromvalue_lines = fromvalue.split('\n')
        self.tovalue = tovalue
        self.tovalue_lines = tovalue.split('\n')
        fromdesc = '{0} [current]'.format(name)
        todesc = '{0} [proposed]'.format(name)
        diffgen = difflib.unified_diff(self.fromvalue_lines,
                                       self.tovalue_lines,
                                       fromdesc, todesc)
        self.lines = []
        self.colored_lines = []
        for line in diffgen:
            self.lines.append(line)
            if line.startswith('+'):
                self.colored_lines.append(Fore.GREEN + line + Fore.RESET)
            elif line.startswith('-'):
                self.colored_lines.append(Fore.RED + line + Fore.RESET)
            elif line.startswith('^'):
                self.colored_lines.append(Fore.BLUE + line + Fore.RESET)
            else:
                self.colored_lines.append(line)

    def has_diff(self):
        return len(self.colored_lines)

    def to_colored_string(self):
        return os.linesep.join(self.colored_lines)

    def to_string(self):
        return os.linesep.join(self.lines)

    def confirm(self):
        if not self.has_diff():
            return 'none'
        res = raw_input('({0}) Are you sure you want to make this '
                        'change (y/N)? '.format(self.name))
        if res.lower() in ['y', 'yes']:
            return 'accepted'
        return 'declined'


class DictDiff(object):
    def __init__(self, fromvalues, tovalues):
        for k in fromvalues:
            if k not in tovalues:
                tovalues[k] = ''
        for k in tovalues:
            if k not in fromvalues:
                fromvalues[k] = ''
        keys = set(fromvalues.keys()).union(set(tovalues.keys()))
        self.diffs = [Diff(key, fromvalues[key], tovalues[key])
                      for key in sorted(keys)]

    def show_and_confirm(self, plain=False):
        for diff in self.diffs:
            if plain:
                message = diff.to_string()
            else:
                message = diff.to_colored_string()
            sys.stdout.write(message + os.linesep)

        approved = OrderedDict()
        for diff in self.diffs:
            confirm = diff.confirm()
            if 'accepted' == confirm:
                approved[diff.name] = diff.tovalue
                print('Approved  "{0}"'.format(diff.name))
            elif 'declined' == confirm:
                print('Declined  "{0}"'.format(diff.name))
            elif 'none' == confirm:
                print('No Change "{0}"'.format(diff.name))
            else:
                raise Exception('Unknown response: {0}'.format(confirm))

        return approved
