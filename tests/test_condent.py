from functools import wraps
from textwrap import dedent
from unittest import TestCase

import mock

import condent


def _cleanUpPatch(fn):
    @wraps(fn)
    def cleaned(self, *args, **kwargs):
        patch = fn(*args, **kwargs)
        self.addCleanup(patch.stop)
        return patch.start()
    return cleaned


class PatchMixin(object):
    patch = _cleanUpPatch(mock.patch)
    patchDict = _cleanUpPatch(mock.patch.dict)
    patchObject = _cleanUpPatch(mock.patch.object)


class DictLiteral(TestCase):
    def setUp(self):
        patch = mock.patch.object(condent, "items")
        self.items = patch.start()
        self.addCleanup(patch.stop)


class TestSingleLineItems(TestCase, PatchMixin):
    def setUp(self):
        self.start = ""
        self.left_delimiter = mock.Mock()
        self.is_tuple = self.patchObject(
            condent, "is_tuple", return_value=False,
        )

    def test_it_can_assemble_a_single_line_of_items(self):
        items = ["foo", "bar", "baz", "quux", "spam"]
        self.is_tuple.return_value = False

        self.assertEqual(
            condent.items(self.start, self.left_delimiter, items),
            "foo, bar, baz, quux, spam",
        )

    def test_it_adds_a_comma_if_container_is_a_single_item_tuple(self):
        items = ["foo"]
        self.is_tuple.return_value = True

        self.assertEqual(
            condent.items(self.start, self.left_delimiter, items), "foo,",
        )
        self.is_tuple.assert_called_once_with(self.start, self.left_delimiter)

    def test_it_does_not_add_a_comma_if_container_is_an_empty_tuple(self):
        items = []
        self.is_tuple.return_value = True

        self.assertEqual(
            condent.items(self.start, self.left_delimiter, items), "",
        )
        self.is_tuple.assert_called_once_with(self.start, self.left_delimiter)

    def test_it_does_not_add_a_comma_if_container_is_a_multi_item_tuple(self):
        items = ["foo", "bar", "baz", "quux", "spam"]
        self.is_tuple.return_value = True

        self.assertEqual(
            condent.items(self.start, self.left_delimiter, items),
            "foo, bar, baz, quux, spam",
        )
        self.is_tuple.assert_called_once_with(self.start, self.left_delimiter)

    def test_even_if_the_line_is_really_long(self):
        pass


class TestMultiLineItems(TestCase, PatchMixin):
    def setUp(self):
        self.items = ["a" * 39] * 2
        self.start = ""
        self.left_delimiter = mock.Mock()

    def test_it_splits_items_onto_multiple_lines_if_they_are_long(self):
        self.assertEqual(
            condent.items(self.start, self.left_delimiter, self.items),
            "    " + ",\n    ".join(self.items) + ",",
        )

    def test_it_splits_items_onto_multiple_lines_if_they_are_indented(self):
        self.start = " " * 72 + "foo = "
        items = ["1", "2", "3"]

        self.assertEqual(
            condent.items(self.start, self.left_delimiter, items),
            " " * 76 + (",\n" + " " * 76).join(items) + ",",
        )

    def test_it_indents_more_if_start_is_indented(self):
        self.start = " " * 7 + "foo_bar = "

        indent = " " * 7 + " " * 4
        self.assertEqual(
            condent.items(self.start, self.left_delimiter, self.items),
            indent + (",\n" + indent).join(self.items) + ",",
        )

    def test_it_can_leave_off_the_trailing_comma(self):
        items = condent.items(
            self.start, self.left_delimiter, self.items, trailing_comma=False,
        )
        self.assertEqual(items, "    " + ",\n    ".join(self.items))


class TestParsesDelimiters(TestCase):
    def setUp(self):
        self.parser = condent.ParsesDelimiters("[]")

    def test_it_splits_a_line_with_a_delimeter(self):
        source = "foo = [1"
        self.assertEqual(
            list(self.parser.parse(source)),
            ["foo = ", "[", "1"],
        )

    def test_it_splits_a_line_with_an_open_and_close_delimeter(self):
        source = "foo = [1, 2]"
        self.assertEqual(
            list(self.parser.parse(source)),
            ["foo = ", "[", "1, 2", "]"],
        )

    def test_it_splits_a_line_with_multiple_delimiters(self):
        source = "foo = [1, [2]]"
        self.assertEqual(
            list(self.parser.parse(source)),
            ["foo = ", "[", "1, ", "[", "2", "]", "]"],
        )

    def test_it_does_not_split_delimiters_in_strings(self):
        source = "foo = [1, '[2]]', \"[[3]]\"]"
        self.assertEqual(
            list(self.parser.parse(source)),
            ["foo = ", "[", "1, '[2]]', \"[[3]]\"", "]"],
        )

    def test_it_does_not_split_multi_line_strings(self):
        source = 'foo = ["""[1]""", \'\'\'[4]\'\'\']'
        self.assertEqual(
            list(self.parser.parse(source)),
            ["foo = ", "[", '"""[1]""", \'\'\'[4]\'\'\'', "]"],
        )



class TestCondenter(TestCase):
    def setUp(self):
        self.config = mock.Mock()
        self.condenter = condent.Condenter(self.config)

    def assertRedents(self, input, output):
        lines = dedent(input).splitlines(True)
        redented = self.condenter.redent(lines)
        self.assertEqual("".join(redented), dedent(output))

    def test_found_left_delimiter(self):
        with mock.patch.dict(self.condenter.delimiters, **{"|" : "|"}):
            line = "start|end"

            with mock.patch.object(self.condenter, "enter_container") as enter:
                self.condenter.find_left_delimiter(line)
                enter.assert_called_once_with("start", "|", "end")

    def test_did_not_find_left_delimiter(self):
        with mock.patch.dict(self.condenter.delimiters):
            line = "start|end"

            with mock.patch.object(self.condenter, "enter_container") as enter:
                self.condenter.find_left_delimiter(line)
                self.assertFalse(enter.called)

    def test_it_can_fix_spaces_around_colons_non_symmetrically(self):
        self.condenter.config.symmetric_colons = False
        source = 'd = {"foo": "bar"}'
        self.assertRedents(source, source)

    def test_it_can_leave_off_trailing_commas(self):
        self.condenter.config.trailing_comma = False
        source = """
                                                            d = {
                                                                "foo" : "bar",
                                                                "baz" : "quux"
                                                            }
        """.splitlines(True)
        self.assertEqual(
            "".join(self.condenter.redent(source)), "".join(source)
        )

    def test_it_can_leave_off_trailing_commas_in_single_lines(self):
        self.condenter.config.trailing_comma = False
        source = 'd = {"foo" : "bar", "baz" : "quux"}'
        self.assertRedents(source, source)

#     def test_it_does_not_split_tuple_assignment(self):
#         pass
# 
#     def test_it_combines_args_that_fit_on_one_line(self):
#         pass
