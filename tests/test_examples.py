import os
import textwrap
import unittest

from condent import Condenter


EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "examples")
REDENTED_FILE = os.path.join(os.path.dirname(__file__), "redented_examples")
SEP = "---\n"


class TestExamples(unittest.TestCase):
    def test_it_redents_the_examples(self):
        with open(EXAMPLE_FILE) as examples, open(REDENTED_FILE) as expected:
            examples.readline(), expected.readline()  # remove modeline

            examples = [e.splitlines(True) for e in examples.read().split(SEP)]
            expected = [e.splitlines(True) for e in expected.read().split(SEP)]

            for example, expect in zip(examples, expected):
                example = "".join(Condenter().redent(example))
                expect = "".join(expect)

                try:
                    self.assertEqual(example, expect)
                except Exception:
                    self.dump(example, expect)
                    raise

    def dump(self, example, expected):
        print textwrap.dedent("""

        Example failed:
        ===============

        Got
        ---

        {0}

        Expected
        --------

        {1}

        -----------------------------------------------------------------------

        """).format(example, expected)

