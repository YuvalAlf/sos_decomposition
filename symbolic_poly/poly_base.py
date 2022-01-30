from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import List, Optional

import cvxpy as cp

from symbolic_poly.monom import Monom
from symbolic_poly.poly import Poly
from utils.cvxpy_utils import cvxpy_sum_product
from utils.math_utils import combinations_sum


@dataclass
class PolyBase:
    polys: List[Poly]

    @staticmethod
    def gen_random(variables: List[str], deg: int, num_polys: int, prng: Random) -> PolyBase:
        return PolyBase([Poly.gen_random(variables, deg, prng) for _ in range(num_polys)])

    def normalize_square(self) -> PolyBase:
        return PolyBase([poly.square().normalize() for poly in self.polys])

    # @on_error_return(None)
    def convex_approximation(self, variables: List[str], max_deg: int, poly: Poly) -> float:
        linear_multipliers = cp.Variable(len(self.polys))
        constraints = [multiplier >= 0 for multiplier in linear_multipliers]

        monoms = [Monom(dict(zip(variables, exponents))) for deg in range(max_deg + 1)
                  for exponents in combinations_sum(number_of_values=len(variables), desired_sum=deg)]

        sum_squares_error = cp.Constant(0.0)

        for monom in monoms:
            coefficients = [basis_poly[monom] for basis_poly in self.polys]
            total_coefficient = cvxpy_sum_product(coefficients, list(linear_multipliers))
            sum_squares_error += (poly[monom] - total_coefficient) ** 2

        objective = cp.Minimize(sum_squares_error)
        problem = cp.Problem(objective, constraints)
        result = problem.solve()
        return result

    def calc_error(self, variables: List[str], max_deg: int, prng: Random) -> float:
        poly = Poly.gen_random(variables, max_deg // 2, prng).square().normalize()
        return self.convex_approximation(variables, max_deg, poly)

    @staticmethod
    def calc_approximation_error(num_vars: int, base_polys: int, max_deg: int, sum_polys: int, prng: Random) \
            -> Optional[float]:
        half_deg = max_deg // 2
        variables = [f'x{num}' for num in range(1, num_vars + 1)]
        polys_in_sum = [Poly.gen_random(variables, half_deg, prng).square().normalize() for _ in range(sum_polys)]
        sum_poly = sum(polys_in_sum, Poly.zero()).normalize()
        poly_basis = PolyBase.gen_random(variables, half_deg, base_polys, prng).normalize_square()
        return poly_basis.convex_approximation(variables, max_deg, sum_poly)

