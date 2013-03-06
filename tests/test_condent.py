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

    def test_it_creates_left_delimiter_tokens_with_before_after_rights(self):
        before, content = mock.Mock(), mock.Mock()
        parsed = iter([before, "<", content, ">", before.another, "<"])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.LeftDelimiter(before=before, delimiter="<"),
                condent.NonDelimiter(content=content),
                condent.RightDelimiter(delimiter=">"),
                condent.LeftDelimiter(before=before.another, delimiter="<"),
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

    def test_it_can_tokenize_repeated_right_delimiters(self):
        parsed = iter(["foo", "<", "bar, baz", "<", "quux", ">", ">"])

        tokens = condent.tokenize(parsed, self.left_delims, self.right_delims)

        self.assertEqual(
            list(tokens), [
                condent.LeftDelimiter(before="foo", delimiter="<"),
                condent.LeftDelimiter(before="bar, baz", delimiter="<"),
                condent.NonDelimiter(content="quux"),
                condent.RightDelimiter(delimiter=">"),
                condent.RightDelimiter(delimiter=">"),
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
        self.condenter = condent.Condenter(self.builder, self.config)

    def test_it_visits_tokens(self):
        tokens = [[mock.Mock()], [mock.Mock(), mock.Mock()]]
        output = iter([1, None, 3])
        visit = self.patchObject(self.condenter, "visit", side_effect=output)

        got = self.condenter.redent(tokens)

        self.assertEqual(list(got), [1, 3])
        self.assertEqual(
            visit.mock_calls,
            [mock.call(token) for token in sum(tokens, [])]
        )

    def test_it_empties_the_stack_when_done(self):
        tokens = [
            condent.LeftDelimiter(before="foo", delimiter="("),
            condent.NonDelimiter(content="bar"),
            condent.LeftDelimiter(before="", delimiter="("),
            condent.NonDelimiter(content="20"),
        ]

        got = self.condenter.redent([tokens])

        self.assertEqual("".join(got), "foo(bar(20")

    def test_it_empties_the_stack_when_partially_done(self):
        def side_effect(before, left, items, right):
            return before + left + "".join(items) + right
        self.builder.build.side_effect = side_effect

        tokens = [
            condent.LeftDelimiter(before="foo", delimiter="("),
            condent.NonDelimiter(content="bar"),
            condent.LeftDelimiter(before="", delimiter="("),
            condent.NonDelimiter(content="30"),
            condent.RightDelimiter(delimiter=")"),
        ]

        got = self.condenter.redent([tokens])

        self.assertEqual("".join(got), "foo(bar(30)")

    def test_it_reformats_the_items_as_it_goes(self):
        # TODO: e.g. foo(bar,baz(20 -> foo(bar, baz(20
        pass

    def test_it_visits_tokens_by_class(self):
        token = mock.Mock()
        visit = "visit_{0.__class__.__name__}".format(token)
        visitor = self.patchObject(self.condenter, visit, create=True)

        output = self.condenter.visit(token)

        self.assertEqual(output, visitor.return_value)

    def test_it_builds_a_literal_when_exiting_containers(self):
        left_token, items = mock.Mock(), [mock.Mock(), mock.Mock()]
        self.condenter.stack.append((left_token, items))

        right_token = mock.Mock()
        output = self.condenter.visit_RightDelimiter(right_token)

        self.assertEqual(output, self.builder.build.return_value)
        self.builder.build.assert_called_once_with(
            left_token.before,
            left_token.delimiter,
            [item.content for item in items],
            right_token.delimiter,
        )

    def test_it_descends_into_the_stack_for_left_delimiters(self):
        left_token = mock.Mock()
        output = self.condenter.visit_LeftDelimiter(left_token)
        self.assertEqual(self.condenter.stack, [(left_token, [])])
        self.assertIsNone(output)

    def test_it_saves_non_delimited_lines_inside_containers(self):
        left_token, items = mock.Mock(), []
        self.condenter.stack.append((left_token, items))

        token = mock.Mock()
        output = self.condenter.visit_NonDelimiter(token)

        self.assertEqual(items, [token])
        self.assertIsNone(output)

    def test_it_yields_non_delimited_lines_outside_containers_unchanged(self):
        token = mock.Mock()
        output = self.condenter.visit_NonDelimiter(token)
        self.assertEqual(output, token.content)

    def test_it_can_fix_spaces_around_colons_non_symmetrically(self):
        pass

    def test_it_can_leave_off_trailing_commas(self):
        pass

    def test_it_combines_args_that_fit_on_one_line(self):
        pass

    def test_it_is_reusable(self):
        pass


class TestLiteralBuilder(TestCase):
    def setUp(self):
        self.config = mock.Mock()

    def test_it_has_default_builders_for_delimiters(self):
        b = condent.LiteralBuilder(self.config)
        self.assertEqual(
            b.builders, {"{" : "brace", "[" : "sequence", "(" : "sequence"},
        )
    def test_it_builds_things(self):
        self.patchObject(condent.LiteralBuilder, "build_angle", create=True)
        args = before, L, items, R = mock.Mock(), "<", mock.Mock(), mock.Mock()

        builder = condent.LiteralBuilder(self.config, {"<" : "angle"})
        builder.build(*args)

        builder.build_angle.assert_called_once_with(*args)


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
