import itertools
import re


__version__ = "0.2"


class Condenter(object):

    visitors = {"}" : "brace", "]" : "sequence", ")" : "sequence"}
    delimiters = {"{" : "}", "[" : "]", "(" : ")"}

    def __init__(self, config):
        self.config = config
        self.context = []
        self.stack = []

    def redent(self, lines):
        """
        Redent the given iterable of lines.

        Returns a generator which will yield redented lines.

        """

        for line in lines:
            for redented in self.visit(line):
                yield redented
        yield self.done()

    def visit(self, line):
        """
        Visit a line.

        Returns an iterable of redented lines that became available after
        visiting the given line.

        """

        for delimit in (self.find_left_delimiter, self.find_right_delimiter):
            result = delimit(line)
            if result is not None:
                return result
        else:
            return self.non_delimited(line)

    def done(self):
        """
        You ain't gots to go home, but you got to get the hell up outta here.

        The end of the input was reached. Who knows what is half-parsed, but
        it's gotta be shipped, now.

        """

        result = "".join(start + d for start, d in reversed(self.stack))
        return result + "".join(self.context)

    def find_left_delimiter(self, line):
        """
        Find a left delimiter if it exists in the line.

        """

        start, delimiter, end =  find_delimiters(self.delimiters, line)
        if delimiter is not None:
            return self.enter_container(start, delimiter, end)
        assert end is None, "Found no left delimiter but end is: " + repr(end)

    def find_right_delimiter(self, line):
        """
        Find a right delimiter if it exists in the line.

        """

        start, delimiter, end = find_delimiters(self.delimiters.values(), line)
        if delimiter is not None:
            return self.exit_container(start, delimiter, end)
        assert end is None, "Found no right delimiter but end is: " + repr(end)

    def enter_container(self, start, delimiter, end):
        """
        A left delimiter was encountered.

        """

        self.stack.append((start, delimiter))
        if end:
            return self.visit(end)

    def non_delimited(self, line):
        """
        A lite without a delimiter was encountered.

        If we're inside a container, it's a line with items to be buffered
        until the right delimiter is reached. Otherwise it's a non-container
        line, and is returned unchanged immediately.

        """

        if not self.stack:
            return [line]
        else:
            self.context.append(line)
            return []

    def exit_container(self, start, delimiter, end):
        """
        A right delimiter was encountered.

        It's time to redent and return the buffered lines.

        """

        self.context.append(start)

        visitor = getattr(self, "visit_" + self.visitors[delimiter])
        result = visitor(*self.stack.pop() + (self.context, delimiter))
        self.context = []
        return itertools.chain(result, self.visit(end))

    def visit_brace(self, *args):
        if is_dict(*args):
            return self.visit_dict(*args)
        else:
            return self.visit_sequence(*args)

    def visit_dict(self, start, left_delimiter, context, right_delimiter):
        cleaned = self.cleaned_dict_items(context)
        return self.container(start, left_delimiter, cleaned, right_delimiter)

    def visit_sequence(self, start, left_delimiter, context, right_delimiter):
        cleaned = self.cleaned_sequence_items(context)
        return self.container(start, left_delimiter, cleaned, right_delimiter)

    def container(self, start, left_delimiter, items, right_delimiter):
        items = list(items)
        line = self.single_line(start, left_delimiter, items, right_delimiter)
        if len(line) <= 79:
            return line
        return self.multi_line(start, left_delimiter, items, right_delimiter)

    def single_line(self, start, left_delimiter, items, right_delimiter):
        items = self.items(start, left_delimiter, items, right_delimiter)
        return "".join([start, left_delimiter, items, right_delimiter])

    def multi_line(self, start, left_delimiter, items, right_delimiter):
        indent = self.indent_for(start)
        items = self.multi_line_items(indent + "    ", items)
        end = indent + right_delimiter
        return "\n".join([start + left_delimiter, items, end])

    def indent_for(self, start):
        indent = len(start) - len(start.lstrip(" "))
        return indent * " "

    def split_items(self, items):
        for line in items:
            for item in re.split(",\n?", line.strip()):
                if item:
                    yield item

    def items(self, start, left_delimiter, items, right_delimiter):
        joined = ", ".join(items).rstrip(",")
        if is_tuple(start, left_delimiter) and len(items) == 1:
            joined += ","
        return joined

    def multi_line_items(self, indent, items):
        return ",\n".join(indent + item for item in items) + ","

    def cleaned_sequence_items(self, items):
        return (self.sequence_item(item) for item in self.split_items(items))

    def cleaned_dict_items(self, items, separator=":"):
        for item in self.split_items(items):
            key, value = re.split("\s*{}\s*".format(separator), item)
            yield self.dict_item(key, value)

    def dict_item(self, key, value, separator=":"):
        if self.config.symmetric_colons:
            separator = " " + separator
        return self.sequence_item("{0}{1} {2}".format(key, separator, value))

    def sequence_item(self, e, separator=","):
        return e.strip()


def find_delimiters(delimiters, line):
    """
    Partition the line using the given delimiters.

    Always returns a 3-tuple of the line up until the delimiter, the delimiter,
    and the line following the delimiter.

    """

    delimiter_re = "|".join(re.escape(d) for d in delimiters)
    result = re.split("({0})".format(delimiter_re), line)
    return tuple(result + [None] * (3 - len(result)))


def is_tuple(start, left_delimiter):
    _, __, callable = start.rpartition(" ")
    return not callable and left_delimiter == "("


def is_dict(start, left_delimiter, context, right_delimiter):
    return any(":" in line for line in context)
