PyRC's Calculator module is a solution to the problem of often wanting to crunch some numbers without being willing to launch another program.


---

# Overview #
The Calculator module works by first establishing a session -- a context in which all calculations are to take place. Sessions are relevant because they hold user-defined variables and functions.

When given input, the Calculator module automatically parses the string into function and variable definitions -- first resolving variable values, then compiling functions -- and then evaluates every given equation in sequence. (As a consequence, the order of specification is irrelevant -- variables can come at the end, and they'll still be mapped properly)

A large number of built-in functions and variables are available, though they may be overridden by user-defined entities.


---

# Usage #
Both user-friendly and programmer-friendly interfaces exist. For examples of using both methods, see the unit tests in `plugins/Calculator/tests.py`

If you want to integrate the Calculator in your own project, look at its [API documentation](http://static.uguu.ca/projects/puukusoft/PyRC/plugins/Calculator/api/).


---

# Getting the code #
The Calculator is available as part of the standard PyRC distribution: `plugins/Calculator/`


---

# Project information #
## Development plans ##
This module is tentatively final.


---

# Credits #
[Neil Tallim](http://uguu.ca/)
  * Programming