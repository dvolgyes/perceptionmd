#!/usr/bin/make

default:
	echo "There is nothing to do."
test:
	coverage run --concurrency=thread --append --source perceptionmd ./PerceptionMD.py perceptionmd/unittests/travis-example.pmd
	coverage run --concurrency=thread --append --source perceptionmd ./PerceptionMD.py perceptionmd/examples/simple/simple.pmd
	coverage run --append --source perceptionmd perceptionmd/utils/utils.py
	coverage run --append --source perceptionmd perceptionmd/utils/rev_eng.py
	coverage run --append --source perceptionmd perceptionmd/utils/Log.py


graph:
	@textx check perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.pmd
	@textx visualize perceptionmd/lang/perception.tx perceptionmd/unittests/travis-example.pmd >/dev/null
	@dot -Tpng -O perceptionmd/lang/perception.tx.dot
	@dot -Tpng -O perceptionmd/unittests/travis-example.pmd.dot

ico:
	@inkscape -z perceptionmd.svg -w 128 -h 128 -e perceptionmd.png
	@convert perceptionmd.png -define icon:auto-resize=64,48,32,16 perceptionmd.ico
	@convert perceptionmd.png -stroke red -strokewidth 12 -draw "line 0 0 127 127, line 0 127 127 0" -define icon:auto-resize=64,48,32,16 perceptionmd-uninstall.ico