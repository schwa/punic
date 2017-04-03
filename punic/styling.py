from __future__ import division, absolute_import, print_function

__all__ = ['styled', 'styled_print']

# noinspection PyUnresolvedReferences
from six.moves.html_parser import HTMLParser
from blessings import Terminal
import six
import sys

term = Terminal()

default_styles = {
    'err': term.red,

    'ref': term.yellow,
    'path': term.yellow,

    'rev': term.bold,
    'version': term.bold,

    'cmd': term.cyan + term.underline,  # 'sub': term.cyan,

    'echo': term.yellow,
}


class MyHTMLParser(HTMLParser):
    def __init__(self, style, styles = None):
        HTMLParser.__init__(self)

        self.s = ''
        self.style = style

        self.styles = styles if styles else default_styles
        self.style_stack = []

    # noinspection PyUnusedLocal
    def handle_starttag(self, tag, attrs):
        if tag in self.styles:
            self.style_stack.append(self.styles[tag])

    def handle_endtag(self, tag):
        if tag in self.styles:
            self.style_stack.pop()

    def handle_data(self, data):
        if self.style:
            self.apply()
        self.s += data

    def apply(self):
        self.s += term.normal
        for style in set(self.style_stack):
            self.s += style

from punic.config import config

def styled(s, style = None, styles = None):

    if style is None:
        style = config.color
    else:
        style = True

    parser = MyHTMLParser(style=style, styles = styles)
    parser.feed(s)
    return parser.s + (term.normal if style else '')



def styled_print(message, sep=' ', end='\n', file=sys.stdout, flush=False, style = None, styles = None, *args):
    args = [message] + list(args)
    s = sep.join([six.text_type(arg) for arg in args]) + end
    s = styled(s, style = style, styles = styles)

    file.write(s)
    if flush:
        file.flush()


# '<head>***</head> Checkout out <title>SwiftLogging</title> at "<version>v1.0.1</version>"')
#
# # instantiate the parser and fed it some HTML
