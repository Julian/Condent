import re


__version__ = "0.1"


def single_line(left, items, right):
    """
    Format the given collection on a single line.

    """

    return "".join((left, " ".join(items), right))


def fits_on_one_line(left, items, right):
    """
    Check if the given collection would fit on a single line.

    """

    return len(single_line(left, items, right)) <= 79


def parts(source):
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

    start, _, body = source.partition("{")
    start, start_break, left = start.rpartition("\n")
    body, _, end = body.rpartition("}")
    right, end_break, end = end.partition("\n")
    left, right = left + "{", "}" + right
    return start + start_break, left, body.strip(), right, end_break + end


def fixed(item, symmetric_colons=True):
    """
    Fix an individual collection item, removing surrounding whitespace.

    """

    colon = " : " if symmetric_colons else ": "
    return re.sub("\s*:\s*", colon, item.strip())


def split_items(body):
    """
    Split the items of a collection to be one per line.

    """

    for line in body.splitlines():
        if line.count(",") > 1:
            for item in line.replace(",", ",\n").splitlines():
                yield item
        else:
            yield line


def fix_indentation(left, items, right):
    """
    Correct the indentation of the lines using the indent of the first line.

    """

    indent = len(left) - len(left.lstrip())

    yield left
    for item in items:
        yield (indent + 4) * " " + item.lstrip()
    yield indent * " " + right


def redent(source, symmetric_colons=True):
    """
    Redent the given source.

    """

    start, left, body, right, end = parts(source)
    items = [
        fixed(i, symmetric_colons=symmetric_colons) for i in split_items(body)
    ]

    if "\n" not in source.rstrip() or fits_on_one_line(left, items, right):
        return single_line(start + left, items, right + end)

    indented_items = "\n".join(fix_indentation(left, items, right))
    return "".join((start, indented_items, end))
