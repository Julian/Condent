import re


__version__ = "0.1"


def find_delimiters(source):
    """
    Discover what kind of container literal the source contains.

    """

    for left, right in ["{}", "[]", "()"]:
        if left in source and right in source:
            return left, right
    raise ValueError("Can't find the delimiters!")


def single_line(left, items, right, trailing_comma=False):
    """
    Format the given collection on a single line.

    """

    items = " ".join(items)
    if not trailing_comma:
        items = items.rstrip(",")
    return "".join((left, items, right))


def fits_on_one_line(left, items, right):
    """
    Check if the given collection would fit on a single line.

    """

    return len(single_line(left, items, right)) <= 79


def parts(source, delimiters="{}"):
    """
    Split a chunk of source into parts.

    The parts are:
        * the lines before the line containing the beginning of the literal
        * the (entire) line containing the beginning of the literal
        * the (possibly partial first line and succeeding) lines containing the
          items of the literal
        * the (entire) line containing the end of the literal
        * the lines after the line containing the end of the literal

    They are returned as a tuple in that order.

    """

    start, _, body = source.partition(delimiters[0])
    start, start_break, left = start.rpartition("\n")
    body, _, end = body.rpartition(delimiters[1])
    right, end_break, end = end.partition("\n")
    left, right = left + delimiters[0], delimiters[1] + right
    return start + start_break, left, body.strip(), right, end_break + end


def fixed(item, symmetric_colons=True, trailing_comma=True):
    """
    Fix an individual collection item, removing surrounding whitespace.

    """

    colon = " : " if symmetric_colons else ": "
    item = re.sub("\s*:\s*", colon, item.strip())

    if trailing_comma:
        item = item.rstrip(",") + ","

    return item


def split_items(body):
    """
    Split the items of a collection to be one per line.

    """

    for item in re.split(",\n?", body):
        if item:
            yield item


def fix_indentation(left, items, right):
    """
    Correct the indentation of the lines using the indent of the first line.

    """

    indent = len(left) - len(left.lstrip())

    yield left
    for item in items:
        yield (indent + 4) * " " + item.lstrip()
    yield indent * " " + right


def redent(
    source, symmetric_colons=True, trailing_comma=True,
    single_line_trailing_comma=False,
):
    """
    Redent the given source.

    """

    try:
        delimiters = find_delimiters(source)
    except ValueError:
        return source

    start, left, body, right, end = parts(source, delimiters=delimiters)
    items = [
        fixed(i, symmetric_colons, trailing_comma) for i in split_items(body)
    ]

    if fits_on_one_line(left, items, right):
        comma = single_line_trailing_comma
        line = single_line(left, items, right, trailing_comma=comma)
        return start + line + end

    indented_items = "\n".join(fix_indentation(left, items, right))
    return "".join((start, indented_items, end))
