
class ConsoleWriter(object):
    def __init__(self):
        self.indent = 0
        self._debug = True

    def error(self, text):
        print ' '*self.indent + 'Error: ' + text

    def debug(self, text):
        if self._debug:
            print ' '*self.indent + 'Debug: ' + text

    def output(self, text, add_indent=False):
        print ' '*self.indent + text
        if add_indent:
            self.indent += 2

    def reset_indent(self):
        self.indent -= 2
