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

#     def test_it_does_not_split_tuple_assignment(self):
#         pass
# 
#     def test_it_does_not_split_string_literals(self):
#         pass
# 
#     def test_multi_line_function_call(self):
#         source = "d = foo(\n1, 2, 3\n)"
#         self.assertEqual(redent(source), "d = foo(\n    1,\n    2,\n    3,\n)")
# 
#     def test_it_splits_up_containers_exceeding_line_limit(self):
#         source = " " * 72 + "d = [1, 2, 3, 4]"
#         self.assertGreater(len(redent(source).splitlines()), 1)
# 
#     def test_if_it_is_confused_it_does_nothing(self):
#         source = "awefoijaowf;oiwfe[qpk1240i-"
#         self.assertEqual(redent(source), source)
# 
#     def test_it_combines_args_that_fit_on_one_line(self):
#         pass
