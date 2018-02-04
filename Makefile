test:
	nosetests --with-coverage --cover-html-dir=coverage --cover-package=jf --cover-html --with-id tests/

devinstall: README.rst
	pip install -e .

readme:
	pandoc README.md | sed 's/<code/<code style="color:cyan;"/g'| elinks -dump -dump-color-mode 1 | sed -r 's/^/ /g;s/ *$$//' | (echo && cat && echo)

README.rst: README.md
	pandoc -f markdown -t rst $< >$@

pylint:
	pylint --output-format=parseable jf tests

pep8:
	pep8 jf tests

package:
	pip wheel .

release: README.rst
	@echo update version to setup.py
	@echo git tag version
	@echo python setup.py sdist upload -r pypi

clean:
	rm *.whl
