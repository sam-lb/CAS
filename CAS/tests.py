from CAS.Parser import Parser;
from time import time;
from math import e, pi, sin, cos;


expressions = [
    "-2+4",
    "1/x+3",
    "x/-2",
    "sin(cos(1 + x) + x    )",
    "pi+e*3x^4",
    "-2-sin(4-xyz/2)"
];

lambdas = [
    lambda x, y, z: -2+4,
    lambda x, y, z: 1/x+3,
    lambda x, y, z: x/-2,
    lambda x, y, z: sin(cos(1+x)+x),
    lambda x, y, z: pi+e*3*x**4,
    lambda x, y, z: -2-sin(4-x*y*z/2)
];

tests = list(zip(expressions, lambdas));

def bench(test, iterations):
    parser_expression, python_expression = test;
    parser = Parser({"sin": sin, "cos": cos}, ["x", "y", "z"]);
    parser_expression = parser.parse(parser_expression);

    x, y, z = 12.1, 14.2, 5.0;
    parser_initial_time = time();
    for i in range(iterations):
        parser_expression.evaluate(x=x, y=y, z=z);
    parser_final_time = time();
    parser_time = parser_final_time - parser_initial_time;

    python_initial_time = time();
    for i in range(iterations):
        python_expression(x, y, z);
    python_final_time = time();
    python_time = python_final_time - python_initial_time;

    return "Parser time: {}, Python time: {}".format(parser_time, python_time);


