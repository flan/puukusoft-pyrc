# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.C_FUNCS

Purpose
=======
 Store stateless functions that are needed by several modules in PyRC, thereby
 preventing code duplication.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2006-2007
"""
import GLOBAL

#Functions
#==============================================================================
def evaluateTruth(string_in):
	"""
	This function is used to evaluate a user-provided string, like a value in a
	configuration file, to find out whether it has a boolean value of True or
	not.
	
	@type string_in: basestring|None
	@param string_in: The string to be tested.
	
	@rtype: bool
	@return: True if the string has a boolean value of True; False otherwise.
	"""
	if not string_in:
		return False
	return string_in.lower() in GLOBAL.PTN_TRUTH
	
def padInteger(value, target_length, fail_on_excessive_length=True):
	"""
	This function prepends '0's to integers if they are less than the target
	length.
	
	@type value: int
	@param value: The integer to be padded.
	@type target_length: int
	@param target_length: The length the returned integer should be.
	@type fail_on_excessive_length: bool
	@param fail_on_excessive_length: If True, an error will be raised if the
	    given integer is longer than its target.
	
	@rtype: string
	@return: A '0'-padded version of the given integer.
	
	@raise ValueError: If the given integer is longer than the target length and
	    fail_on_excessive_length is set.
	"""
	value = str(value)
	pad_number = target_length - len(value)
	
	if pad_number < 0 and fail_on_excessive_length:
		raise ValueError("Unable to pad integer: length of '%s' exceeds target length (%i)" % (value, target_length))
	elif pad_number > 0:
		value = ('0' * pad_number) + value
		
	return value
	
def pluralizeQuantity(value, singular, alt_plural=None):
	"""
	This function returns the appropriate pluralization for a quantity.
	
	If the quantity is 1, the basic type is returned; if the quantity is not 1,
	the plural form of the type is returned.
	
	@type value: int
	@param value: The quantity to be evaluated.
	@type singular: basestring
	@param singular: The singular form of the term under evaluation.
	@type alt_plural: basestring|None
	@param alt_plural: The plural form of the term under evaluation. This may be
	    omitted if a simple 's'-append will work on the singular form.
	
	@rtype: basestring
	@return: The correct quantity string for the given type.
	"""
	if value != 1:
		if alt_plural:
			return alt_plural
		else:
			return singular + 's'
	return singular
	