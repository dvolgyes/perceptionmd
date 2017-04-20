#!/usr/bin/make

ifndef COVERAGE
COVERAGE=python$(PYVERSION) -m coverage
endif

default:
	echo "There is nothing to do."
test:
	(./input.sh &)
	$(COVERAGE) erase
	$(COVERAGE) run --parallel-mode --source perceptionmd perceptionmd/utils/utils.py
	$(COVERAGE) run --parallel-mode --source perceptionmd perceptionmd/utils/rev_eng.py perceptionmd/examples/simple/rawtest/A.raw
	$(COVERAGE) run --parallel-mode --source perceptionmd perceptionmd/utils/rev_eng.py perceptionmd/examples/simple/rawtest/A_9_512_512.raw
	$(COVERAGE) run --parallel-mode --source perceptionmd perceptionmd/utils/Log.py
	$(COVERAGE) run --parallel-mode --concurrency=thread --source perceptionmd ./PerceptionMD.py
	$(COVERAGE) run --parallel-mode --concurrency=thread --source perceptionmd ./PerceptionMD.py perceptionmd/unittests/travis-example.pmd
	$(COVERAGE) run --parallel-mode --concurrency=thread --source perceptionmd ./PerceptionMD.py perceptionmd/examples/simple/simple.pmd
	$(COVERAGE) combine

graph:
	@textx check perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.pmd
	@textx visualize perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.pmd >/dev/null
	@dot -Tpng -O perceptionmd/lang/perception.tx.dot
	@dot -Tpng -O perceptionmd/unittests/travis-example.pmd.dot

ico:
	@inkscape -z perceptionmd.svg -w 128 -h 128 -e perceptionmd.png
	@convert perceptionmd.png -define icon:auto-resize=64,48,32,16 perceptionmd.ico
	@convert perceptionmd.png -stroke red -strokewidth 12 -draw "line 0 0 127 127, line 0 127 127 0" -define icon:auto-resize=64,48,32,16 perceptionmd-uninstall.ico