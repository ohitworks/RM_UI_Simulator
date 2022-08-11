"""
这里定义了模仿C类型的对象，请注意其实没有模仿真实最大值情况。
"""

from RM_UI_Simulator.c_reader.ctype import c_range
from RM_UI_Simulator.c_reader.debugger import debugger

import math


class CtypeBase:
    pass


class CIntBase(CtypeBase):
    MAX = None
    MIN = None

    def __init__(self, number):
        self.number = int(number)
        if not self.MIN <= self.number <= self.MAX:
            raise ValueError(f"{type(self).__name__} 取值范围为 [-32768, 32767], {self.number} 超过范围")

    def __repr__(self):
        return f"{type(self).__name__}({self.number})"

    def __bool__(self):
        return bool(self.number)

    def __eq__(self, other):
        if isinstance(other, (C_Int, C_UInt)):
            return C_Int(self.number == other.number)
        elif isinstance(other, (C_Float, C_double)):
            return C_Int(self.number == other.integer and other.decimal == 0)
        elif isinstance(other, (int, float)):
            return C_Int(self.number == other)
        else:
            return C_Int(0)

    def __int__(self):
        return self.number


class C_Int(CIntBase):
    MIN = c_range.INT_MIN
    MAX = c_range.INT_MAX


class C_UInt(CIntBase):
    MAX = c_range.UINT_MAX
    MIN = 0


class CFloatBase(CtypeBase):
    MANTISSA = None  # 尾数长度
    EXPONENT = None  # 指数长度

    def __init__(self, float_or_string: (float, str)):
        """
        integer 保存整数部分， decimal 保存小数部分， float = integer + decimal * pow(10, exp)
        """
        if not isinstance(float_or_string, str):
            float_or_string = str(float_or_string)
        a, _, b = float_or_string.partition(".")
        self.integer = int(a)
        b = b.rstrip("0")
        if b:
            self.decimal = int(b)
            self.exp = len(b)
        else:
            self.decimal = 0
            self.exp = 1
        self.precision_adjustment()

    def __bool__(self):
        return bool(float(self))

    @debugger.register_important_function("C_Float or C_Double：精度调节")
    def precision_adjustment(self):
        """精度调节
        """
        mantissa, exponent = math.frexp(abs(float(self)))  # 这种方法求出来的 mantissa相当于把补码加上后的， exponent则是标准的+1

        exponent_max = (1 << (self.EXPONENT - 1))
        exponent_min = -exponent_max - 1
        if not exponent_min <= exponent - 1 <= exponent_max:
            raise ValueError(f"{type(self).__name__} 指数过大")

        if mantissa == 0 or mantissa == 0.5:  # 整倍，如 0 = 0.0 / 2^0 0.5 = 1 / 2^1
            return
        # 此时以证明该小数无法被完整表达，开始考虑精度问题

        # 2022-4-14 更新：我来这里修bug，然后发现 emmm 根本看不懂这段数学运算在干什么。。于是加了个 if 排除错误情况并优化了一下计算流程。
        i = 3
        e = 2
        temp = mantissa * (1 << e)
        while temp != i:
            if e > self.MANTISSA:  # 由于此方法的后效性，此代码不应使用 self.MANTISSA - 1
                self.precision_adjustment.send_message(f"{type(self).__name__}: mantissa max")
                break
            if temp < i:
                e += 1
                i += i - 1
                temp *= 2
            else:
                i += 1

        # 此时 i 去掉二进制首位再左移至self.MANTISSA长度即为码位
        _, new_e = math.frexp(i)
        try:
            new = i * (1 << (exponent - new_e))
        except ValueError:
            if exponent > 0:
                new = i / (1 << new_e) * (1 << exponent)
            else:
                new = i / (1 << new_e) / (1 << -exponent)
        if self.integer < 0:
            new = - new

        a, _, b = str(new).partition(".")
        self.integer = int(a)
        b = b.rstrip("0")
        if b:
            self.decimal = int(b)
            self.exp = len(b)
        else:
            self.decimal = 0
            self.exp = 1

    @staticmethod
    def _get_compare(m, e):
        return m * (1 << e)

    def __repr__(self):
        d = str(self.decimal).ljust(self.exp, "0")
        return f"{type(self).__name__}({self.integer}.{d})"

    def __float__(self):
        return float(f"{self.integer}.{str(self.decimal).ljust(self.exp, '0')}")

    def __eq__(self, other):
        if isinstance(other, (C_Float, C_double)):
            return C_Int(self.decimal == other.decimal and self.integer == self.integer)
        elif isinstance(other, (C_Int, C_UInt)):
            return C_Int(self.decimal == 0 and self.integer == other.number)
        elif isinstance(other, (int, float)):
            return C_Int(float(self) == other)


class C_Float(CFloatBase):
    MANTISSA = 23
    EXPONENT = 8


class C_double(CFloatBase):
    MANTISSA = 52
    EXPONENT = 11


class C_Char(CtypeBase):
    def __init__(self, code):
        if isinstance(code, (int, CIntBase)):
            if not c_range.CHAR_MIN <= code <= c_range.CHAR_MAX:
                raise ValueError("char 值超过范围")
        elif isinstance(code, (str, bytes)):
            if len(code) != 1:
                raise ValueError("char 长度应为1")
            if not c_range.CHAR_MIN <= ord(code) <= c_range.CHAR_MAX:
                raise ValueError("char 值超过范围")
        self.string = str(code)

    def __repr__(self):
        return f"{type(self).__name__}(%s)" % repr(self.string)

    def __bool__(self):
        return bool(self.string)

    def __eq__(self, other):
        if isinstance(other, C_Char):
            return C_Int(self.string == other.string)
        elif isinstance(other, (CIntBase, int)):
            return C_Int(ord(self.string))
        else:
            return C_Int(self.string == other)

    def __int__(self):
        return ord(self.string)
