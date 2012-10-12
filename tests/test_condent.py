from textwrap import dedent
from unittest import TestCase

import mock

from condent import Condenter


class TestCondenter(TestCase):
    def setUp(self):
        self.condenter = Condenter()

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
        self.condenter.symmetric_colon = False
        source = 'd = {"foo": "bar"}'
        self.assertRedents(source, source)



# class TestDictRedent(TestCase):
#     def setUp(self):
#         patch = mock.patch("condent.fits_on_one_line", return_value=False)
#         patch.start()
#         self.addCleanup(patch.stop)
# 
#     def test_it_splits_up_multiple_items_on_a_line(self):
#         source = """
# d = {
#     "foo" : "bar", "baz" : "quux",
# }
# """
# 
#         self.assertEqual(redent(source), """
# d = {
#     "foo" : "bar",
#     "baz" : "quux",
# }
# """)
# 
#     def test_it_does_not_split_tuple_assignment(self):
#         pass
# 
#     def test_it_does_not_split_string_literals(self):
#         pass
# 
#     def test_it_reindents_items(self):
#         source = """
# d = {
# "foo" : "bar",
#         "baz" : "quux",
# }
# """
# 
#         self.assertEqual(redent(source), """
# d = {
#     "foo" : "bar",
#     "baz" : "quux",
# }
# """)
# 
#     def test_it_reindents_more_if_first_line_is_indented(self):
#         source = """
#         d = {
# "foo" : "bar",
#         "baz" : "quux",
# }
# """
# 
#         self.assertEqual(redent(source), """
#         d = {
#             "foo" : "bar",
#             "baz" : "quux",
#         }
# """)
# 
#     def test_it_puts_multiple_line_dict_braces_on_their_own_lines(self):
#         source = 'd = {   "foo" : "bar"\n  }'
#         self.assertEqual(redent(source), 'd = {\n    "foo" : "bar",\n}')
# 
#     def test_it_fixes_spaces_around_colons(self):
#         source = 'd = {"foo": "bar"\n}'
#         self.assertEqual(redent(source), 'd = {\n    "foo" : "bar",\n}')
# 
#     def test_it_leaves_a_trailing_comma(self):
#         source = """
# {
#     "foo" : "bar",
#     "baz" : "quux"
# }
# """
#         self.assertEqual(redent(source), """
# {
#     "foo" : "bar",
#     "baz" : "quux",
# }
# """)
# 
# 
# class TestOtherDelimiters(TestCase):
#     def setUp(self):
#         patch = mock.patch("condent.fits_on_one_line", return_value=False)
#         patch.start()
#         self.addCleanup(patch.stop)
# 
#     def test_multi_line_function_call(self):
#         source = "d = foo(\n1, 2, 3\n)"
#         self.assertEqual(redent(source), "d = foo(\n    1,\n    2,\n    3,\n)")
# 
#     def test_multi_line_list(self):
#         source = """
# [1, 2,
# 3, 4, 5,
# 6]
# """
#         self.assertEqual(redent(source), """
# [
#     1,
#     2,
#     3,
#     4,
#     5,
#     6,
# ]
# """)
# 
#     def test_it_splits_up_containers_exceeding_line_limit(self):
#         source = " " * 72 + "d = [1, 2, 3, 4]"
#         self.assertGreater(len(redent(source).splitlines()), 1)
# 
#     def test_if_it_is_confused_it_does_nothing(self):
#         source = "awefoijaowf;oiwfe[qpk1240i-"
#         self.assertEqual(redent(source), source)
# 
# 
# class TestFitsOnOneLine(TestCase):
#     def test_it_combines_dicts_that_fit_on_one_line(self):
#         source = """
# d = {
#            "this" : "dict",
# "fits" : "on",
#       "a single" : "line"
# }
# """
#         self.assertEqual(
#             redent(source),
#             '\nd = {"this" : "dict", "fits" : "on", "a single" : "line"}\n')
# 
#     def test_it_combines_args_that_fit_on_one_line(self):
#         pass
# 
# 
# class TestFullExample(TestCase):
#     def setUp(self):
#         patch = mock.patch("condent.fits_on_one_line", return_value=False)
#         patch.start()
#         self.addCleanup(patch.stop)
# 
#     def test_full_example(self):
#         source = """
#             d = {"foo": "bar",
#         "baz" : "quux",
#                             "spam": "eggs", "cat": "dog",}"""
# 
#         self.assertEqual(
#             redent(source),
#             """
#             d = {
#                 "foo" : "bar",
#                 "baz" : "quux",
#                 "spam" : "eggs",
#                 "cat" : "dog",
#             }"""
#         )
