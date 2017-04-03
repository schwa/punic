from __future__ import division, absolute_import, print_function

__all__ = ['HTMLFormatter', 'HTMLStripperFormatter']

import punic.styling
import six

# TODO: Convert < and > to &lt; and &gt;

class HTMLFormatter(object):

    def __init__(self):
        self.color = True

    def format(self, record):
        message = record.msg
        if not isinstance(message, six.string_types):
            message = repr(message)
        else:
            message = punic.styling.styled(message, self.color)
        return message


class HTMLStripperFormatter(object):
    def __init__(self, formatter=None):
        self.formatter = formatter

    def format(self, record):
        if self.formatter:
            message = self.formatter.format(record)
        else:
            message = record.msg
        if not isinstance(message, six.string_types):
            message = repr(message)
        else:
            message = punic.styling.styled(message, False)
        return message
