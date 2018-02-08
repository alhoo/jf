CC = g++
CFLAGS = -g -pthread -fwrapv -Wall -Wno-unused-result -fPIC -std=c++11
LDFLAGS = -pthread -shared

INCLUDE = $(shell pkg-config --cflags python3)
#INCLUDE = -I/usr/include/python3.5m/


all: jf/jsonlgen.so

jf/jsonlgen.o: jf/jsonlgen.cc
	$(CC) $(CFLAGS) $(INCLUDE) -c $^ -o $@

jf/jsonlgen.so: jf/jsonlgen.o
	$(CC) $(LDFLAGS) $^ -o $@


test: jf/jsonlgen.so
	nosetests --with-coverage --cover-html-dir=coverage --cover-package=jf --cover-html --with-id tests/

devinstall: README.rst
	pip install -e .

readme:
	pandoc README.md | sed 's/<code/<code style="color:cyan;"/g'| elinks -dump -dump-color-mode 1 | sed -r 's/^/ /g;s/ *$$//' | (echo && cat && echo)

README.rst: README.md
	pandoc -f markdown -t rst $< >$@

build33:
	virtualenv local --python=python3.3
	local/bin/pip install -r requirements.txt

build34:
	virtualenv local --python=python3.4
	local/bin/pip install -r requirements.txt

build35:
	virtualenv local --python=python3.5
	local/bin/pip install -r requirements.txt

pylint:
	pylint --output-format=parseable jf tests

pep8:
	pep8 jf tests

package:
	pip wheel .

release: jf/jsonlgen.so README.rst
	@echo update version to setup.py
	@echo git tag version
	@echo python setup.py sdist upload -r pypi

clean:
	rm -Rf *.whl jf/*.o jf/*.so tests/*.pyc jf/*.pyc build dist
