#! /usr/bin/python
# -*- coding: utf-8 -*-
import unittest
import math

import calc

class ComputationTest(unittest.TestCase):
	_session = None #: An instance of calc.Session.
	_session_full = None #: An instance of calc.Session.
	
	def setUp(self):
		"""
		This creates two sessions: one that takes a string of input in its
		constructor, and one that loads the same information (in an acceptable
		order). They should both behave identically.
		"""
		self._session_full = calc.Session(
		 ''.join([
		  "b = 2; a = 1; c = a + b; d = g(c); f = g(c, 5); g = h();",
		  "g(a) = a b; g(x, y) = x + y; h() = ceil(4.009);",
		  "g(a + b + c + d + f + 10.007 - e, h()); 77(b) - 22b; g(-c); g(g(g(2)));",
		  "solve((0.6? - 5) / ?, 0.54)"
		 ])
		)
		
		self._session = calc.Session()
		self._session.setVariable(self._session.createVariable("b = 2"))
		self._session.setVariable(self._session.createVariable("a = 1"))
		self._session.setVariable(self._session.createVariable("c = a + b"))
		self._session.setFunction(self._session.createFunction("g(a) = a b"))
		self._session.setVariable(self._session.createVariable("d = g(c)"))
		self._session.setFunction(self._session.createFunction("g(x, y) = x + y"))
		self._session.setVariable(self._session.createVariable("f = g(c, 5)"))
		self._session.setFunction(self._session.createFunction("h() = ceil(4.009)"))
		self._session.setVariable(self._session.createVariable("g = h()"))
		self._session.addEquation(self._session.createEquation("g(a + b + c + d + f + 10.007 - e, h())"))
		self._session.addEquation(self._session.createEquation("77(b) - 22b"))
		self._session.addEquation(self._session.createEquation("g(-c)"))
		self._session.addEquation(self._session.createEquation("g(g(g(2)))"))
		self._session.addEquation(self._session.createEquation("solve((0.6? - 5) / ?, 0.54)"))
		
	def testLexer(self):
		"""
		This test ensures that the more primitive logic of the lexer is working
		as intended -- that is to say that it ensures that negation is properly
		enforced and that parentheses work properly.
		"""
		self.assertEquals(self._session.createEquation("1").evaluate(), 1)
		self.assertEquals(self._session.createEquation("100").evaluate(), 100)
		self.assertEquals(self._session.createEquation("-1").evaluate(), -1)
		self.assertEquals(self._session.createEquation("-100").evaluate(), -100)
		self.assertEquals(self._session.createEquation("0.5").evaluate(), 0.5)
		self.assertEquals(self._session.createEquation("-0.5").evaluate(), -0.5)
		self.assertEquals(self._session.createEquation(".5").evaluate(), 0.5)
		self.assertEquals(self._session.createEquation("-.5").evaluate(), -0.5)
		
		self.assertEquals(self._session.createEquation("1 - (1)").evaluate(), 0)
		self.assertEquals(self._session.createEquation("-1 - (-1)").evaluate(), 0)
		self.assertEquals(self._session.createEquation("1-(-(-1))").evaluate(), 0)
		self.assertEquals(self._session.createEquation("-1-(-(-1))").evaluate(), -2)
		self.assertEquals(self._session.createEquation("1 - ---1").evaluate(), 2)
		self.assertEquals(self._session.createEquation("1 - --1").evaluate(), 0)
		
		self.assertEquals(self._session.createEquation("-1-(-(-1 + 1 + 1 * 5))").evaluate(), 4)
		
	def testOperators(self):
		"""
		This test provides a more thorough test of the lexer, ensuring that it
		properly handles every operator the calculator knows about.
		"""
		self.assertEquals(self._session.createEquation("10 - 33").evaluate(), -23)
		self.assertEquals(self._session.createEquation("10 - -33").evaluate(), 43)
		self.assertEquals(self._session.createEquation("10 + --33").evaluate(), 43)
		self.assertEquals(self._session.createEquation("10 + 6").evaluate(), 16)
		self.assertEquals(self._session.createEquation("10 % 3").evaluate(), 10 % 3)
		self.assertEquals(self._session.createEquation("10/5").evaluate(), 2)
		self.assertEquals(self._session.createEquation("10/3").evaluate(), float(10)/3)
		self.assertEquals(self._session.createEquation("10\\3").evaluate(), 10/3)
		self.assertEquals(self._session.createEquation("5 * 5").evaluate(), 25)
		self.assertEquals(self._session.createEquation("1 > 2").evaluate(), 2)
		self.assertEquals(self._session.createEquation("10^2").evaluate(), 100)
		self.assertEquals(self._session.createEquation("1 < 2").evaluate(), 1)
		self.assertEquals(self._session.createEquation("1 > 2").evaluate(), 2)
		
	def testBuiltInVariables(self):
		"""
		This test runs through every built-in variable the calculator knows about
		and ensures that a compiled expression consisting of each one will
		produce a correct value.
		"""
		self.assertEquals(self._session.createEquation("e").evaluate(), math.e)
		self.assertEquals(self._session.createEquation("pi").evaluate(), math.pi)
		
	def testBuiltInFunctions(self):
		"""
		This test runs through every built-in function the calculator knows
		about	and ensures that a compiled expression consisting of each one will
		produce a correct value.
		"""
		self.assertEquals(self._session.createEquation("abs(-1)").evaluate(), abs(-1))
		self.assertEquals(self._session.createEquation("acos(-1)").evaluate(), math.acos(-1))
		self.assertEquals(self._session.createEquation("asin(-1)").evaluate(), math.asin(-1))
		self.assertEquals(self._session.createEquation("atan(-1)").evaluate(), math.atan(-1))
		self.assertEquals(self._session.createEquation("atan(-1, -1)").evaluate(), math.atan2(-1, -1))
		self.assertEquals(self._session.createEquation("ceil(0.1)").evaluate(), math.ceil(0.1))
		self.assertEquals(self._session.createEquation("cos(-1)").evaluate(), math.cos(-1))
		self.assertEquals(self._session.createEquation("deg(-1)").evaluate(), math.degrees(-1))
		self.assertEquals(self._session.createEquation("e(1.46, 2)").evaluate(), 146)
		self.assertEquals(self._session.createEquation("fact(5)").evaluate(), 120)
		self.assertEquals(self._session.createEquation("floor(1.9)").evaluate(), math.floor(1.9))
		self.assertEquals(self._session.createEquation("ln(5)").evaluate(), math.log(5, math.e))
		self.assertEquals(self._session.createEquation("log(5)").evaluate(), math.log(5))
		self.assertEquals(self._session.createEquation("log(5, 2)").evaluate(), math.log(5, 2))
		self.assertEquals(self._session.createEquation("ncr(5, 2)").evaluate(), 10)
		self.assertEquals(self._session.createEquation("npr(5, 2)").evaluate(), 20)
		self.assertEquals(self._session.createEquation("rad(-1)").evaluate(), math.radians(-1))
		self.assertEquals(type(self._session.createEquation("rnd()").evaluate()), float)
		self.assertEquals(type(self._session.createEquation("rnd(1, 10)").evaluate()), float)
		self.assertEquals(type(self._session.createEquation("rndint(1, 6)").evaluate()), int)
		self.assertEquals(self._session.createEquation("sin(-1)").evaluate(), math.sin(-1))
		self.assertEquals(self._session.createEquation("sqrt(16)").evaluate(), 4)
		self.assertEquals(self._session.createEquation("sum(1, 5)").evaluate(), 15)
		self.assertEquals(self._session.createEquation("sum(1, 5, 2)").evaluate(), 9)
		self.assertEquals(self._session.createEquation("tan(-1)").evaluate(), math.tan(-1))
		self.assertEquals(self._session.createEquation("solve(5 - ?, 1)").evaluate(), 4)
		
	def testVariables(self):
		"""
		This test ensures that every variable within the sessions reports the
		proper value.
		"""
		variables = self._session.getVariables()
		variables_full = self._session_full.getVariables()
		
		self.assertEquals(variables['a'].evaluate(), 1)
		self.assertEquals(variables_full['a'].evaluate(), 1)
		self.assertEquals(variables['b'].evaluate(), 2)
		self.assertEquals(variables_full['b'].evaluate(), 2)
		self.assertEquals(variables['c'].evaluate(), 3)
		self.assertEquals(variables_full['c'].evaluate(), 3)
		self.assertEquals(variables['d'].evaluate(), 6)
		self.assertEquals(variables_full['d'].evaluate(), 6)
		self.assertEquals(variables['f'].evaluate(), 8)
		self.assertEquals(variables_full['f'].evaluate(), 8)
		self.assertEquals(variables['g'].evaluate(), 5)
		self.assertEquals(variables_full['g'].evaluate(), 5)
		
	def testFunctions(self):
		"""
		This test ensures that every function within the sessions reports proper
		values.
		"""
		self.assertEquals(self._session.createEquation("g(1)").evaluate(), 2)
		self.assertEquals(self._session_full.createEquation("g(1)").evaluate(), 2)
		self.assertEquals(self._session.createEquation("g(-3)").evaluate(), -6)
		self.assertEquals(self._session_full.createEquation("g(-3)").evaluate(), -6)
		self.assertEquals(self._session.createEquation("g(1, 3)").evaluate(), 4)
		self.assertEquals(self._session_full.createEquation("g(1, 3)").evaluate(), 4)
		self.assertEquals(self._session.createEquation("g(-3, -1)").evaluate(), -4)
		self.assertEquals(self._session_full.createEquation("g(-3, -1)").evaluate(), -4)
		self.assertEquals(self._session.createEquation("h()").evaluate(), 5)
		self.assertEquals(self._session_full.createEquation("h()").evaluate(), 5)
		
	def testEquations(self):
		"""
		This test ensures that the result of evaluating the session is consistent
		with expectations.
		"""
		(variables, equations) = self._session.evaluate()
		(variables_full, equations_full) = self._session_full.evaluate()
		
		self.assertEquals(variables[0], ('a', 1))
		self.assertEquals(variables_full[0], ('a', 1))
		self.assertEquals(variables[1], ('b', 2))
		self.assertEquals(variables_full[1], ('b', 2))
		self.assertEquals(variables[2], ('c', 3))
		self.assertEquals(variables_full[2], ('c', 3))
		self.assertEquals(variables[3], ('d', 6))
		self.assertEquals(variables_full[3], ('d', 6))
		self.assertEquals(variables[4], ('f', 8))
		self.assertEquals(variables_full[4], ('f', 8))
		self.assertEquals(variables[5], ('g', 5))
		self.assertEquals(variables_full[5], ('g', 5))
		
		self.assertEquals(equations[0][1], 35.007 - math.e)
		self.assertEquals(equations_full[0][1], 35.007 - math.e)
		self.assertEquals(equations[1][1], 110)
		self.assertEquals(equations_full[1][1], 110)
		self.assertEquals(equations[2][1], -6)
		self.assertEquals(equations_full[2][1], -6)
		self.assertEquals(equations[3][1], 16)
		self.assertEquals(equations_full[3][1], 16)
		
	def testErrors(self):
		"""
		This test runs through a list of scenarios that should trigger errors,
		failing if one gets through.
		"""
		try:
			self._session.createEquation("5 + 66 2 + 12")
			self.fail("No error generated. Expected %s." % (calc.ConsecutiveFactorError.__class__.__name__))
		except calc.ConsecutiveFactorError, e: pass
		
		try:
			self._session.createEquation("5 -+ 6 + 8")
			self.fail("No error generated. Expected %s." % (calc.ConsecutiveOperatorError.__class__.__name__))
		except calc.ConsecutiveOperatorError, e: pass
		
		try:
			self._session.createEquation("66 / 0").evaluate()
			self.fail("No error generated. Expected %s." % (calc.DivisionByZeroError.__class__.__name__))
		except calc.DivisionByZeroError, e: pass
		
		try:
			self._session.createEquation("fake_function(1, 2, 3)")
			self.fail("No error generated. Expected %s." % (calc.FunctionError.__class__.__name__))
		except calc.FunctionError, e: pass
		
		try:
			self._session.createEquation("5 + '6 * 10")
			self.fail("No error generated. Expected %s." % (calc.IllegalCharacterError.__class__.__name__))
		except calc.IllegalCharacterError, e: pass
		
		try:
			self._session.createEquation("6 + (55) + 17 -")
			self.fail("No error generated. Expected %s." % (calc.IncompleteExpressionError.__class__.__name__))
		except calc.IncompleteExpressionError, e: pass
		
		try:
			self._session.createEquation(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createVariable(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createFunction(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createEquation("")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createVariable("")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createFunction("")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createEquation("x = 5")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createVariable("g(x, y) = x + y")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.createFunction("77 + 12")
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.addEquation(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.setVariable(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		try:
			self._session.setFunction(None)
			self.fail("No error generated. Expected %s." % (calc.InstantiationError.__class__.__name__))
		except calc.InstantiationError, e: pass
		
		try:
			self._session.createEquation("()").evaluate()
			self.fail("No error generated. Expected %s." % (calc.NullSubexpressionError.__class__.__name__))
		except calc.NullSubexpressionError, e: pass
		
		session = calc.Session("g = 67q; q = 5g; x(y, z)= 2 x(y, z)")
		try:
			session.createEquation("g").evaluate()
			self.fail("No error generated. Expected %s." % (calc.RecursionError.__class__.__name__))
		except calc.RecursionError, e: pass
		try:
			session.createEquation("x(1, 2)").evaluate()
			self.fail("No error generated. Expected %s." % (calc.RecursionError.__class__.__name__))
		except calc.RecursionError, e: pass
		
		try:
			self._session.createEquation("75^2048").evaluate()
			self.fail("No error generated. Expected %s." % (calc.ThresholdError.__class__.__name__))
		except calc.ThresholdError, e: pass
		
		try:
			self._session.createEquation("6 + ((55) + 17")
			self.fail("No error generated. Expected %s." % (calc.UnbalancedParenthesesError.__class__.__name__))
		except calc.UnbalancedParenthesesError, e: pass
		
		try:
			self._session.createEquation("6 + ((55) + 17")
			self.fail("No error generated. Expected %s." % (calc.UnbalancedParenthesesError.__class__.__name__))
		except calc.UnbalancedParenthesesError, e: pass
		
		try:
			self._session.createEquation("5 + )")
			self.fail("No error generated. Expected %s." % (calc.UnexpectedCharacterError.__class__.__name__))
		except calc.UnexpectedCharacterError, e: pass
		
		try:
			self._session.createEquation("5, + 66")
			self.fail("No error generated. Expected %s." % (calc.UnexpectedCharacterError.__class__.__name__))
		except calc.UnexpectedCharacterError, e: pass
		
		try:
			self._session.createEquation("fake_function(1, 2, 3")
			self.fail("No error generated. Expected %s." % (calc.UnterminatedFunctionError.__class__.__name__))
		except calc.UnterminatedFunctionError, e: pass
		
		try:
			self._session.createEquation("fake_variable")
			self.fail("No error generated. Expected %s." % (calc.VariableError.__class__.__name__))
		except calc.VariableError, e: pass
		
		
test_computation = unittest.main()
