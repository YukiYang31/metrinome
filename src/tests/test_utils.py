"""This is used to test the utils that are primarily used in computing APC and path complexity."""
import unittest
from time import sleep

from sympy import sympify  # type: ignore

import utils
from core.env import Env


class Testutils(unittest.TestCase):
    """Test all of the utils methods."""

    # === show_func_defs ===
    def test_show_func_defs(self) -> None:
        """Check that we can get the names of all functions in a C file."""
        names = utils.show_func_defs(Env.project_file("tests/cFiles/collatz.c"))
        self.assertTrue(len(names.keys()) == 1)
        self.assertTrue(list(names.keys())[0] == "countCollatz")

    # === get_solution_from_roots ===
    def test_solution_from_roots(self) -> None:
        """
        Verify that we get the correct solution to recurrence solution.

        The method should return the solution to a linear homogeneous recurrence relation
        from the roots of the charactersic equation.
        """
        # utils.getSolutionFromRoots()
        # self.assertEqual('1', '1')

    # === get_recurrence_solution ===
    def test_recurrence_solution(self) -> None:
        """Returns the solution to an arbitrary linear homogeneous recurrence relation."""
        # utils.getRecurrenceSolution()
        # self.assertEqual('1', '1')

    # === get_taylor_coeffs ===
    def test_taylor_coeffs(self) -> None:
        """
        Verify that we get the correct coefficients of a Taylor series.

        This should return the coefficients of the Taylor series of a
        rational function (p(x) / q(x) where p and q are polynomials),
        up to a specified degree.
        """
        # utils.getTaylorCoeffs()
        # self.assertEqual('1', '1')

    # === big_o ===
    def test_big_o_empty(self) -> None:
        """Check that we can get the big O of an empty expression."""
        big_o = utils.big_o([])
        self.assertEqual(big_o, '0')

    def test_big_o_constant(self) -> None:
        """
        Terms of the same order are summed, so the big O of constants is their sum.

        Callers (metric.path_complexity) pass the sympy terms of path(n); same-order terms
        are combined (`simplify(term_one + term_two)`) rather than one being dropped.
        """
        big_o_one = utils.big_o(list(sympify(['1', '2', '3'])))
        big_o_two = utils.big_o(list(sympify(['3', '2', '1'])))

        self.assertEqual(sympify(big_o_one), 6)
        self.assertEqual(sympify(big_o_two), 6)

    def test_big_o_same_order_sympy_terms(self) -> None:
        """Same-order terms are summed while lower-order terms are dropped."""
        big_o = utils.big_o(list(sympify(['2*n**2', '5*n', '3*n**2'])))
        self.assertEqual(sympify(big_o), sympify('5*n**2'))

    def test_big_o_same_order_strings(self) -> None:
        """Same-order terms given as strings (the documented input) are added, not concatenated."""
        self.assertEqual(sympify(utils.big_o(['1', '2', '3'])), 6)

    def test_big_o_polynomial(self) -> None:
        """The big_o of a polynomial should be O(x^n) where n is the degree of the polynomial."""
        # Expression One: "1 - x + 6*x^8"
        # Expression Two: = "1.2*x^(8.4) - 3.1*x"

        polynomial_expression = ['1', '-n', '6*n^8']
        polynomial_expression_two = ['1.2 * n^(8.4)', '-3.1 * n']

        big_o_one = utils.big_o(polynomial_expression)
        big_o_two = utils.big_o(polynomial_expression_two)

        expectedbig_o_one = '6*n^8'
        expectedbig_o_two = '1.2 * n^(8.4)'
        self.assertEqual(expectedbig_o_one, big_o_one)
        self.assertEqual(expectedbig_o_two, big_o_two)

    def test_big_o_exponential(self) -> None:
        """The big_o of an exponential should be O(a^n) where a is the base (variable is 'n')."""
        expression = ['1000000', 'n', '.5**n', '2**n']
        expression_two = ['2*1.01**n', '1.02**n']

        self.assertEqual(utils.big_o(expression), '2**n')
        self.assertEqual(utils.big_o(expression_two), '1.02**n')

    # === Timeout ===
    def test_timeout_notimetout(self) -> None:
        """A function that is done before the timeout limit should behave normally."""
        def fast_func() -> int:
            """Execute immediately."""
            return 7

        result = 0
        with utils.Timeout(seconds=1):
            result = fast_func()
        self.assertEqual(result, 7)

    def test_timeout_timeout(self) -> None:
        """A function that takes too long to execute should throw an error."""
        def slow_func() -> None:
            sleep(2)

        with self.assertRaises(TimeoutError):
            with utils.Timeout(seconds=1):
                slow_func()


if __name__ == '__main__':
    unittest.main()
