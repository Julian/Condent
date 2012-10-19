from collections import namedtuple
import itertools
import re


__version__ = "0.3"


DELIMITERS = {"{" : "}", "[" : "]", "(" : ")"}


class Condenter(object):

    visitors = {"}" : "brace", "]" : "sequence", ")" : "sequence"}

    def __init__(self, builder, config, delimiters=DELIMITERS):
        self.builder = builder
        self.config = config
        self.delimiters = delimiters
        self.stack = []

    def redent(self, tokened_lines):
        """
        Redent the given iterable of tokenized lines.

        Returns a generator which will yield redented lines.

        """

        for line in tokened_lines:
            for token in line:
                self.visit(token)
        return [1, 2, 3]

    def visit(self, token):
        """
        Visit a token.

        Returns an iterable of redented lines that became available after
        visiting the given line.

        """

        if token in self.delimiters:
            self.enter_container(token)
        elif token in self.delimiters.values():
            self.exit_container(token)
        else:
            self.visit_non_delimiter(token)

    def enter_container(self, start, delimiter, end):
        """
        A left delimiter was encountered.

        """

        self.stack.append((start, delimiter))
        if end:
            return self.visit(end)

    def visit_non_delimiter(self, token):
        """
        A token that is not a delimiter was encountered.

        If we're inside a container, it's a line with items to be buffered
        until the right delimiter is reached. Otherwise it's a non-container
        line, and is returned unchanged immediately.

        """

        if not self.stack:
            return [token]

        item_tokens = self.stack[-1][2]
        item_tokens.append(token)

    def exit_container(self, delimiter):
        """
        A right delimiter was encountered.

        It's time to redent and return the buffered lines.

        """

        start, left_delimiter, item_toks = self.stack.pop()
        return self.builder.build(start, left_delimiter, item_toks, delimiter)

    def done(self):
        """
        You ain't gots to go home, but you got to get the hell up outta here.

        The end of the input was reached. Who knows what is half-parsed, but
        it's gotta be shipped, now.

        """

        result = "".join(start + d for start, d in reversed(self.stack))
        return result + "".join(self.context)


class LiteralBuilder(object):
    def build(self, start, left_delimiter, item_tokens, right_delimiter):
        pass

    def build_brace(self, *args):
        if is_dict(*args):
            return self.build_dict(*args)
        else:
            return self.build_sequence(*args)

    def build_dict(self, start, left_delimiter, items, right_delimiter):
        separator = " : " if self.config.symmetric_colons else ": "
        return dict_literal(
            start,
            left_delimiter,
            _clean_dict_items(items, separator),
            right_delimiter,
            trailing_comma=self.config.trailing_comma,
        )

    def build_sequence(self, start, left_delimiter, items, right_delimiter):
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
    joined = ", ".join(items)

    if is_tuple(start, left_delimiter) and len(items) == 1:
        joined += ","

    if len(indent + joined) > 79:
        trailing = "," if trailing_comma else ""
        return ",\n".join(indent + item for item in items) + trailing
    return joined


class Token(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            if k not in self.fields:
                raise TypeError(k)
            setattr(self, k, v)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._content == other._content

    @property
    def _content(self):
        return [(k, getattr(self, k)) for k in self.fields]


class NonDelimiter(Token): fields = ["content"]
class LeftDelimiter(Token): fields = ["before", "delimiter"]
class RightDelimiter(Token): fields = ["delimiter"]


def tokenize(parsed, left_delimiters, right_delimiters):
    first = next(parsed)
    second = next(parsed, None)

    if second is not None and second in left_delimiters:
        yield LeftDelimiter(before=first, delimiter=second)
        first = second = []
    else:
        first, second = [first], [second] if second is not None else []

    for thing in itertools.chain(first, second, parsed):
        if thing in left_delimiters:
            yield LeftDelimiter(before="", delimiter=thing)
        elif thing in right_delimiters:
            yield RightDelimiter(delimiter=thing)
        else:
            yield NonDelimiter(content=thing)


class ParsesDelimiters(object):
    def __init__(self, delimiters):
        self.buffer = []
        self.delimiters = delimiters
        self.in_string = False

    def _parse(self, line):
        for c in line:
            if self.in_string:
                yield self.see_in_string(c)
            else:
                for result in self.see(c):
                    yield result
        yield self.empty_buffer()

    def parse(self, line):
        return (result for result in self._parse(line) if result is not None)

    def see(self, c):
        if c in self.delimiters:
            yield self.empty_buffer()
            yield c
        else:
            self.buffer.append(c)

            if c in """"'""":
                self.in_string = True

    def see_in_string(self, c):
        if c in """"'""":
            self.in_string = False
        self.buffer.append(c)

    def empty_buffer(self):
        if self.buffer:
            try:
                return "".join(self.buffer)
            finally:
                self.buffer = []


def is_tuple(start, left_delimiter):
    _, __, callable = start.rpartition(" ")
    return not callable and left_delimiter == "("


def is_dict(start, left_delimiter, context, right_delimiter):
    return any(":" in line for line in context)
