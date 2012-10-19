from functools import wraps
from textwrap import dedent
from unittest import TestCase
import mock


def _cleanUpPatch(fn):
    @wraps(fn)
    def cleaned(self, *args, **kwargs):
        patch = fn(*args, **kwargs)
        self.addCleanup(patch.stop)
        return patch.start()
    return cleaned


class TestCase(TestCase):
    patch = _cleanUpPatch(mock.patch)
    patchDict = _cleanUpPatch(mock.patch.dict)
    patchObject = _cleanUpPatch(mock.patch.object)


import condent


class TestTokenize(TestCase):
    def setUp(self):
        self.left_delims = set("<")
        self.right_delims = set(">")

    def test_it_creates_non_delimiter_tokens(self):
        content = mock.Mock()
        parsed = iter([content])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.NonDelimiter(content=content),
            ]
        )

    def test_it_creates_left_delimiter_tokens(self):
        content = mock.Mock()
        parsed = iter(["<", content])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.LeftDelimiter(before="", delimiter="<"),
                condent.NonDelimiter(content=content),
            ]
        )

    def test_it_creates_left_delimiter_tokens_with_before(self):
        before, content = mock.Mock(), mock.Mock()
        parsed = iter([before, "<", content])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.LeftDelimiter(before=before, delimiter="<"),
                condent.NonDelimiter(content=content),
            ]
        )

    def test_it_creates_right_delimiter_tokens(self):
        one, another = mock.Mock(), mock.Mock()
        parsed = iter([one, ">", another])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.NonDelimiter(content=one),
                condent.RightDelimiter(delimiter=">"),
                condent.NonDelimiter(content=another),
            ]
        )


class TestIShouldKnowNotToUseNamedTupleByNow(TestCase):
    def test_tokens_of_different_classes_are_not_equal(self):
        # see http://bugs.python.org/issue16279
        self.assertFalse(
            condent.NonDelimiter(content=12) ==
            condent.RightDelimiter(delimiter=12)
        )
        self.assertNotEqual(
            condent.NonDelimiter(content=12),
            condent.RightDelimiter(delimiter=12),
        )


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
        self.builder = mock.Mock()
        self.config = mock.Mock()
        self.delimiters = {"<" : ">"}
        self.condenter = condent.Condenter(
            self.builder, self.config, self.delimiters,
        )

    def test_it_visits_tokens(self):
        tokens = [[mock.Mock()], [mock.Mock(), mock.Mock()]]
        output = iter([1, 2, 3])
        visit = self.patchObject(self.condenter, "visit", return_value=output)

        got = self.condenter.redent(tokens)

        self.assertEqual(list(got), [1, 2, 3])
        self.assertEqual(visit.call_count, 3)

    def test_it_visits_left_delimiters(self):
        enter = self.patchObject(self.condenter, "enter_container")
        self.condenter.visit("<")
        enter.assert_called_once_with("<")

    def test_it_visits_right_delimiters(self):
        exit = self.patchObject(self.condenter, "exit_container")
        self.condenter.visit(">")
        exit.assert_called_once_with(">")

    def test_it_visits_non_delimiters(self):
        visit = self.patchObject(self.condenter, "visit_non_delimiter")
        self.condenter.visit("foo bar baz")
        visit.assert_called_once_with("foo bar baz")

    def test_it_builds_a_literal_when_exiting_containers(self):
        start, left_delimiter, tokens = mock.Mock(), mock.Mock(), mock.Mock()
        stack = self.patchObject(self.condenter, "stack")
        stack.pop.return_value = start, left_delimiter, tokens

        right_delimiter = mock.Mock()
        output = self.condenter.exit_container(right_delimiter)

        self.assertEqual(output, self.builder.build.return_value)
        self.builder.build.assert_called_once_with(
            start, left_delimiter, tokens, right_delimiter,
        )

    def test_it_saves_non_delimited_lines_inside_containers(self):
        start, delim, tokens = mock.Mock(), mock.Mock(), []
        self.patchObject(self.condenter, "stack", [(start, delim, tokens)])

        token = mock.Mock()
        output = self.condenter.visit_non_delimiter(token)

        self.assertEqual(tokens, [token])
        self.assertIsNone(output)

    def test_it_yields_non_delimited_lines_outside_containers_unchanged(self):
        stack = self.patchObject(self.condenter, "stack", [])
        token = mock.Mock()
        output = self.condenter.visit_non_delimiter(token)
        self.assertEqual(list(output), [token])

    def test_it_can_fix_spaces_around_colons_non_symmetrically(self):
        pass

    def test_it_can_leave_off_trailing_commas(self):
        pass

    def test_it_combines_args_that_fit_on_one_line(self):
        pass

    def test_it_is_reusable(self):
        pass


class DictLiteral(TestCase):
    def setUp(self):
        patch = mock.patch.object(condent, "items")
        self.items = patch.start()
        self.addCleanup(patch.stop)


class TestSingleLineItems(TestCase):
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


class TestMultiLineItems(TestCase):
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
