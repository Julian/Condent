from textwrap import dedent
from unittest import TestCase

import mock

from condent import Condenter


class TestCondenter(TestCase):
    def setUp(self):
        self.config = mock.Mock()
        self.condenter = Condenter(self.config)

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
        source = 'd = {"foo" : "bar", "baz" : "quux"}'
        self.assertRedents(source, source)

#     def test_it_does_not_split_tuple_assignment(self):
#         pass
# 
#     def test_it_does_not_split_string_literals(self):
#         pass
# 
#     def test_it_combines_args_that_fit_on_one_line(self):
#         pass
