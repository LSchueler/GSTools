# -*- coding: utf-8 -*-
"""
GStools subpackage providing tools for the covariance-model.

.. currentmodule:: gstools.covmodel.tools

The following classes and functions are provided

.. autosummary::
   InitSubclassMeta
   rad_fac
   set_len_anis
   check_bounds
   check_arg_in_bounds
   default_arg_from_bounds
"""

# pylint: disable=C0103
import numpy as np
from scipy import special as sps
from gstools.tools.geometric import set_anis

__all__ = [
    "InitSubclassMeta",
    "rad_fac",
    "set_len_anis",
    "check_bounds",
    "check_arg_in_bounds",
    "default_arg_from_bounds",
]


# __init_subclass__ hack for Python 3.5

if hasattr(object, "__init_subclass__"):
    InitSubclassMeta = type
else:

    class InitSubclassMeta(type):  # pragma: no cover
        """Metaclass that implements PEP 487 protocol.

        Notes
        -----
        See :
            https://www.python.org/dev/peps/pep-0487

        taken from :
            https://github.com/graphql-python/graphene/blob/master/graphene/pyutils/init_subclass.py
        """

        def __new__(cls, name, bases, ns, **kwargs):
            """Create a new subclass."""
            __init_subclass__ = ns.pop("__init_subclass__", None)
            if __init_subclass__:
                __init_subclass__ = classmethod(__init_subclass__)
                ns["__init_subclass__"] = __init_subclass__
            return super(InitSubclassMeta, cls).__new__(
                cls, name, bases, ns, **kwargs
            )

        def __init__(cls, name, bases, ns, **kwargs):
            super(InitSubclassMeta, cls).__init__(name, bases, ns)
            super_class = super(cls, cls)
            if hasattr(super_class, "__init_subclass__"):
                super_class.__init_subclass__.__func__(cls, **kwargs)


# Helping functions ###########################################################


def rad_fac(dim, r):
    """Volume element of the n-dimensional spherical coordinates.

    Given as a factor for integration of a radial-symmetric function.

    Parameters
    ----------
    dim : :class:`int`
        spatial dimension
    r : :class:`numpy.ndarray`
        Given radii.
    """
    if dim == 1:
        fac = 2.0
    elif dim == 2:
        fac = 2 * np.pi * r
    elif dim == 3:
        fac = 4 * np.pi * r ** 2
    else:  # general solution ( for the record :D )
        fac = (
            dim
            * r ** (dim - 1)
            * np.sqrt(np.pi) ** dim
            / sps.gamma(dim / 2.0 + 1.0)
        )
    return fac


def set_len_anis(dim, len_scale, anis):
    """Set the length scale and anisotropy factors for the given dimension.

    Parameters
    ----------
    dim : :class:`int`
        spatial dimension
    len_scale : :class:`float` or :class:`list`
        the length scale of the SRF in x direction or in x- (y-, ...) direction
    anis : :class:`float` or :class:`list`
        the anisotropy of length scales along the transversal axes

    Returns
    -------
    len_scale : :class:`float`
        the main length scale of the SRF in x direction
    anis : :class:`list`, optional
        the anisotropy of length scales along the transversal axes

    Notes
    -----
    If ``len_scale`` is given by at least two values,
    ``anis`` will be recalculated.

    If ``len_scale`` is given as list with to few values, the latter value will
    be used for the remaining dimensions. (e.g. [l_1, l_2] in 3D is equal to
    [l_1, l_2, l_2])

    If to few ``anis`` values are given, the first dimensions will be filled
    up with 1. (eg. anis=[e] in 3D is equal to anis=[1, e])
    """
    ls_tmp = np.array(len_scale, dtype=np.double)
    ls_tmp = np.atleast_1d(ls_tmp)[:dim]
    # use just one length scale (x-direction)
    out_len_scale = ls_tmp[0]
    # set the anisotropies in y- and z-direction according to the input
    if len(ls_tmp) == 1:
        out_anis = set_anis(dim, anis)
    else:
        # fill up length-scales with the latter len_scale, such that len()==dim
        if len(ls_tmp) < dim:
            ls_tmp = np.pad(ls_tmp, (0, dim - len(ls_tmp)), "edge")
        # if multiple length-scales are given, calculate the anisotropies
        out_anis = np.zeros(dim - 1, dtype=np.double)
        for i in range(1, dim):
            out_anis[i - 1] = ls_tmp[i] / ls_tmp[0]

    for ani in out_anis:
        if not ani > 0.0:
            raise ValueError(
                "anisotropy-ratios needs to be > 0, " + "got: " + str(out_anis)
            )
    return out_len_scale, out_anis


def check_bounds(bounds):
    """
    Check if given bounds are valid.

    Parameters
    ----------
    bounds : list
        bound can contain 2 to 3 values:
            1. lower bound
                float
            2. upper bound
                float
            3. Interval type (optional)
                * "oo" : open - open
                * "oc" : open - close
                * "co" : close - open
                * "cc" : close - close
    """
    if len(bounds) not in (2, 3):
        return False
    if bounds[1] <= bounds[0]:
        return False
    if len(bounds) == 3 and bounds[2] not in ("oo", "oc", "co", "cc"):
        return False
    return True


def check_arg_in_bounds(model, arg, val=None):
    """Check if given argument value is in bounds of the given model."""
    if arg not in model.arg_bounds:
        raise ValueError("check bounds: unknown argument: {}".format(arg))
    bnd = list(model.arg_bounds[arg])
    val = getattr(model, arg) if val is None else val
    error_case = 0
    if len(bnd) == 2:
        bnd.append("cc")  # use closed intervals by default
    if bnd[2][0] == "c":
        if val < bnd[0]:
            error_case = 1
    else:
        if val <= bnd[0]:
            error_case = 2
    if bnd[2][1] == "c":
        if val > bnd[1]:
            error_case = 3
    else:
        if val >= bnd[1]:
            error_case = 4
    return error_case


def default_arg_from_bounds(bounds):
    """
    Determine a default value from given bounds.

    Parameters
    ----------
    bounds : list
        bounds for the value.

    Returns
    -------
    float
        Default value in the given bounds.
    """
    if bounds[0] > -np.inf and bounds[1] < np.inf:
        return (bounds[0] + bounds[1]) / 2.0
    if bounds[0] > -np.inf:
        return bounds[0] + 1.0
    if bounds[1] < np.inf:
        return bounds[1] - 1.0
    return 0.0
