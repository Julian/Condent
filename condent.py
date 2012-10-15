import itertools
import re


__version__ = "0.3"


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

        try:
            for line in lines:
                for redented in self.visit(line):
                    yield redented
        finally:
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
        A line without a delimiter was encountered.

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

    def visit_dict(self, start, left_delimiter, items, right_delimiter):
        separator = " : " if self.config.symmetric_colons else ": "
        return dict_literal(
            start,
            left_delimiter,
            _clean_dict_items(items, separator),
            right_delimiter,
            trailing_comma=self.config.trailing_comma,
        )

    def visit_sequence(self, start, left_delimiter, items, right_delimiter):
        return container_literal(
            start,
            left_delimiter,
            _clean_sequence_items(items),
            right_delimiter,
            self.config.trailing_comma,
        )


def dict_literal(
    start, left_delimiter, items, right_delimiter, trailing_comma=True,
):
    return container_literal(
        start, left_delimiter, items, right_delimiter, trailing_comma,
    )


def container_literal(
    start, left_delimiter, items, right_delimiter, trailing_comma=True,
):
    start = _clean_start(start)
    items = list(items)

    c = _single_line_container(start, left_delimiter, items, right_delimiter)
    if len(c) <= 79:
        return c

    return _multi_line_container(
        start, left_delimiter, items, right_delimiter, trailing_comma,
    )


def _clean_start(start):
    return re.sub("\s*=\s*$", " = ", start)


def _indent_for(start):
    indent = len(start) - len(start.lstrip(" "))
    return indent * " "


def _split_items(items):
    for line in items:
        for item in re.split(",\n?", line.strip()):
            if item:
                yield item


def _clean_dict_items(items, separator):
    for item in _split_items(items):
        key, value = re.split("\s*{}\s*".format(separator.strip()), item)
        yield _dict_item(key, value, separator)


def _dict_item(key, value, separator):
    return _sequence_item("{0}{1}{2}".format(key, separator, value))


def _clean_sequence_items(items):
    return (_sequence_item(item) for item in _split_items(items))


def _sequence_item(item):
    return item.strip()


def _single_line_container(start, left_delimiter, itms, right_delimiter):
    itms = items(start, left_delimiter, itms)
    return "".join([start, left_delimiter, itms, right_delimiter])


def _multi_line_container(
    start, left_delimiter, itms, right_delimiter, trailing_comma,
):
    indent = _indent_for(start)
    itms = items(start, left_delimiter, itms, trailing_comma)

    if len(itms) < 79:
        itms = indent + "    " + itms + ","

    return "{start}{left}\n{items}\n{indent}{right}".format(
        start=start,
        left=left_delimiter,
        items=itms,
        indent=indent,
        right=right_delimiter,
    )


def items(start, left_delimiter, items, trailing_comma=True):
    indent = "    " + _indent_for(start)
    trailing = "," if trailing_comma else ""
    joined = ", ".join(items)

    if is_tuple(start, left_delimiter) and len(items) == 1:
        joined += ","

    if len(indent + joined) > 79:
        joined = ",\n".join(indent + item for item in items) + trailing
    return joined


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
