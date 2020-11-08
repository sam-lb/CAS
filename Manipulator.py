from CAS.data import OPERATIONS;
from CAS import Parser;

class Manipulator:

    """ Algebraic manipulator """

    @staticmethod
    def move_all_terms_to_left(left, right):
        return Parser.ParseTree(OPERATIONS["-"], [left, right], "-", type_="tree");
