CC = g++
CFLAGS = -O3 -pthread -fwrapv -Wall -Wno-unused-result -fPIC -std=c++11
LDFLAGS = -pthread -shared

INCLUDE = $(shell pkg-config --cflags python3)
SPHINXOPTS ?=
SPHINXBUILD ?= python3 -m sphinx.cmd.build
DOC_SOURCE_DIR ?= docs/source
DOC_FILES := $(shell find $(DOC_SOURCE_DIR) -type f -name '*.rst')
DOC_BUILD_DIR ?= docs/build
#INCLUDE = -I/usr/include/python3.5m/


all: jf/jsonlgen.so

jf/jsonlgen.o: jf/jsonlgen.cc
	$(CC) $(CFLAGS) $(INCLUDE) -c $^ -o $@

jf/jsonlgen.so: jf/jsonlgen.o
	$(CC) $(LDFLAGS) $^ -o $@

program.prof:
	python3 -m cProfile -o program.prof jf/__main__.py 'sorted(.cmd)' ~/.zsh_fullhistory.jsonl >/dev/null 2>/dev/null

profile: program.prof
	pip install -U tuna==0.4.4
	tuna program.prof

test: jf/jsonlgen.so
	nosetests --with-coverage --cover-html-dir=coverage --cover-package=jf --cover-html --with-doctest

devinstall: README.rst
	pip install -e .

readme:
	pandoc README.md | sed 's/<code/<code style="color:cyan;"/g'| elinks -dump -dump-color-mode 1 | sed -r 's/^/ /g;s/ *$$//' | (echo && cat && echo)

README.rst: README.md
	pandoc -f markdown -t rst $< >$@

$(DOC_BUILD_DIR)/html/index.html: $(DOC_FILES)
	@$(SPHINXBUILD) -M html "$(DOC_SOURCE_DIR)" "$(DOC_BUILD_DIR)" $(SPHINXOPTS)

## Create HTML documentation based on Sphinx sources
docs: $(DOC_BUILD_DIR)/html/index.html


build35:
	virtualenv local --python=python3.5
	local/bin/pip install -r requirements.txt

build36:
	virtualenv local --python=python3.6
	local/bin/pip install -r requirements.txt

build37:
	virtualenv local --python=python3.7
	local/bin/pip install -r requirements.txt

build38:
	virtualenv local --python=python3.8
	local/bin/pip install -r requirements.txt

pylint:
	pylint --output-format=parseable jf tests

pep8:
	pep8 jf tests

package:
	pip wheel .

release: jf/jsonlgen.so README.rst
		@echo "git flow release start <version>"
		@echo update version to setup.py
		@echo git add setup.py
		@echo 'git commit -m "bump version to <version>"'
		@echo git flow release finish
		@echo git push --all
		@echo git push --tags
		@echo python setup.py sdist upload -r pypi

clean:
	rm -Rf *.whl jf/*.o jf/*.so tests/*.pyc jf/*.pyc build dist
