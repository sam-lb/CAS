from CAS.Tokenizer import *;
from CAS.Errors import UserError, EvaluationError;
from CAS.data import PRECEDENCES;
from CAS.Manipulator import Manipulator;
import math;


PARENTHESIS_WEIGHT = max(PRECEDENCES.values()) + 1;


class ParseTree():

    """ A parse tree of a mathematical expression """

    def __init__(self, function, subtrees, value, type_="tree"):
        self.type = type_;
        if self.type == "tree":
            self.function = function;
            self.subtrees = subtrees;
        else:
            self.value = value;

    def __evaluate(self, tree, **substitutions):
        """ evaluate a ParseTree at specific values """
        try:
            if tree.type == "tree":
                for arg in tree.subtrees:
                    pass;
                return perfect_ratio(tree.function(*[self.__evaluate(arg, **substitutions) for arg in tree.subtrees]));
            elif tree.type == "symbol":
                return perfect_ratio(substitutions[tree.value]);
            else:
                return tree.value;
        except ZeroDivisionError:
            raise EvaluationError("Division by zero");
        except ValueError:
            raise EvaluationError("Function input is out of domain");

    def __complex_evaluate(self, tree, **substitutions):
        """ evaluate a ParseTree at specific complex values """
        try:
            if tree.type == "tree":
                return tree.function(*[self.__complex_evaluate(arg, **substitutions) for arg in tree.subtrees]);
            elif tree.type == "symbol":
                return substitutions[tree.value];
            else:
                return tree.value;
        except ZeroDivisionError:
            raise EvaluationError("Division by zero");
        except ValueError:
            raise EvaluationError("Function input is out of domain");

    def evaluate(self, **substitutions):
        """ evaluate at specific values """
        # This is a wrapper for __evaluate so the ParseTree does not need to be explicitly passed as an argument.
        for value in substitutions.values():
            if not isinstance(value, (int, float, Fraction)):
                raise UserError("expressions can only be evaluated at float values, not {}".format(type(value)));
        return float(self.__evaluate(self, **substitutions));

    def complex_evaluate(self, **substitutions):
        """ evaluate at specific complex values """
        return self.__complex_evaluate(self, **substitutions);

    def quick_unsafe_evaluate(self, **substitutions):
        """ use this only if you are certain that the substitutions are of the correct type """
        return float(self.__evaluate(self, **substitutions));

    def evaluate_exact(self, **substitutions):
        """ does not convert to float """
        for value in substitutions.values():
            if not isinstance(value, (int, float, Fraction)):
                raise UserError("expressions can only be evaluated at float values");
        return self.__evaluate(self, **substitutions);

    def quick_unsafe_evaluate_exact(self, **substitutions):
        """ use this only if you are certain that the substitutions are of the correct type """
        return self.__evaluate(self, **substitutions);

    def evaluate_with_dict(self, substitutions):
        """ evaluate with dict data, not keyword arguments """
        return float(self.__evaluate(self, **substitutions));

    def set_ordered_subs(self, valid_symbols):
        """ Set a tuple of valid symbols so evaluation doesn't require passing a dict with the correct variable names """
        self.valid_symbols = valid_symbols;
        self.valid_symbols_length = len(valid_symbols);

    def evaluate_with_values_only(self, values: tuple):
        """ evaluate given a tuple of values only. set_ordered_subs must have been called """
        # I just put the type hint here because I don't want to call this "unsafe"
        subs = dict(zip(self.valid_symbols, values));
        return self.evaluate_with_dict(subs);

class Parser():

    """ object to parse a string into a ParseTree """

    def __init__(self, defined_functions={}, defined_symbols=[]):
        self._tokenizer = Tokenizer(defined_functions, defined_symbols);

    def define_functions(self, **functions):
        """ define additional functions """
        temp = self._tokenizer.functions;
        temp.update(functions);
        self._tokenizer.functions = temp;

    def redefine_functions(self, **functions):
        """ redefine the allowed functions """
        self._tokenizer.functions = functions;

    def define_symbols(self, *symbols):
        """ define additional symbols """
        self._tokenizer.symbols += symbols;

    def redefine_symbols(self, *symbols):
        """ redefine the allowed symbols """
        self._tokenizer.symbols = symbols;

    def get_arguments(self, tokens):
        """ split a list of tokens at the argument separator (comma) """
        result, sub_list, p_count = [], [], 0;
        for token in tokens:
            if isinstance(token, OtherToken):
                if token.value == ",":
                    if p_count == 1:
                        result.append(sub_list)
                        sub_list = [];
                    else:
                        sub_list.append(token);
                elif token.value == "(":
                    p_count += 1;
                    sub_list.append(token);
                elif token.value == ")":
                    p_count -= 1;
                    sub_list.append(token);
            else:
                sub_list.append(token);
        if sub_list: result.append(sub_list); # sub_list could be [] if there is only one argument
        return result;

    def get_lowest_precedence_token(self, tokens):
        """ get the index of the token with lowest precedence in a list of tokens. -1 if no tokens have a precedence (terminal) """
        lowest_index, lowest_precedence = -1, len(tokens) * PARENTHESIS_WEIGHT;
        for i, token in enumerate(tokens):
            if isinstance(token, (InfixFunction, PrefixFunction)):
                if token.precedence < lowest_precedence:
                    lowest_index = i;
                    lowest_precedence = token.precedence;
                elif (token.precedence == lowest_precedence and token.associativity == -1):
                    lowest_index = i;
                    lowest_precedence = token.precedence;
        return lowest_index, tokens[lowest_index];

    def get_unary_arguments(self, tokens, index):
        """ get the arguments of a prefix function """
        tokens, arglist, count = tokens[index+1:], [], 1;
        for token in tokens:
            if isinstance(token, OtherToken):
                if token.value == "(": count += 1;
                elif token.value == ")": count -= 1;
                if not count:
                    arglist.append(token);
                    break;
            arglist.append(token);
        return self.get_arguments(arglist);

    def __parse(self, weighted_tokens):
        """ parses a list of tokens that have their precedences weighted by parentheses """
        lowest_index, lowest_token = self.get_lowest_precedence_token(weighted_tokens);
        if lowest_index == -1:
            token = [tkn for tkn in weighted_tokens if not isinstance(tkn, OtherToken)][0];
            type_ = "symbol" if isinstance(token, Symbol) else "number";
            return ParseTree(None, None, token.value, type_);

        if isinstance(lowest_token, InfixFunction):
            l, r = self.__parse(weighted_tokens[:lowest_index]), self.__parse(weighted_tokens[lowest_index+1:]);
            return ParseTree(lowest_token.value, [l, r], None);

        elif isinstance(lowest_token, PrefixFunction):
            zo = [self.__parse(argument) for argument in self.get_unary_arguments(weighted_tokens, lowest_index)];
            return ParseTree(lowest_token.value, zo, None);

    def parse(self, expression):
        """ parses a mathematical expression into a ParseTree """
        tokens, p_count = self._tokenizer.tokenize(expression), 0;

        for token in tokens:
            if isinstance(token, OtherToken):
                if token.value == "(":
                    p_count += 1;
                elif token.value == ")":
                    p_count -= 1;
            elif isinstance(token, (InfixFunction, PrefixFunction)):
                token.precedence += p_count * PARENTHESIS_WEIGHT;
        return self.__parse(tokens);

    def parse_equation(self, equation):
        """ parses the left and right sides of an equation. Returns a ParseTree with all terms on the left """
        left, right = equation.split("=");
        left = self.parse(left);
        right = self.parse(right);
        return Manipulator.move_all_terms_to_left(left, right);


if __name__ == "__main__":
    p = Parser({"sin": math.sin, "cos": math.cos, "exp": math.exp}, ["x", "y", "A", "a"]);
    multiarg = Parser({"max": max, "abs":abs}, ["a", "b"]);
