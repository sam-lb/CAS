from fractions import Fraction;
from CAS.Errors import UserError, InternalError;
from CAS.data import OPERATORS, CONSTANTS, OPERATIONS, VALID_SYMBOLS, PRECEDENCES;
from math import sin, exp, gcd;
from pprint import pprint;


ts1 = "3x+1-(-6^x)*sin(y/2+2)";
ts2 = "e + exp(A/(a+3))";


def perfect_ratio(flt):
    """ return a fraction that PERFECTLY represents a float. the fractions module still falls victim to floating point errors (although it will reduce the fraction) """
    if isinstance(flt, (int, float)):
        str_flt = str(flt);
        if not "." in str_flt:
            return Fraction(int(flt), 1);
        else:
            mag = 10 ** len(str_flt.split(".")[1]);
            return Fraction(int(flt * mag), int(mag));
    elif isinstance(flt, Fraction):
        return flt;
    else:
        raise InternalError("An internal error has occurred. Details: perfect_ratio expected a float or Fraction but got {} instead".format(type(flt)));


class Number():

    """ A number in an expression """

    def __init__(self, value):
        self.value = perfect_ratio(value);

    def __repr__(self):
        return "{}".format(self.value);


class Symbol():

    """ A symbol (variable) in an expression """

    def __init__(self, value):
        self.value = value;

    def __repr__(self):
        return self.value;


class InfixFunction():

    """ An infix function (a function that is between its two arguments) """

    def __init__(self, name, value):
        self.name = name;
        self.value = value;
        self.precedence = PRECEDENCES[name];
        self.associativity = -1 if self.name == "^" else 1;

    def __repr__(self):
        return self.name;


class PrefixFunction():

    """ A prefix function (a function that is before its arbitrary number of arguments) """

    def __init__(self, name, value):
        self.name = name;
        self.value = value;
        self.precedence = 3;

    def __repr__(self):
        return self.name;


class OtherToken():

    """ Another token in an expression: (, ), or ,. """

    def __init__(self, value):
        self.value = value;

    def __repr__(self):
        return self.value;


class Tokenizer():

    """ Turns a string into a set of tokens """

    def __init__(self, defined_functions={}, defined_symbols=[]):
        self.test_function_dict(defined_functions);
        self.test_symbol_list(defined_symbols);
        
        self._functions = defined_functions;
        self._symbols = defined_symbols;
        self.get_function_names();
        self.get_valid_characters();

    def __repr__(self):
        return "Tokenizer(\n\t Defined functions: {}\n\t Defined symbols: {}\n\t Legal Characters: {}\n)".format(self._functions, self._symbols, self._valid_characters);

    @property
    def functions(self):
        """ returns the dict of defined functions """
        return self._functions;

    @functions.setter
    def functions(self, function_dict):
        """ sets the dict of defined functions """
        self.test_function_dict(function_dict);
        self._functions = function_dict;
        self.get_function_names();
        self.get_valid_characters();

    @property
    def symbols(self):
        """ returns the list of defined symbols """
        return self._symbols;

    @symbols.setter
    def symbols(self, symbol_list):
        """ sets the list of defined functions """
        self.test_symbol_list(symbol_list);
        self._symbols = symbol_list;
        self.get_valid_characters();

    def get_function_names(self):
        """ gets the list of strings of defined functions """
        self._function_names = sorted(self._functions.keys(), key=lambda f: len(f), reverse=True);

    def get_valid_characters(self):
        """ gets a list of all valid letters """
        self._valid_characters = list(set(("".join(self._function_names) + "".join(self._symbols)) + "".join(CONSTANTS.keys())));

    def test_function_dict(self, function_dict):
        """ checks if a set of defined functions is valid """
        if not isinstance(function_dict, dict):
            raise UserError("Defined functions must be a dict of the form {function name: function}. Actual value: {}".format(function_dict));
        else:
            for name, function in function_dict.items():
                if not isinstance(name, str):
                    raise UserError("Names of defined functions must be strings. Actual value of first illegal name: {}".format(name));
                if not callable(function):
                    raise UserError("Defined functions must be callable. Actual value of first illegal function: {}".format(function));

    def test_symbol_list(self, symbol_list):
        """ checks if a list of defined symbols is valid """
        if not hasattr(symbol_list, "__iter__"):
            raise UserError("List of symbols must be iterable. Actual list of symbols: {}".format(symbol_list));
        else:
            for symbol in symbol_list:
                if not isinstance(symbol, str): raise UserError("Symbols must be strings.");
                elif symbol not in VALID_SYMBOLS: raise UserError("Symbols must be an alphabetic character of length 1.");

    def special_split(self, string, sep="+-"):
        """ splits the string each time a character in sep is encountered, but not when inside parentheses """
        p_count, segments, buffer = 0, [], "";
        for character in string:
            if character in sep and p_count == 0:
                if len(buffer) > 0:
                    segments.append(buffer);
                    buffer = "";
                segments.append(character);
                continue;
            elif character == "(": p_count += 1;
            elif character == ")": p_count -= 1;
            buffer += character;
        if buffer: segments.append(buffer);
        return segments;

    def handle_unary_minus(self, string, replacement="~"):
        """ detects when there is a unary '-' and replaces it with '~' because somebody thought it would be a good idea to use the same symbol for 2 different things """
        result, last_character = "", string[0];

        if last_character == "-":
            result += replacement;
        else:
            result += last_character;
            
        for i, character in enumerate(string[1:]):
            if character == "-":
                if last_character in "+-*/^(":
                    result += replacement;
                else:
                    result += character;
            else:
                result += character;
            last_character = character;
        return result;

    def clean(self, string):
        """ removes whitespace and notational clutter, handles implicit multiplication, locates function names and constants """
        string = string.replace(" ", "").replace("+-", "-").replace("--", "+");
        
        new_string = string[0];
        for i, character in enumerate(string[1:], start=1):
            if ((character in self._valid_characters+["("]) and (string[i-1] not in OPERATORS+"(,")):
                new_string += "*" + character;
            else:
                new_string += character;

        for name in self._function_names:
            old = "*".join(list(name)) + "*";
            new_string = new_string.replace(old, name);
        for name in sorted(CONSTANTS.keys(), key=lambda name: len(name), reverse=True):
            old = "*".join(list(name));
            new_string = new_string.replace(old, name);
            
        return new_string;

    def test(self, string):
        """ test the string: parens, illegal characters """
        pass;

    def get_components(self, string):
        """ separate the string at each operator, parenthesis, and comma """
        result, buffer = [], "";
        for character in string:
            if character in OPERATORS+"(),":
                if buffer:
                    result.append(buffer);
                    buffer = ""
                result.append(character);
            else:
                buffer += character;
        if buffer: result.append(buffer);
        return result;

    def tokenize_term(self, term):
        """ return a list of tokens from a single term """
        components, tokens, negates = self.get_components(term), [], 0;

        for component in components:
            if component in self._function_names:
                tokens.append(PrefixFunction(component, self._functions[component]));
            elif component == "~":
                tokens.append(PrefixFunction("~", OPERATIONS[component]));
                ###
                tokens.append(OtherToken("("));
                negates += 1;
                ###
            elif component in OPERATORS:
                tokens.append(InfixFunction(component, OPERATIONS[component]));
            elif component.replace(".", "").isdigit():
                tokens.append(Number(float(component)));
            elif component in CONSTANTS.keys():
                tokens.append(Number(CONSTANTS[component]));
            elif component in self._symbols:
                tokens.append(Symbol(component));
            elif component in "(),":
                tokens.append(OtherToken(component));
            else:
                raise UserError("Invalid token '{}'".format(component));
        ###
        for i in range(negates):
            tokens.append(OtherToken(")"));
        ###
        return tokens;

    def tokenize(self, expression):
        """ get tokens from an expression """
        if not isinstance(expression, str): raise UserError("Expression must be a string. Actual expression: {}".format(expression));
        
        tokens = [];
        for term in self.special_split(self.handle_unary_minus(self.clean(expression))):
            tokens += self.tokenize_term(term);
        return tokens;


if __name__ == "__main__":
    t = Tokenizer({"sin": sin}, ["x", "y"]);
    t2 = Tokenizer({"exp": exp}, ["A", "a"]);
