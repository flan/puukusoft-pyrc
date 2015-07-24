PyRC was, and is, [Puukusoft](http://uguu.ca/projects/puukusoft/)'s first [Python](http://www.python.org/)-based project, initially undertaken as a means of learning the language back during the dark 1.x days.

PyRC is developed exclusively against [Debian](http://www.debian.org/)-[based](http://www.ubuntu.com/) [GNU](http://www.gnu.org/)/[Linux](http://www.kernel.org/) systems, although, by the time 1.0 is released, it should support whatever operating systems still exist.


---

# Overview #
Since its inception, PyRC has been a project that has been very slow to evolve. It is prone to long periods of "going nowhere" while receiving extensive amounts of work. This paradox is explainable only by likening it to a development testbed, for that is what it has become.

In essence, PyRC itself is fundamentally complete: it's stable, feature-rich, extensively documented, and needs only bindings to complete its support of the current IRC protocol. However, it is not an IRC client. Rather, it is an IRC client _framework_: a structure to which other components may be affixed to create an IRC-based client-like entity that realizes the developer's imagination.

Because of this, PyRC's primary incarnation has evolved as a bot (although it is more capable, design-wise, than contemporary clients, such as [irssi](http://www.irssi.org) and [XChat](http://www.xchat.org)), and its learning-related innovative potential has been tapped through the creation of modules that may be exposed to IRC users: things ranging from extensive calculators to database scrapers to social profilers to Turing-test prototype ideas, to say nothing of the fact that it has been rewritten in its entirety more than a dozen times as new Pythonic idioms and innovative software development techniques have been learned, to allow us to hone our skills and better our refactoring techniques.

Ultimately, PyRC cannot be classified. It cannot be declared "finished". It is fated to forever remain a work-in-progress, endlessly evolving into a more pure form of itself, yet growing nowhere. (Every hacker has to have an eternal pet project, after all)


---

# PyRC's potential #
PyRC is a completely modular system -- so modular that, without at least one plugin, a head for manipulation, it does absolutely nothing. This approach has pros and cons, although the pros greatly outweigh the cons from a development perspective:
  * Cons:
    * Useless without investment of work
    * Must be configured to be usable
    * No deployment standardization
  * Pros:
    * A little bit of work, in pure Python with an **entirely** decoupled API, allows _anything_ to be done
      * The nature of PyRC's API does not cause scripts to become dependent on interactions with an imported module; rather, they have access to an input source and an output sink, which can be ignored or redirected to allow for standalone use
    * Configuration may happen however the developer wills it, allowing for absolute control over the system's behaviour
    * No deployment standardization
      * If you want a GUI, you can have it; if you prefer terminals, that's fine, too; if you want to use a neural interface, that's just as doable
      * If you don't care about DCCs, don't load the module; if you can't live without an RSS feed in every window, add a handler

The goal of the project is to enable everything and hinder nothing. Lofty, yes, but it wouldn't be an entertaining learning experience otherwise.

Additionally, starting with 0.2.0, all API extensions are intended to be backwards-compatible with existing modules: nothing should ever be left behind because it is too old, and the API should never feel cluttered or redundant because of legacy support.


---

# Notable plugins #
Although PyRC includes a large number of [plugins](plugins.md), the following are projects unto themselves: modules that can stand alone, be integrated into another unrelated project, or simply warrant an article of their own:
  * [Calculator](Calculator.md) : A full-featured calculator, capable of everything from solving 1 + 1 to storing sessional variables and user-defined functions to quickly resolving linear equations


---

# Using PyRC #
PyRC, being forever beta, has had no formal releases. However, that does not mean the code is not stable. Everything you should need for development purposes can be found in the repository and at the following locations:
  * [Core documentation](http://static.uguu.ca/projects/puukusoft/PyRC/api/)
  * [Dictionary reference](http://static.uguu.ca/projects/puukusoft/PyRC/dictionaries/) (event-flow API)


---

# Project information #
## Development plans ##
A a means of increasing familiarity with Python 3.x, PyRC will evolve until it reaches 0.3.0, which should transparently afford support for all remaining important IRC protocol features to plugin developers.

Additionally, newer Python techniques and idiomatic practices will be incorporated and documented, making PyRC an even better reference for learning.


---

# Feedback #
If you use PyRC, let us know. It's a fun project to hack on, but having expectations would greatly help to focus development efforts.


---

# Credits #
[Neil Tallim](http://uguu.ca/)
  * Programming, documentation


---

# Contacts #
red {dot} hamsterx {at} gmail