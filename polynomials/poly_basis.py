from __future__ import annotations

from itertools import chain

import cvxpy as cp
import more_itertools
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from methodtools import lru_cache
from random import Random
from symtable import Symbol
from typing import List, Tuple, Iterable, Dict

from more_itertools import ilen
from sympy import Poly, symbols, Expr
from polynomials.poly import gen_normalized_poly, normalize, poly_to_str, Monomial
from utils import math_utils
from utils.cvxpy_utils import sum_product
from utils.iterable_utils import enumerate1
from utils.math_utils import combinations_sum


@dataclass
class PolyBasis:
    variables: List[Symbol]
    polys: List[Poly]

    @cached_property
    def max_deg(self) -> int:
        return max(poly.total_degree() for poly in self.polys)

    @cached_property
    def poly_len(self):
        return ilen(self.poly_combinations())

    @lru_cache(maxsize=20)
    def monomimals(self, index: int) -> Dict[Monomial, float]:
        return self.polys[index].as_expr().as_coefficients_dict()

    def all_monomials(self) -> Iterable[Dict[Monomial, float]]:
        for index in range(len(self.polys)):
            yield self.monomimals(index)

    def poly_combinations(self) -> Iterable[Tuple[Monomial, List[float]]]:
        for combination in combinations_sum(number_of_values=len(self.variables) + 1, desired_sum=self.max_deg):
            monomial = math_utils.product(variable ** exponent
                                          for exponent, variable in zip(combination, chain([1], self.variables)))
            yield monomial, [monomial_dict[monomial] for monomial_dict in self.all_monomials()]

    def __str__(self):
        return '\n'.join([f'\t{index}) {poly_to_str(poly)}' for index, poly in enumerate1(self.polys)])

    @staticmethod
    def gen_random_basis(num_variables: int, num_polys: int, max_deg: int, random: Random) -> PolyBasis:
        variables = symbols(f'x1:{num_variables+1}')
        polys = [gen_normalized_poly(variables, max_deg, random) for _ in range(num_polys)]
        return PolyBasis(variables, polys)

    def square(self) -> PolyBasis:
        return PolyBasis(self.variables, [normalize(poly*poly) for poly in self.polys])

    def approximate(self, poly: Poly) -> (List[Tuple[float, Poly]], Poly, float):
        linear_multipliers = cp.Variable(len(self.polys))
        error_poly = cp.Variable(self.poly_len)
        objective = cp.Minimize(cp.sum_squares(error_poly))
        constraints = []
        all_monomials = []
        for error, (monomial, coefficients) in zip(error_poly, self.poly_combinations()):
            all_monomials.append(monomial)
            total_coefficient = sum_product(coefficients, list(linear_multipliers))
            constraints.append(total_coefficient + error == poly.coeff_monomial(monomial))

        problem = cp.Problem(objective, constraints)
        result = problem.solve()
        result_error_poly = sum(coefficient * monom for coefficient, monom in zip(error_poly.value, all_monomials))
        multipliers = list(zip(linear_multipliers.value, self.polys))
        return multipliers, result_error_poly, result


        cp.constraints()

