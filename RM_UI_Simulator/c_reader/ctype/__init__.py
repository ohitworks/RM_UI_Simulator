"""
本模块用于模拟C语言类型，默认为32位。
"""

from . import c_range, core
from .core import CtypeBase, C_Int, C_UInt, C_double, C_Float, C_Char

__all__ = ["core", "c_range",
           "CtypeBase", "C_Int", "C_UInt", "C_double", "C_Char", "C_Float"]
