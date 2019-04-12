#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
calc: A general-purpose, feature-rich calculator module

Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the attached licensing agreement.
 
 Copyright (c) Neil Tallim, 2002-2016
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.
 
 You should have received a copy of the GNU Lesser General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import collections
import functools
import math
import re
import random

#Constants
########################################
_ALPHA_BLOB = r"[A-Za-z_]" #: All characters that can be used in a variable/function name.
_NUMERIC_REGEXP = re.compile(r"^(\d+(?:\.\d+)?|\.\d+)") #: Matches numeric entities.
_FUNCTION_REGEXP = re.compile(r"^(%s+)\(" % (_ALPHA_BLOB)) #: Matches function entities.
_VARIABLE_REGEXP = re.compile(r"^(%s+|\?)" % (_ALPHA_BLOB)) #: Matches variable entities.
_QUOTED_VARIABLE_REGEXP = re.compile(r'^`(.+?)`') #: Matches quoted variable entities.

_LINE_FUNCTION_REGEXP = re.compile(r"^(%s+)\(\s*(?:((?:%s+,\s*)*%s+)\s*)?\)\s*=\s*(.+)$" % (_ALPHA_BLOB, _ALPHA_BLOB, _ALPHA_BLOB)) #: Determines whether a line is a function.
_LINE_SOLVE_LINEAR_REGEXP = re.compile(r"^solve\(\s*(.+?)\s*,\s*(.+?)\s*\)$") #: Determines whether a line is a solve() function.
_LINE_VARIABLE_REGEXP = re.compile(r"^(%s+)\s*=\s*(.+)$" % (_ALPHA_BLOB)) #: Determines whether a line is a variable.

_LINE_EQUATION = 0 #: Indicates that a line seems to be an equation.
_LINE_FUNCTION = 1 #: Indicates that a line seems to be a function.
_LINE_SOLVE_LINEAR = 2 #: Indicates that a line seems to be a solve() function.
_LINE_VARIABLE = 3 #: Indicates that a line seems to be a variable.

_FUNCTION_CUSTOM = 0 #: Indicates that a token is a custom function.
_FUNCTION_BUILTIN = 1 #: Indicates that a token is a built-in function.
_FUNCTION_EXTERNAL = 2 #: Indicates that the token is an external function.
_VARIABLE_CUSTOM = 10 #: Indicates that a token is a custom variable.
_VARIABLE_BUILTIN = 11 #: Indicates that a token is a built-in variable.
_VARIABLE_EXTERNAL = 12 #: Indicates that a token is an external variable.

_FUNCTION_PREFIX = 'f' #: Indicates that a token starts a function block.
_PARAMETER_PREFIX = 'p' #: Indicates that a token is a function parameter.
_VARIABLE_PREFIX = 'v' #: Indicates that a token is a variable.

_NEGATION_DISABLER = (')', _FUNCTION_PREFIX, _PARAMETER_PREFIX, _VARIABLE_PREFIX) #: Upon reaching these, reset the negation evaluator.
_FUNCTION_DELIMITER = ',' #: Separates function parameters.
_NEGATION_MULTIPLIER = '*' #: Used to ensure negation gets applied first.
_PURE_OPERATORS = ('^', '*', '/', '\\', '%', '+', '-', '<', '>', _NEGATION_MULTIPLIER) #: Perform basic mathematical functions.
_OPERATORS = tuple(list(_PURE_OPERATORS) + ['(', ')']) #: Have significance to the structure of mathematical formulas.
_ALLOWED_TOKENS = tuple(list(_OPERATORS) + [_FUNCTION_DELIMITER]) #: All permitted standalone tokens.
_OPERATOR_PRECEDENCE = {
 _NEGATION_MULTIPLIER: 100,
 '^': 9,
 '*': 8,
 '/': 8,
 '\\': 8,
 '%': 8,
 '+': 6,
 '-': 6,
 '<': 1,
 '>': 1,
 '(': -1,
 ')': 0
} #: The order in which operators should resolve.


#Built-in properties
########################################
_VARIABLES = {
 'e': (_VARIABLE_BUILTIN, math.e),
 'pi': (_VARIABLE_BUILTIN, math.pi),
 '?': (_VARIABLE_BUILTIN, 1j), #Complex number for equation-solver.
} #: Pre-defined variables.

def _generateBuiltinFunctions():
    """
    This function populates the catalogue of built-in calculation functions.
    It is deleted immediately after execution is complete.
    
    All functions it defines take a sequence of numbers on which they will
    operate, returning a computed value when done.
    
    @return: A dictionary keyed by arity of dictionaries that contain
        built-in calculation functions.
    """
    functions = {
    }
    
    def _abs(args):
        return abs(args[0])
    functions[(1, 'abs')] = _abs
    
    def _acos(args):
        return math.acos(args[0])
    functions[(1, 'acos')] = _acos
    
    def _asin(args):
        return math.asin(args[0])
    functions[(1, 'asin')] = _asin
    
    def _atan(args):
        return math.atan(args[0])
    functions[(1, 'atan')] = _atan
    def _atan2(args):
        return math.atan2(args[0], args[1])
    functions[(2, 'atan')] = _atan2
    
    def _ceil(args):
        return int(math.ceil(args[0]))
    functions[(1, 'ceil')] = _ceil
    
    def _cos(args):
        return math.cos(args[0])
    functions[(1, 'cos')] = _cos
    
    def _degrees(args):
        return math.degrees(args[0])
    functions[(1, 'degrees')] = _degrees
    
    def _e(args):
        if args[1] > 9999:
            raise ThresholdError("Exponents have been limited to prevent abuse. e() caps at 9999.")
        return args[0] * (10 ** args[1])
    functions[(2, 'e')] = _e
    
    def _fact(args):
        if args[0] <= 1:
            return 1
        elif args[0] > 100:
            raise ThresholdError("Value passed to fact() (%i) is too large. Use 100 or less." % args[0])
        return reduce(lambda x, y:x*y, xrange(1, args[0] + 1))
    functions[(1, 'fact')] = _fact
    
    def _floor(args):
        return int(math.floor(args[0]))
    functions[(1, 'floor')] = _floor
    
    def _ln(args):
        return math.log(args[0], math.e)
    functions[(1, 'ln')] = _ln
    
    def _log(args):
        return math.log(args[0])
    functions[(1, 'log')] = _log
    def _log2(args):
        return math.log(args[0], args[1])
    functions[(2, 'log')] = _log2
    
    def _ncr(args):
        return (_fact((args[0],)) / (_fact((args[1],)) * _fact((args[0] - args[1],))))
    functions[(2, 'ncr')] = _ncr
    
    def _npr(args):
        return (_fact((args[0],)) / _fact((args[0] - args[1],)))
    functions[(2, 'npr')] = _npr
    
    def _radians(args):
        return math.radians(args[0])
    functions[(1, 'radians')] = _radians
    
    def _random(args):
        return random.random()
    functions[(0, 'random')] = _random
    def _random2(args):
        return random.uniform(args[0], args[1])
    functions[(2, 'random')] = _random2
    
    def _randomint(args):
        return random.randint(args[0], args[1])
    functions[(2, 'randomint')] = _randomint
    
    def _sin(args):
        return math.sin(args[0])
    functions[(1, 'sin')] = _sin
    
    def _sqrt(args):
        if args[0] < 0:
            raise ThresholdError("Imaginary numbers suck. For seriously.")
        return math.sqrt(args[0])
    functions[(1, 'sqrt')] = _sqrt
    
    def _sum(args):
        if abs(args[1] - args[0]) > 999999:
            raise ThresholdError("Sums with over one million possible steps aren't supported.")
        
        if len(args) == 2:
            return sum(range(args[0], args[1] + 1))
            
        if args[2] == 0:
            raise ThresholdError("A sum with a step of 0 will not resolve.")
        dest = args[1]
        if args[2] < 0:
            dest -= 1
        else:
            dest += 1
        return sum(range(args[0], dest, args[2]))
    functions[(2, 'sum')] = _sum
    functions[(3, 'sum')] = _sum
    
    def _tan(args):
        return math.tan(args[0])
    functions[(1, 'tan')] = _tan
    
    return functions
_FUNCTIONS = _generateBuiltinFunctions() #: Pre-defined functions.
del _generateBuiltinFunctions #Remove the no-longer-necessary generator.


#Calculator logic
########################################
def _parseLine(raw_line):
    """
    This function serves as the calculator's lexer, taking an input string and
    converting it into tokens.
    
    This function does not employ any syntaxtic or semantic processing. Rather,
    it just scans the entire string in linear fashion and generates a list of
    tokens that represent the content it received.
    
    It works by first determining which type of expression it is processing,
    extracting any meta-data (such as name and parameters), and then lexing the
    body of the expression.
    
    While lexing, it successively applies the following logic to the remaining
    string::
        - Drop leading whitespace
        - Break if nothing is left
        - Lex token::
            - If numeric, parse and add
            - If a function, add a symbolic reference
            - If a variable, add a symbolic reference
            - If any other valid character, add directly
            
    @type raw_line: basestring
    @param raw_line: The string to be lexed.
    
    @rtype: (list, int)
    @return: A list of all tokens lexed from the input string and a _LINE
        constant that indicates the type of expression parsed.
        
    @raise IllegalCharacterError: If an invalid character is found.
    """
    line = raw_line
    tokens = []
    
    line_type = None
    match = _LINE_SOLVE_LINEAR_REGEXP.match(line)
    if match:
        line_type = _LINE_SOLVE_LINEAR
        tokens.append(_splitLine(match.group(1), raw_line))
        tokens.append(_splitLine(match.group(2), raw_line))
    else:
        match = _LINE_FUNCTION_REGEXP.match(line)
        if match:
            line_type = _LINE_FUNCTION
            tokens.append(match.group(1)) #Add the name.
            tokens.append(match.group(2)) #Add the parameters.
            line = match.group(3)
        else:
            match = _LINE_VARIABLE_REGEXP.match(line)
            if match:
                line_type = _LINE_VARIABLE
                tokens.append(match.group(1)) #Add the name.
                line = match.group(2)
            else:
                line_type = _LINE_EQUATION
        tokens += _splitLine(line, raw_line)
        
    return (tokens, line_type)
    
def _splitLine(line, raw_line):
    tokens = []
    while True:
        line = line.lstrip()
        if not line:
            break
            
        match = _NUMERIC_REGEXP.match(line)
        if match:
            number = match.group(1)
            if number.find('.') == -1:
                tokens.append(int(number))
            else:
                tokens.append(float(number))
        else:
            match = _FUNCTION_REGEXP.match(line)
            if match:
                tokens.append("%s:%s" % (_FUNCTION_PREFIX, match.group(1)))
                tokens.append('(')
            else:
                match = _VARIABLE_REGEXP.match(line) or _QUOTED_VARIABLE_REGEXP.match(line)
                if match:
                    tokens.append("%s:%s" % (_VARIABLE_PREFIX, match.group(1)))
                else:
                    if line[0] in _ALLOWED_TOKENS:
                        tokens.append(line[0])
                    else:
                        raise IllegalCharacterError(raw_line, line[0])
                        
        if match:
            line = line[match.end():]
        else:
            line = line[1:]
    return tokens
    
def _validateExpression(raw_tokens, functions, variables):
    """
    This function performs a semantic check on an expression to make sure that
    it should be computable. At the same time, it compiles symbolic links.
    Additionally, through _validateSyntax(), it performs a syntax check.
    
    It works by replacing symbolic references to variables and functions with
    actual objects. Upon completion, syntax validation is performed.
    
    Nested expressions, such as those passed as arguments to functions, are
    recursively validated.
    
    This function returns a list containing a compiled version of the initial
    input.
    
    @type raw_tokens: list
    @param raw_tokens: The tokenized expression to be validated.
    @type functions: defaultdict
    @param functions: A dictionary of functions, keyed by arity and name.
    @type variables: defaultdict
    @param variables: A dictionary of variables, keyed by name.
        
    @rtype: list
    @return: A compiled version of the initial input.
    
    @raise UnterminatedFunctionError: If a function call is missing its terminal
        parenthesis.
    @raise UnexpectedCharacterError: If a token appears in a position where it
        contradicts the syntactic structure of an expression.
    @raise ConsecutiveFactorError: If two factors appear consecutively.
    @raise ConsecutiveOperatorError: If two operators appear consecutively.
    @raise UnbalancedParenthesesError: If the expression ends without closing
        all parentheses.
    @raise IncompleteExpressionError: If the expression ends while expecting a
        factor.
    @raise VariableError: If a variable was referenced but not found.
    @raise FunctionError: If a function was referenced but not found.
    @raise TokensError: If no tokens are provided for a function's parameter.
    """
    tokens = raw_tokens[:]
    tokens.reverse()
    
    do_negation = True
    last_variable = False
    last_parenthesis = False
    last_factor = False
    expression = []
    
    while tokens:
        token = tokens.pop()
        if isinstance(token, basestring):
            if do_negation and token == '-':
                expression.append(-1)
                expression.append(_NEGATION_MULTIPLIER)
                continue
                
            if token[0] in _NEGATION_DISABLER:
                do_negation = False
            elif token in _OPERATORS:
                do_negation = True
            
            if token[0] == _VARIABLE_PREFIX:
                if last_variable or last_parenthesis or last_factor:
                    expression.append('*')
                expression.append(_validateExpression_variable(raw_tokens, token, variables))
                last_parenthesis = last_factor = False
                last_variable = True
            elif token[0] == _FUNCTION_PREFIX:
                if last_variable or last_parenthesis or last_factor:
                    expression.append('*')
                expression.append(_validateExpression_function(raw_tokens, token, tokens, functions, variables))
                last_parenthesis = last_factor = False
                last_variable = True
            else:
                if token == '(':
                    if last_variable or last_factor:
                        expression.append('*')
                    last_parenthesis = last_variable = last_factor = False
                elif token == ')':
                    last_variable = last_factor = False
                    last_parenthesis = True
                    
                expression.append(token)
                last_parenthesis = last_variable = last_factor = False
        else:
            do_negation = False
            if last_variable or last_parenthesis:
                expression.append('*')
            expression.append(token)
            last_variable = last_parenthesis = False
            last_factor = True
                    
    _validateSyntax(expression, raw_tokens)
    return expression
    
def _validateSyntax(tokens, raw_tokens):
    """
    This function performs the actual process of validating the syntax of an
    expression.
    
    It works by ensuring that factors and operators appear in alternating
    order, with a factor on each end.
    
    Bracketed expressions count as factors if they contain valid content.
    
    @type tokens: list
    @param tokens: The tokenized expression to be evaluated.
    @type raw_tokens: list
    @param raw_tokens: The original tokenized expression.
    
    @raise UnexpectedCharacterError: If a token appears in a position where it
        contradicts the syntactic structure of an expression.
    @raise ConsecutiveFactorError: If two factors appear consecutively.
    @raise ConsecutiveOperatorError: If two operators appear consecutively.
    @raise UnbalancedParenthesesError: If the expression ends without closing
        all parentheses.
    @raise IncompleteExpressionError: If the expression ends while expecting a
        factor.
    """
    expecting_factor = True
    if tokens:
        tokens = tokens[:]
        tokens.reverse()
    else:
        tokens = [0]
        
    while tokens:
        token = tokens.pop()
        if    isinstance(token, basestring):
            if not token in _OPERATORS or token == ')':
                raise UnexpectedCharacterError(token, raw_tokens)
                
            if token == '(': #Check the subexpression.
                if not expecting_factor:
                    raise ConsecutiveFactorError(token, raw_tokens)
                    
                depth = 1
                expression = []
                while tokens:
                    e_token = tokens.pop()
                    if e_token == '(':
                        depth += 1
                    elif e_token == ')':
                        depth -= 1
                        if depth == 0:
                            _validateSyntax(expression, raw_tokens)
                            break
                    expression.append(e_token)
                        
                if depth > 0:
                    raise UnbalancedParenthesesError(raw_tokens)
            elif expecting_factor:
                raise ConsecutiveOperatorError(token, raw_tokens)
        elif not expecting_factor:
            raise ConsecutiveFactorError(token, raw_tokens)
            
        expecting_factor = not expecting_factor
        
    if expecting_factor:
        raise IncompleteExpressionError(raw_tokens)
        
def _validateExpression_variable(raw_tokens, token, variables):
    """
    This function processes an instance of a variable within an expression's
    tokens.
    
    A compiled variable reference is returned.
    
    @type raw_tokens: list
    @param raw_tokens: The original tokenized expression being processed.
    @type token: str
    @param token: The string that identifies which variable is being referenced.
    @type variables: defaultdict
    @param variables: A dictionary of variables, keyed by name.
    
    @rtype: None|tuple
    @return: A tuple of the variable's builtin/custom status, the variable
        or None if not in semantics mode.
        
    @raise VariableError: If the named variable does not exist.
    """
    identifier = token[2:]
    variable = variables[identifier]
    if variable is not None:
        return (identifier in variables and _VARIABLE_CUSTOM or _VARIABLE_EXTERNAL, variable)
        
    variable = _VARIABLES.get(identifier) #Look for a builtin variable.
    if variable is not None:
        return variable
        
    raise VariableError(identifier, raw_tokens)
    
def _validateExpression_function(raw_tokens, token, tokens, functions, variables):
    """
    This function processes an instance of a function within an expression's
    tokens.
    
    A compiled function reference is returned.
    
    @type raw_tokens: list
    @param raw_tokens: The original tokenized expression being processed.
    @type token: str
    @param token: The string that identifies which function is being referenced.
    @type tokens: list
    @param tokens: The tokens remaining in the expression, starting from the
        opening parenthesis of the function's parameter list.
    @type functions: defaultdict
    @param functions: A dictionary of functions, keyed by arity and name.
    @type variables: defaultdict
    @param variables: A dictionary of variables, keyed by name.
    
    @rtype: None|tuple
    @return: A tuple of the function's builtin/custom status, the function
        object, and the function's arguments (a tuple of equations) or None if
        not in semantics mode.
        
    @raise TokensError: If no tokens are provided.
    @raise UnterminatedFunctionError: If a function call is missing its terminal
        parenthesis.
    @raise UnexpectedCharacterError: If a token appears in a position where it
        contradicts the syntactic structure of an expression.
    @raise ConsecutiveFactorError: If two factors appear consecutively.
    @raise ConsecutiveOperatorError: If two operators appear consecutively.
    @raise UnbalancedParenthesesError: If the expression ends without closing
        all parentheses.
    @raise IncompleteExpressionError: If the expression ends while expecting a
        factor.
    @raise FunctionError: If the named function does not exist.
    """
    identifier = token[2:]
    parameters = _validateExpression_parameters(raw_tokens, tokens, identifier, functions, variables)
    arity = len(parameters)
    spec = (arity, identifier)
    
    function = functions[spec]
    if function is not None:
        return (spec in functions and _FUNCTION_CUSTOM or _FUNCTION_EXTERNAL, function, parameters)
        
    function = _FUNCTIONS.get(spec)
    if function is not None:
        return (_FUNCTION_BUILTIN, function, parameters)
        
    raise FunctionError(identifier, arity, tokens)
    
def _validateExpression_parameters(raw_tokens, tokens, function_name, functions, variables):
    """
    This function takes an expression from the start of a function's
    argument list and generates or validates equations for each argument to be
    passed.
    
    A compiled collection of parameters is returned.
    
    @type raw_tokens: list
    @param raw_tokens: The original tokenized expression being processed.
    @type tokens: list
    @param tokens: The tokenized expression being processed.
    @type function_name: str
    @param function_name: The name of the function for which parameters are
        being processed.
    @type functions: defaultdict
    @param functions: A dictionary of functions, keyed by arity and name.
    @type variables: defaultdict
    @param variables: A dictionary of variables, keyed by name.
    
    @rtype: None|tuple
    @return: A tuple of all equations that will serve as function parameters or
        None if not in semantics mode.
        
    @raise TokensError: If no tokens are provided.
    @raise UnterminatedFunctionError: If a function call is missing its terminal
        parenthesis.
    @raise UnexpectedCharacterError: If a token appears in a position where it
        contradicts the syntactic structure of an expression.
    @raise ConsecutiveFactorError: If two factors appear consecutively.
    @raise ConsecutiveOperatorError: If two operators appear consecutively.
    @raise UnbalancedParenthesesError: If the expression ends without closing
        all parentheses.
    @raise IncompleteExpressionError: If the expression ends while expecting a
        factor.
    """
    depth = 1
    parameter = []
    parameters = []
    
    tokens.pop() #Drop the opening parenthesis.
    while tokens:
        token = tokens.pop()
        if token == '(':
            depth += 1
        elif token == ')':
            depth -= 1
            if depth == 0:
                if parameter or parameters: #Allow for 0-arity.
                    equation = Equation(parameter)
                    equation.compile(functions, variables)
                    parameters.append(equation)
                break
        elif depth == 1 and token == _FUNCTION_DELIMITER:
            equation = Equation(parameter)
            equation.compile(functions, variables)
            parameters.append(equation)
            parameter = []
            continue
        parameter.append(token)
        
    if depth > 0:
        raise UnterminatedFunctionError(function_name, raw_tokens)
        
    return tuple(parameters)
        
def _convertRPN(tokens):
    """
    This function converts a valid expression into an RPN token stack.
    
    @type tokens: list
    @param tokens: The tokenized expression to be converted.
    
    @rtype: list
    @return: An RPN token stack representing the given expression.
    
    @raise UnbalancedParenthesesError: If the expression ends without closing
        all parentheses.
    """
    rpn_tokens = []
    stack = []
    sum = 0
    for i in tokens:
        if not i in _OPERATORS:
            rpn_tokens.append(i)
        else:
            if i == '(':
                stack.append(i)
            elif i == ')':
                match_found = False
                while stack:
                    token = stack.pop()
                    if token == '(':
                        match_found = True
                        break
                    else:
                        rpn_tokens.append(token)
                        
                if not match_found:
                    raise UnbalancedParenthesesError(tokens)
            else:
                while stack:
                    if _OPERATOR_PRECEDENCE[i] <= _OPERATOR_PRECEDENCE[stack[-1]]:
                        rpn_tokens.append(stack.pop())
                    else:
                        break
                stack.append(i)
                    
    while stack:
        token = stack.pop()
        if token == '(':
            raise UnbalancedParenthesesError(tokens)
        rpn_tokens.append(token)
        
    return rpn_tokens
    
def _evaluateRPN(tokens, call_stack):
    """
    This function evaluates an RPN-i-fied expression.
    
    Each factor in the token stack is individually evaluated to ensure that
    function and variable values are computed only when needed.
    
    @type tokens: list
    @param tokens: The RPN stack to evaluate.
    @type call_stack: list
    @param call_stack: A stack containing every function and variable traversed
        up to this point.
    
    @rtype: int|float
    @return: The result of the evaluation.
    
    @raise ThresholdError: If the values passed to an operand or function exceed
        pre-defined limits.
    @raise DivisionByZeroError: If a division by zero would occur as a result of
        an operation.
    @raise IncompleteExpressionError: If there are excessive tokens in the input
        stack.
    @raise NullSubexpressionError: If a bracketed expression contains no
        content.
    """
    stack = []
    for i in tokens:
        if i in _PURE_OPERATORS:
            token_right = stack.pop()
            token_left = stack.pop()
            value_right = _evaluate(token_right, call_stack)
            value_left = _evaluate(token_left, call_stack)
            
            if i == '^':
                if value_left > 9999999 or value_right > 1024:
                    raise ThresholdError("The time required to calculate such a power is too great.")
                stack.append(value_left ** value_right)
            elif i in ('*', _NEGATION_MULTIPLIER):
                stack.append(value_left * value_right)
            elif i == '/':
                if value_right == 0:
                    raise DivisionByZeroError(token_left, token_right, ['RPN:'] + tokens)
                    
                stack.append(value_left / float(value_right))
            elif i == '\\':
                if value_right == 0:
                    raise DivisionByZeroError(token_left, token_right, ['RPN:'] + tokens)
                    
                stack.append(int(value_left // value_right))
            elif i == '%':
                stack.append(value_left % value_right)
            elif i == '+':
                stack.append(value_left + value_right)
            elif i == '-':
                stack.append(value_left - value_right)
            elif i == '<':
                stack.append(min(value_left, value_right))
            elif i == '>':
                stack.append(max(value_left, value_right))
        else:
            stack.append(_evaluate(i, call_stack))
            
    if len(stack) > 1:
        raise IncompleteExpressionError(['RPN:'] + tokens)
    if len(stack) < 1:
        raise NullSubexpressionError()
        
    return stack[0]
    
def _evaluate(token, call_stack):
    """
    This function evaluates a token to provide a value processable by the
    computation mechanism.
    
    @type token: int|float|tuple
    @param token: The token to evaluate.
    @type call_stack: list
    @param call_stack: A stack containing every function and variable traversed
        up to this point.
    
    @rtype: int|float
    @return: The value of the token.
    """
    if type(token) == tuple:
        if token[0] == _VARIABLE_CUSTOM:
            return token[1].evaluate(call_stack)
        elif token[0] in (_VARIABLE_BUILTIN, _VARIABLE_EXTERNAL):
            return token[1]
        elif token[0] == _FUNCTION_CUSTOM:
            return token[1].evaluate(token[2], call_stack)
        elif token[0] in (_FUNCTION_BUILTIN, _FUNCTION_EXTERNAL):
            return token[1]([i.evaluate(call_stack) for i in token[2]])
        else:
            raise UnknownTypeError(token)
    return token
    
def _renderExpression(tokens):
    """
    This function provides a mostly-sane, human-readable rendition of the tokens
    that make up an expression processed by the lexer.
    
    @type tokens: list
    @param tokens: The expression to render
    
    @rtype: str
    @return: A rendition of the expression.
    """
    buffer = []
    pad = False
    pad_character = ' '
    for i in tokens:
        if pad and not i in (')', _FUNCTION_DELIMITER):
            buffer.append(pad_character)
            
        if isinstance(i, basestring):
            if i[0] == _FUNCTION_PREFIX:
                i = i[2:]
                pad = False
            elif i[0] == _VARIABLE_PREFIX:
                i = i[2:]
                pad = True
            elif i == '-':
                if len(buffer) >= 2 and buffer[-1] == pad_character and buffer[-2] in _PURE_OPERATORS:
                    pad = False
            else:
                pad = not i == '('
        else:
            if type(i) == tuple:
                if i[0] in (_VARIABLE_CUSTOM, _VARIABLE_EXTERNAL, _VARIABLE_BUILTIN, _FUNCTION_CUSTOM, _FUNCTION_EXTERNAL):
                    i = i[1]
                elif i[0] == _FUNCTION_BUILTIN:
                    i = "%s(%s)" % (i[1].__name__[1:] + ", ".join([str(parameter) for parameter in i[2]]))
            pad = True
            
        buffer.append(str(i))
    return ''.join(buffer)
    
    
#Logical entities
########################################
class Equation(object):
    """
    This class models an equation, which is any expression that can be evaluated
    to produce a numeric value.
    """
    _tokens = None #: The tokens that make up this expression.
    _equation = None #: The expression to be evaluated in RPN, with substitutions.
    
    def __init__(self, tokens):
        """
        This constructs a new Equation.
        
        @type tokens: list
        @param tokens: A list of tokens that represent the expression modeled by
            this equation.
        
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        if not tokens:
            raise TokensError()
            
        self._tokens = tokens
        
    def copy(self):
        """
        Returns a non-compiled copy.
        """
        return Equation(self._tokens)
        
    def compile(self, functions, variables):
        """
        This function compiles this equation, performing semantic validation and
        replacing symbolic function and variable references with object-based
        ones.
        
        When done, this equation will be ready for evaluation.
        
        @type functions: defaultdict
        @param functions: A dictionary of functions, keyed by arity and name.
        @type variables: defaultdict
        @param variables: A dictionary of variables, keyed by name.
        
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        if self._equation: #Already compiled.
            return
            
        if not self._tokens:
            raise TokensError()
            
        self._equation = _convertRPN(_validateExpression(self._tokens, functions, variables))
        
    def evaluate(self, stack=None):
        """
        This function provides the numeric value of this equation.
        
        @type stack: None|list
        @param stack: A stack containing every function and variable traversed
            until this point.
            
        @rtype: int|float
        @return: The value of this equation.
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        if self._equation == None:
            raise CompilationError(self._tokens)
            
        if not stack:
            stack = []
        elif self in stack:
            raise RecursionError(stack + [self])
        stack.append(self)
        
        return _evaluateRPN(self._equation, stack[:])
        
    def getTokens(self):
        return self._tokens
        
    def getRPNTokens(self):
        return self._equation
        
    def __str__(self):
        return _renderExpression(self._tokens)
        
class LinearEquation(Equation):
    _left_side = None
    _right_side = None
    
    def __init__(self, left_side, right_side):
        if not left_side or not right_side:
            raise TokensError()
            
        self._left_side = left_side
        self._right_side = right_side
        self._tokens = ['('] + left_side + [')', '-', '('] + right_side + [')']
        
    def copy(self):
        """
        Returns a non-compiled copy.
        """
        return LinearEquation(self._left_side, self._right_side)
        
    def evaluate(self, stack=None):
        result = Equation.evaluate(self, stack)
        return -result.real/result.imag
        
    def __str__(self):
        return ' '.join((
         _renderExpression(self._left_side),
         '=',
         _renderExpression(self._right_side),
         '|',
         '?',
        ))
        
class Variable(Equation):
    """
    This class models a variable, which is an equation that stores a value for
    later (re-)use.
    """
    _name = None #: The name of this variable.
    _computed_value = None #: The pre-computed value of this variable.
    
    def __init__(self, tokens, name):
        """
        This constructs a new Variable.
        
        @type tokens: list
        @param tokens: A list of tokens that represent the expression modeled by
            this variable.
        @type name: basestring
        @param name: The name of this variable.
        
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        Equation.__init__(self, tokens)
        self._name = name
        
    def copy(self):
        """
        Returns a non-compiled copy.
        """
        return Variable(self._tokens, self._name)
        
    def compute(self, stack=None):
        """
        This function pre-computes the value of this variable, preventing
        redundant when it will be used repeatedly. This function should be
        invoked only when beginning a batch of equations, and it should be
        followed by a call to reset().
        
        @type stack: list
        @param stack: A stack containing every function and variable traversed
            until this point.
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        if not stack:
            stack = []
            
        if self._computed_value == None:
            self._computed_value = Equation.evaluate(self, stack)
            
    def evaluate(self, stack=None, compute=False):
        """
        This function returns the value of this variable, either pre-computed or
        dynamically calculated, depending on status.
        
        @type stack: list
        @param stack: A stack containing every function and variable traversed
            until this point.
        @type compute: bool
        @param compute: If True, the result of evaluating this variable will be
            cached if it has not already been computed.
            
        @rtype: int|float
        @return: The value of this variable.
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        if not stack:
            stack = []
            
        if compute:
            self.compute(stack)
        if self._computed_value:
            return self._computed_value
        else:
            return Equation.evaluate(self, stack)
            
    def reset(self):
        """
        This function clears any pre-computed value from this variable, forcing
        it to be re-evaluated the next time it is used.
        """
        self._computed_value = None
        
    def getName(self):
        return self._name
        
    def __str__(self):
        return "v:%s" % (self._name)
        
class Parameter(Variable):
    """
    This class models a parameter, which is a variable specific to one call to a
    function.
    """
    def __init__(self, name):
        """
        This constructs a new Parameter.
        
        @type name: basestring
        @param name: The name of this variable.
        """
        self._name = name
        
    def copy(self):
        """
        Returns a non-compiled copy.
        """
        return Parameter(self._name)
        
    def assign(self, equation):
        """
        This function assigns a value to this parameter, allowing it to be used
        when the function is called.
        
        @type equation: Equation
        @param equation: The equation attached to this parameter.
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        self._equation = equation.getRPNTokens()
        self.compute()
        
    def unassign(self):
        """
        This function clears the value of this parameter, allowing its values to
        be    removed from the interpreter once they are no longer needed.
        """
        self._equation = None
        self.reset()
        
    def getName(self):
        return self._name
        
    def __str__(self):
        return "p:%s" % (self._name)
        
class Function(Equation):
    """
    This class models a function, which is an equation that requires zero or
    more parameters to produce a result.
    """
    _name = None #: The name of this function.
    _parameters = None #: The names and values of this function's parameters.
    
    def __init__(self, tokens, name):
        """
        This constructs a new Function.
        
        @type tokens: list
        @param tokens: A list of tokens that represent the expression modeled by
            this function.
        @type name: basestring
        @param name: The name of this function.
        
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        Equation.__init__(self, tokens[1:])
        self._name = name
        self._parameters = []
        
        parameters = tokens[0]
        if parameters:
            for i in [j.strip() for j in parameters.split(_FUNCTION_DELIMITER)]:
                self._parameters.append((i, Parameter(i)))
                
    def copy(self):
        """
        Returns a non-compiled copy.
        """
        return Function(self._tokens, self._name)
        
    def compile(self, functions, variables):
        """
        This function compiles this function, extending Equation.compile(),
        which it invokes, with references to function parameters as variables.
        
        @type functions: defaultdict
        @param functions: A dictionary of functions, keyed by arity and name.
        @type variables: defaultdict
        @param variables: A dictionary of variables, keyed by name.
        
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        variables = variables.copy()
        for (name, parameter) in self._parameters:
            variables[name] = parameter
            
        Equation.compile(self, functions, variables)
        
    def evaluate(self, arguments, stack):
        """
        This function provides the numeric value of this function.
        
        It assigns values to all parameters, evaluates the function, and then
        clears the parameters.
        
        @type arguments: tuple
        @param arguments: A tuple of equations that are mapped, in order, to this
            function's parameters.
        @type stack: list
        @param stack: A stack containing every function and variable traversed
            until this point.
        
        @rtype: int|float
        @return: The value of this function.
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        for ((name, parameter), argument) in zip(self._parameters, arguments):
            parameter.assign(argument)
            
        result = Equation.evaluate(self, stack)
        
        for (name, parameter) in self._parameters:
            parameter.unassign()
            
        return result
        
    def getArity(self):
        return len(self._parameters)
        
    def getName(self):
        return self._name
        
    def __str__(self):
        return "f:%s/%i" % (self._name, len(self._parameters))
        
        
class Session(object):
    """
    This class provides a context in which equations may be evaluated. Sessions
    store variables and functions that are needed to support complex equations.
    """
    _variables = None #: A dictionary of all local variables.
    _functions = None #: A dictionary of all local functions.
    _equation = None #: A list of all equations to be evaluated.
    
    def __init__(self, input=None, variable_lookup_handler=None, function_lookup_handler=None):
        """
        This creates a new session.
        
        If any expressions are provided, they will be processed, with appropriate
        entities resulting.
        
        Once all entities have been generated, they will be compiled; handling
        this process in a two-stage manner prevents circular referencing from
        being a problem.
        
        @type input: basestring
        @param input: The variables, functions, and equations with which this
            session will be initialized.
        @type variable_lookup_handler: callable
        @param variable_lookup_handler: A callable that takes a variable-name
            as a basestring and returns a value or None, used to access external
            variables on-demand.
        @type function_lookup_handler: callable
        @param function_lookup_handler: A callable that takes an arity-number
            and function-name as a basestring and returns a value or None, used
            to access external functions on-demand.
            
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        class variables_dict(collections.defaultdict):
            def __missing__(self, key):
                if variable_lookup_handler is not None:
                    return variable_lookup_handler(key)
                return None
                
        class functions_dict(collections.defaultdict):
            def __missing__(self, key):
                if function_lookup_handler is not None:
                    return function_lookup_handler(key[0], key[1])
                return None
                
        self._variables = variables_dict()
        self._functions = functions_dict()
        self._equations = []
        if input:
            for i in input.split(';'):
                (tokens, line_type) = _parseLine(i.strip())
                if tokens:
                    if line_type == _LINE_VARIABLE:
                        name = tokens[0]
                        self._variables[name] = Variable(tokens[1:], name)
                    elif line_type == _LINE_FUNCTION:
                        name = tokens[0]
                        self._functions[(function.getArity(), name)] = Function(tokens[1:], name)
                    elif line_type == _LINE_SOLVE_LINEAR:
                        (left_side, right_side) = tokens
                        self._equations.append(LinearEquation(left_side, right_side))
                    else:
                        self._equations.append(Equation(tokens))
                        
            for function in self._functions.values():
                function.compile(self._functions, self._variables)
                
            for variable in self._variables.values():
                variable.compile(self._functions, self._variables)
                
            for equation in self._equations:
                equation.compile(self._functions, self._variables)
                
    def getVariables(self):
        """
        Returns a dictionary of Variables, keyed by variable name.
        
        @rtype: dict
        @return: A dictionary of Variables, keyed by variable name.
        """
        return self._variables
        
    def listVariables(self):
        """
        This provides a collection of 'name' variable identifiers.
        
        All variables known to this Session will be represented.
        
        @rtype: tuple
        @return: A collection of 'name' variable-identifying strings.
        """
        variables = set(_VARIABLES.keys())
        for name in self._variables.keys():
            variables.add(name)
            
        return tuple(sorted(variables))
        
    def createVariable(self, expression):
        """
        This creates a new variable within the context of this session. However,
        it will not be assigned to this session unless explicitly set with
        setVariable().
        
        @type expression: basestring
        @param expression: The expression used to model this variable.
        
        @rtype: Variable
        @return: The newly created Variable.
        
        @raise InstantiationError: If an invalid expression is provided.
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        if not isinstance(expression, basestring):
            raise InstantiationError("Non-string input")
        (tokens, line_type) = _parseLine(expression)
        if not tokens:
            raise InstantiationError("Nothing expressed")
        if not line_type == _LINE_VARIABLE:
            raise InstantiationError("Not a variable")
            
        variable = Variable(tokens[1:], tokens[0])
        variable.compile(self._functions, self._variables)
        
        return variable
        
    def setVariable(self, variable):
        """
        This adds a new variable to the set of variables known to this Session.
        
        Variables from other sessions may be added, with the results being that
        newly defined entities in the context of this Session will refer to the
        alien variable, which in turn may refer to other alien entities. This
        will probably be meaningless in most cases, however.
        
        @type variable: Variable
        @param variable: The Variable to add.
        
        @raise InstantiationError: If something other than a Variable is
            provided.
        """
        if not type(variable) == Variable:
            raise InstantiationError("Non-Variable input")
            
        self._variables[variable.getName()] = variable
        
    def clearVariable(self, name):
        """
        This function removes the named variable from its namespace, if it
        exists.
        
        @type name: basestring
        @param name: The name of the variable to dereference.
        """
        if self._variables.has_key[name]:
            del self._variables[name]
        
    def getFunctions(self):
        """
        Returns a dictionary of functions keyed by arity and name.
        
        @rtype: dict
        @return: A dictionary of functions keyed by arity and name.
        """
        return self._functions
        
    def listFunctions(self):
        """
        This provides a collection of 'name/arity' function identifiers.
        
        All functions known to this Session will be represented.
        
        @rtype: tuple
        @return: A collection of 'name/arity' function-identifying strings.
        """
        functions = set(['solve/2'])
        for (arity, name) in _FUNCTIONS.keys():
            functions.add("%s/%i" % (name, arity))
            
        for (arity, name) in self._functions.keys():
            functions.add("%s/%i" % (name, arity))
            
        return tuple(sorted(functions))
        
    def createFunction(self, expression):
        """
        This creates a new function within the context of this session. However,
        it will not be assigned to this session unless explicitly set with
        setFunction().
        
        @type expression: basestring
        @param expression: The expression used to model this function.
        
        @rtype: Function
        @return: The newly created Function.
        
        @raise InstantiationError: If an invalid expression is provided.
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        if not isinstance(expression, basestring):
            raise InstantiationError("Non-string input")
        (tokens, line_type) = _parseLine(expression)
        if not tokens:
            raise InstantiationError("Nothing expressed")
        if not line_type == _LINE_FUNCTION:
            raise InstantiationError("Not a function")
            
        function = Function(tokens[1:], tokens[0])
        function.compile(self._functions, self._variables)
        
        return function
        
    def setFunction(self, function):
        """
        This adds a new function to the set of functions known to this Session.
        
        Functions from other sessions may be added, with the results being that
        newly defined entities in the context of this Session will refer to the
        alien function, which in turn may refer to other alien entities. This
        will probably be meaningless in most cases, however.
        
        @type function: Function
        @param function: The Function to add.
        
        @raise InstantiationError: If something other than a Function is
            provided.
        """
        if not type(function) == Function:
            raise InstantiationError("Non-Function input")
            
        self._functions[(function.getArity(), function.getName())] = function
        
    def clearFunction(self, name, arity):
        """
        This function removes the named function from its namespace, if it
        exists.
        
        @type name: basestring
        @param name: The name of the function to dereference.
        @type arity: int
        @param arity: The arity of the function to dereference.
        """
        self._functions.pop((arity, name), None)
        
    def getEquations(self):
        """
        Returns a list of all equations to be evaluated by this Session.
        
        Evaluations will occur in the order of this list.
        
        @rtype: list
        @return: A list of all functions to be evaluated by this Session.
        """
        return self._equations
        
    def createEquation(self, expression):
        """
        This creates a new equation within the context of this session. However,
        it will not be assigned to this session unless explicitly set with
        addEquation().
        
        @type expression: basestring
        @param expression: The expression used to model this equation.
        
        @rtype: Equation
        @return: The newly created Equation.
        
        @raise InstantiationError: If an invalid expression is provided.
        @raise TokensError: If no tokens are provided.
        @raise UnterminatedFunctionError: If a function call is missing its terminal
            parenthesis.
        @raise UnexpectedCharacterError: If a token appears in a position where it
            contradicts the syntactic structure of an expression.
        @raise ConsecutiveFactorError: If two factors appear consecutively.
        @raise ConsecutiveOperatorError: If two operators appear consecutively.
        @raise UnbalancedParenthesesError: If the expression ends without closing
            all parentheses.
        @raise IncompleteExpressionError: If the expression ends while expecting a
            factor.
        """
        if not isinstance(expression, basestring):
            raise InstantiationError("Non-string input")
        (tokens, line_type) = _parseLine(expression)
        if not tokens:
            raise InstantiationError("Nothing expressed")
            
        equation = None
        if line_type == _LINE_EQUATION:
            equation = Equation(tokens)
        elif line_type == _LINE_SOLVE_LINEAR:
            (left_side, right_side) = tokens
            equation = LinearEquation(left_side, right_side)
        else:
            raise InstantiationError("Not an equation")
            
        equation.compile(self._functions, self._variables)
        return equation
        
    def addEquation(self, equation):
        """
        This adds a new equation to the batch of equations to be evaluated by
        this Session.
        
        Equations from other sessions may be added, but the results may be
        meaningless.
        
        @type equation: Equation
        @param equation: The Equation to add.
        
        @raise InstantiationError: If something other than an Equation is
            provided.
        """
        if not type(equation) in (Equation, LinearEquation):
            raise InstantiationError("Non-Equation input")
            
        self._equations.append(equation)
        
    def clearEquation(self, equation):
        """
        This function removes the given equation from its evaluation batch, if it
        exists.
        
        @type equation: Equation
        @param equation: The equation to be removed from this session's
            evaluation batch.
        """
        try:
            self._equations.remove(equation)
        except: pass
        
    def clearEquations(self):
        """
        This function removes all equations from its evaluation batch.
        """
        self._equations = []
        
    def evaluate(self):
        """
        This function evaluates all equations in this session's batch queue.
        
        It returns information about the variables used to perform the
        computations and the results of each equation.
                    
        @rtype: tuple
        @return: A tuple containing two sequences of paired values::
            - The first contains (<name:str>,<value:int|float>) for each variable
            - The second holds (<expression:str>,<result:int|float> per equation
        
        @raise CompilationError: If this equation has not been compiled.
        @raise RecursionError: If this equation has already been invoked during
            the evaluation process.
        @raise ThresholdError: If the values passed to an operand or function exceed
            pre-defined limits.
        @raise DivisionByZeroError: If a division by zero would occur as a result of
            an operation.
        @raise IncompleteExpressionError: If there are excessive tokens in the input
            stack.
        @raise NullSubexpressionError: If a bracketed expression contains no
            content.
        """
        values = []
        for (variable_type, variable) in self._variables.iteritems():
            variable.compute()
            values.append(variable_type, variable.evaluate())
            
        results = [(str(equation), equation.evaluate()) for equation in self._equations]
            
        for variable in self._variables.values():
            variable.reset()
            
        return (tuple(sorted(values)), tuple(results))
        
    def evaluate_equation(self, input):
        """
        This function evaluates a single equation and returns its result. It is
        intended for repeated reuse of initialised variables and functions.
        
        @type input: basestring
        @param input: The equation to be evaluated.
        
        @rtype: number
        @return: The evaluated number.
        """
        return self.extract_equation(input)()
        
    def extract_equation(self, input):
        """
        This function provides a callable that runs through the compilation and
        evaluation steps of an equation on every invocation, allowing for
        internal and external values to change without requiring repeated
        parsing.
        
        @type input: basestring
        @param input: The equation to be evaluated.
        
        @rtype: callable
        @return: A callable that provides a number, requiring no arguments.
        """
        (tokens, line_type) = _parseLine(input.strip())
        if line_type != _LINE_EQUATION:
            raise CompilationError(input)
            
        equation = Equation(tokens)
        def _evaluate(equation):
            equation = equation.copy()
            equation.compile(self._functions, self._variables)
            return equation.evaluate()
        return functools.partial(_evaluate, equation)
        
        
#Exceptions
########################################
class Error(Exception):
    pass
    
class CompilationError(Error):
    _expression = None #: The expression in which the error occurred.
    
    def __init__(self, expression):
        self._expression = expression
        
    def __str__(self):
        return "expression not compiled : %s"  (_renderExpression(self._expression))
    
class ConsecutiveFactorError(Error):
    _token = None #: The offending token.
    _expression = None #: The expression being evaluated.
    
    def __init__(self, token, expression):
        if type(token) == tuple:
            if token[0] == _VARIABLE_BUILTIN:
                for (name, value) in _VARIABLES:
                    if value == token:
                        self._token = name
                        break
            elif token[0] == _FUNCTION_BUILTIN:
                self._token = token[1].__name__
            elif token[0] in (_VARIABLE_CUSTOM, _VARIABLE_EXTERNAL, _FUNCTION_CUSTOM, _FUNCTION_EXTERNAL):
                self._token = token[1]
                
        else:
            self._token = token
            
        if not self._token:
            self._token = 'unknown'
        self._expression = expression
        
    def __str__(self):
        return "expected operator, not '%s' : %s" % (self._token, _renderExpression(self._expression))
        
class ConsecutiveOperatorError(Error):
    _token = None #: The offending token.
    _expression = None #: The expression being evaluated.
    
    def __init__(self, token, expression):
        self._token = token
        self._expression = expression
        
    def __str__(self):
        return "expected factor, not '%s' : %s" % (self._token, _renderExpression(self._expression))
        
class DivisionByZeroError(Error):
    _value_left = None #: The value being divided.
    _value_right = None #: The value that is equal to 0.
    _expression = None #: The expression being evaluated.
    
    def __init__(self, value_left, value_right, expression):
        self._value_left = value_left
        self._value_right = value_right
        self._expression = expression
        
    def __str__(self):
        return "division by 0 (%s/%s) : %s" % (self._value_left, self._value_right, _renderExpression(self._expression))
        
class FunctionError(Error):
    _name = None #: The name of the function being referenced.
    _arity = None #: The arity being requested.
    _expression = None #: The expression in which the error occurred.
    
    def __init__(self, name, arity, expression):
        self._name = name
        self._arity = arity
        self._expression = expression
        
    def __str__(self):
        return "function '%s/%i' does not exist : %s" % (self._name, self._arity, _renderExpression(self._expression))
        
class IllegalCharacterError(Error):
    _line = None #: The line that contained the error.
    _character = None #: The offending character.
    
    def __init__(self, line, character):
        self.line = line
        self.character = character
        
    def __str__(self):
        return "illegal character '%s' : '%s'" % (self.character, self.line)
        
class IncompleteExpressionError(Error):
    _expression = None #: The expression being evaluated.
    
    def __init__(self, expression):
        self._expression = expression
        
    def __str__(self):
        return "missing terminal factor : %s" % (_renderExpression(self._expression))
        
class InstantiationError(Error):
    _reason = None #: The reason why this error occurred.
    
    def __init__(self, reason):
        self._reason = reason
        
    def __str__(self):
        return "unable to instantiate expression : %s" % (self._reason)
        
class NullSubexpressionError(Error):
    def __str__(self):
        return "null factor : '()'"
        
class RecursionError(Error):
    _stack = None #: The function stack that led to this error.
    
    def __init__(self, stack):
        self._stack = stack
        
    def __str__(self):
        buffer = []
        for i in self._stack:
            buffer.append(str(i))
        buffer.append(')' * len(self._stack))
        return "recursive trace: %s" % ('('.join(buffer))
        
class ThresholdError(Error):
    _message = None #: The description of this error.
    
    def __init__(self, message):
        self._message = message
        
    def __str__(self):
        return "calculation too expensive : %s" % (self._message)
        
class TokensError(Error):
    def __str__(self):
        return "no expression to model"
        
class UnbalancedParenthesesError(Error):
    _expression = None #: The expression being evaluated.
    
    def __init__(self, expression):
        self._expression = expression
        
    def __str__(self):
        return "unbalanced parentheses : %s" % (_renderExpression(self._expression))
        
class UnexpectedCharacterError(Error):
    _token = None #: The offending token.
    _expression = None #: The expression being evaluated.
    
    def __init__(self, token, expression):
        self._token = token
        self._expression = expression
        
    def __str__(self):
        return "unexpected character '%s' : %s" % (self._token, _renderExpression(self._expression))
        
class UnknownTypeError(Error):
    _token = None #: The token that caused this error.
    
    def __init__(self, token):
        self._token = token
        
    def __str__(self):
        return "unknown type : %s" % (self._token)
        
class UnterminatedFunctionError(Error):
    _name = None #: The name of the variable being referenced.
    _expression = None #: The expression in which the error occurred.
    
    def __init__(self, name, expression):
        self._name = name
        self._expression = expression
        
    def __str__(self):
        return "missing ')' on %s : %s" % (self._name, _renderExpression(self._expression))
        
class VariableError(Error):
    _name = None #: The name of the variable being referenced.
    _expression = None #: The expression in which the error occurred.
    
    def __init__(self, name, expression):
        self._name = name
        self._expression = expression
        
    def __str__(self):
        return "variable '%s' does not exist : %s" % (self._name, _renderExpression(self._expression))
        
        
#Debuging interface
########################################
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        print "Nothing to computate. :("
    else:
        for i in sys.argv[1:]:
            session = Session(i)
            (variables, equations) = session.evaluate()
            
            if equations:
                if variables:
                    print "Variables:"
                    for (name, value) in variables:
                        print "\t%s = %s" % (name, value)
                    print
                print "Equations:"
                for (equation, value) in equations:
                    print "\t%s = %s" % (equation, value)
            else:
                print "No expressions provided."
            print '-' * 40 + '\n'
            
