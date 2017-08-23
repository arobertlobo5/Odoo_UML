# -*- coding: utf-8 -*-


def tabs(size=0):
    str_tabs = ''
    while size > len(str_tabs) + 1:
        str_tabs += '\t'
    return str_tabs


class StringUtil(object):
    def __init__(self):
        self.buffer = str()
        self.stack = []

    def newline(self):
        return self.append('\n').append(tabs(len(self.stack)))

    def tab(self):
        return self.append('\t')

    def clear(self):
        self.buffer = str()
        return self

    def output(self):
        return self.buffer

    def restart(self):
        self.stack = []
        return self.clear()

    def append(self, string=''):
        self.buffer += string
        return self

    def push(self):
        self.stack.append(self.buffer)
        return self.clear()

    def pop(self):
        self.buffer = self.stack.pop() + self.buffer
        return self


class PlantUMLClassDiagram(StringUtil):
    def __init__(self):
        super(PlantUMLClassDiagram, self).__init__()

    def begin_uml(self):
        return self.append('@startuml').newline().push()

    def begin_package(self, name, stereotype=None, color=None, alias=None):
        tokens = ['package', '"%s"' % name]
        if alias is not None:
            tokens.extend(['as', alias])
        if stereotype is not None:
            tokens.extend(['<<%s>>' % stereotype])
        if color is not None:
            tokens.append(color)
        tokens.append('{')
        return self.append(' '.join(tokens)).push().newline()

    def add_dependency(self, name1='NoName1', name2='NoName2', alias1=None, alias2=None):
        tokens = [
            alias1 if alias1 is not None else name1,
            '..>',
            alias2 if alias2 is not None else name2
        ]
        return self.append(' '.join(tokens)).newline()

    def end_package(self):
        return self.pop().newline().append('}').newline()

    def end_uml(self):
        return self.pop().append('@enduml')
