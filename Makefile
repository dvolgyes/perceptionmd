#!/usr/bin/make

default:
	echo "There is nothing to do."
test:
	@./PerceptionMD.py perception-md/unittests/travis-example.md

graph:
	@textx check perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.md
	@textx visualize perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.md >/dev/null
	@dot -Tpng -O perceptionmd/lang/perception.tx.dot
	@dot -Tpng -O perceptionmd/unittests/travis-example.md.dot
