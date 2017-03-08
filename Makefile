#!/usr/bin/make

default:
	echo "There is nothing to do."
test:
	@./PerceptionMD.py perception-md/unittests/travis-example.md
	@textx check perception.tx perception-md/unittests/travis-example.md
	@textx visualize perception.tx perception-md/unittests/travis-example.md >/dev/null
	@ls
	@dot -Tpng -O perception-md/unittests/perception.tx.dot
	@dot -Tpng -O perception-md/unittests/travis-example.md.dot
