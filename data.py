from math import pi, e;
from fractions import Fraction;

CONSTANTS = {
    "pi": pi,
    "e": e,
};

OPERATIONS = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "%": lambda x, y: x % y,
    "~": lambda x: -x,
    "^": lambda x, y: x ** y
};

PRECEDENCES = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "%": 2,
    "^": 4
};


OPERATORS = "".join(OPERATIONS.keys());

ARGUMENT_SEPARATOR = ",";

VALID_SYMBOLS = list("abcdfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ");
