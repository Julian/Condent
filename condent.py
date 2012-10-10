import re


__version__ = "0.1"


def single_line(left, items, right):
    return "".join((left, "".join(items), right))


def parts(source):
    start, _, body = source.partition("{")
    start, start_break, left = start.rpartition("\n")
    body, _, end = body.rpartition("}")
    right, end_break, end = end.partition("\n")
    left, right = left + "{", "}" + right
    return start + start_break, left, body.strip(), right, end_break + end


def fix_item(item):
    return re.sub("\s*:\s*", " : ", item)


def split_items(body):
    for line in body.splitlines():
        if line.count(",") > 1:
            for item in line.replace(",", ",\n").splitlines():
                yield item
        else:
            yield line


def fix_indentation(left, items, right):
    indent = len(left) - len(left.lstrip())

    yield left
    for item in items:
        yield (indent + 4) * " " + item.lstrip()
    yield indent * " " + right


def redent(source):
    start, left, body, right, end = parts(source)
    items = (fix_item(item) for item in split_items(body))

    if "\n" not in source.rstrip():
        return single_line(start + left, items, right + end)

    indented_items = "\n".join(fix_indentation(left, items, right))
    return "".join((start, indented_items, end))
