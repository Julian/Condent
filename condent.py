from collections import namedtuple
import itertools
import re


__version__ = "0.4dev"


DELIMITERS = {"{" : "}", "[" : "]", "(" : ")"}


class Condenter(object):
    def __init__(self, builder, config):
        self.builder = builder
        self.config = config
        self.stack = []

    def redent(self, tokened_lines):
        """
        Redent the given iterable of tokenized lines.

        Returns a generator which will yield redented lines.

        """

        for line in tokened_lines:
            for token in line:
                output = self.visit(token)
                if output is not None:
                    yield output

        if self.stack:
            yield self.reassemble()

    def reassemble(self):
        unprocessed = []

        for delimiter, items in reversed(self.stack):
            unprocessed.append(
                "".join([
                    delimiter.before,
                    delimiter.delimiter,
                    "".join(item.content for item in items)
                    ])
            )

        return "".join(reversed(unprocessed))

    def visit(self, token):
        """
        Visit a token.

        Returns an iterable of redented lines that became available after
        visiting the given line.

        """

        return getattr(self, "visit_" + token.__class__.__name__)(token)

    def visit_LeftDelimiter(self, token):
        """
        A left delimiter was encountered.

        """

        self.stack.append((token, []))

    def visit_NonDelimiter(self, token):
        """
        A token that is not a delimiter was encountered.

        If we're inside a container, it's a line with items to be buffered
        until the right delimiter is reached. Otherwise it's a non-container
        line, and is returned unchanged immediately.

        """

        if not self.stack:
            return token.content

        item_tokens = self.stack[-1][1]
        item_tokens.append(token)

    def visit_RightDelimiter(self, right_token):
        """
        A right delimiter was encountered.

        It's time to redent and return the buffered lines.

        """

        left_token, item_tokens = self.stack.pop()
        redented = self.builder.build(
            left_token.before,
            left_token.delimiter,
            [item.content for item in item_tokens],
            right_token.delimiter,
        )
        return self.visit_NonDelimiter(NonDelimiter(content=redented))


class LiteralBuilder(object):
    def __init__(self, config, builders=None):
        if builders is None:
            builders = {"{" : "brace", "[" : "sequence", "(" : "sequence"}

        self.builders = builders
        self.config = config

    def build(self, before, left_delimiter, items, right_delimiter):
        builder = getattr(self, "build_" + self.builders[left_delimiter])
        return builder(before, left_delimiter, items, right_delimiter)

    def build_brace(self, *args):
        if is_dict(*args):
            return self.build_dict(*args)
        else:
            return self.build_sequence(*args)

    def build_dict(self, before, left_delimiter, items, right_delimiter):
        separator = " : " if self.config.symmetric_colons else ": "
        return dict_literal(
            before,
            left_delimiter,
            _clean_dict_items(items, separator),
            right_delimiter,
            trailing_comma=self.config.trailing_comma,
        )

    def build_sequence(self, before, left_delimiter, items, right_delimiter):
        return container_literal(
            before,
            left_delimiter,
            _clean_sequence_items(items),
            right_delimiter,
            self.config.trailing_comma,
        )


def dict_literal(
    before, left_delimiter, items, right_delimiter, trailing_comma=True,
):
    return container_literal(
        before, left_delimiter, items, right_delimiter, trailing_comma,
    )


def container_literal(
    before, left_delimiter, items, right_delimiter, trailing_comma=True,
):
    before = _clean_before(before)
    items = list(items)

    c = _single_line_container(before, left_delimiter, items, right_delimiter)
    if len(c) <= 79:
        return c

    return _multi_line_container(
        before, left_delimiter, items, right_delimiter, trailing_comma,
    )


def _clean_before(before):
    return re.sub("\s*=\s*$", " = ", before)


def _indent_for(before):
    indent = len(before) - len(before.lstrip(" "))
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


def _single_line_container(before, left_delimiter, itms, right_delimiter):
    itms = items(before, left_delimiter, itms)
    return "".join([before, left_delimiter, itms, right_delimiter])


def _multi_line_container(
    before, left_delimiter, itms, right_delimiter, trailing_comma,
):
    indent = _indent_for(before)
    itms = items(before, left_delimiter, itms, trailing_comma)

    if len(itms) < 79:
        itms = indent + "    " + itms + ","

    return "{before}{left}\n{items}\n{indent}{right}".format(
        before=before,
        left=left_delimiter,
        items=itms,
        indent=indent,
        right=right_delimiter,
    )


def items(before, left_delimiter, items, trailing_comma=True):
    indent = "    " + _indent_for(before)
    joined = ", ".join(items)

    if is_tuple(before, left_delimiter) and len(items) == 1:
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

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        fields = ("{0}={1!r}".format(f, getattr(self, f)) for f in self.fields)
        return "<{0.__class__.__name__} {1}>".format(self, " ".join(fields))

    @property
    def _content(self):
        return [(k, getattr(self, k)) for k in self.fields]


class NonDelimiter(Token): fields = ["content"]
class LeftDelimiter(Token): fields = ["before", "delimiter"]
class RightDelimiter(Token): fields = ["delimiter"]


def tokenize(parsed, left_delimiters, right_delimiters):
    last = ""

    for thing in parsed:
        if thing in left_delimiters:
            before, last = last, ""
            yield LeftDelimiter(before=before, delimiter=thing)
        elif thing in right_delimiters:
            if last:
                yield NonDelimiter(content=last)
                last = ""
            yield RightDelimiter(delimiter=thing)
            last = ""
        else:
            last = thing

    if last:
        yield NonDelimiter(content=last)


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


def is_tuple(before, left_delimiter):
    _, __, callable = before.rpartition(" ")
    return not callable and left_delimiter == "("


def is_dict(before, left_delimiter, context, right_delimiter):
    return any(":" in line for line in context)
