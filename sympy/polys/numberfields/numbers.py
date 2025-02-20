"""Algebraic numbers -- forms of expression, and isolation."""

from sympy import AlgebraicNumber, sympify
from sympy.polys.numberfields.isomorphism import field_isomorphism
from sympy.polys.numberfields.minpoly import minpoly, primitive_element
from sympy.polys.polyerrors import IsomorphismFailed
from sympy.printing.lambdarepr import IntervalPrinter
from sympy.utilities import (
    lambdify, public
)

from mpmath import mp


@public
def to_number_field(extension, theta=None, *, gen=None):
    """Express `extension` in the field generated by `theta`. """
    if hasattr(extension, '__iter__'):
        extension = list(extension)
    else:
        extension = [extension]

    if len(extension) == 1 and isinstance(extension[0], tuple):
        return AlgebraicNumber(extension[0])

    minpoly, coeffs = primitive_element(extension, gen, polys=True)
    root = sum([ coeff*ext for coeff, ext in zip(coeffs, extension) ])

    if theta is None:
        return AlgebraicNumber((minpoly, root))
    else:
        theta = sympify(theta)

        if not theta.is_AlgebraicNumber:
            theta = AlgebraicNumber(theta, gen=gen)

        coeffs = field_isomorphism(root, theta)

        if coeffs is not None:
            return AlgebraicNumber(theta, coeffs)
        else:
            raise IsomorphismFailed(
                "%s is not in a subfield of %s" % (root, theta.root))


@public
def isolate(alg, eps=None, fast=False):
    """Give a rational isolating interval for an algebraic number. """
    alg = sympify(alg)

    if alg.is_Rational:
        return (alg, alg)
    elif not alg.is_real:
        raise NotImplementedError(
            "complex algebraic numbers are not supported")

    func = lambdify((), alg, modules="mpmath", printer=IntervalPrinter())

    poly = minpoly(alg, polys=True)
    intervals = poly.intervals(sqf=True)

    dps, done = mp.dps, False

    try:
        while not done:
            alg = func()

            for a, b in intervals:
                if a <= alg.a and alg.b <= b:
                    done = True
                    break
            else:
                mp.dps *= 2
    finally:
        mp.dps = dps

    if eps is not None:
        a, b = poly.refine_root(a, b, eps=eps, fast=fast)

    return (a, b)
