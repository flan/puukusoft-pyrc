__module_data__={
 'name': "Calculator",
 'version': 1.0,
 'author': "Neil Tallim",
 'e-mail': "red.hamsterx@gmail.com",
 'version string': "1.0.0"
}

import re

import calc

import pyrc_shared.convenience as pyrc

_CALC_REGEXP = re.compile("^!calc (.+)", re.I)

_ALLOWED_SOURCES = {
 'synIRC': (
  '#o.o',
  '#utc!',
 )
}

def loadMe(ial, load_mode):
	return (
	 ("Channel Message", processChannelMessage, False),
	 ("Channel Message Local", processChannelMessage, False)
	)
	
def unloadMe(ial, unload_mode):
	pass
	
def processChannelMessage(dictionary, ial):
	if not pyrc.handleChannelMessage(dictionary, _ALLOWED_SOURCES):
		return
		
	match = _CALC_REGEXP.match(dictionary['message'])
	if match:
		message = match.group(1).lower()
		if message == 'list':
			session = calc.Session()
			pyrc.respondToChannelMessage("Built-ins: %s | %s" % (', '.join(session.listFunctions()), ', '.join(session.listVariables())), dictionary)
		elif message == 'help':
			pyrc.respondToChannelMessage("Usage: '!calc <variable|function|equation>[;...]|list' Order does not matter.", dictionary)
		else:
			try:
				session = calc.Session(str(match.group(1)))
				(variables, equations) = session.evaluate()
				
				if equations:
					for (equation, value) in equations:
						try:
							i_value = int(value)
							if i_value == value:
								value = i_value
						except:
							pass
						pyrc.respondToChannelMessage("%s = %s" % (equation, value), dictionary)
				else:
					pyrc.respondToChannelMessage("No expressions provided.", dictionary)
			except calc.Error, e:
				pyrc.respondToChannelMessage("%s: %s" % (e.__class__.__name__, e), dictionary)
			except Exception, e:
				pyrc.respondToChannelMessage("%s: %s" % (e.__class__.__name__, e), dictionary)
				
