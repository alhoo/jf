test:
	nosetests --with-id tests/query_test.py

readme:
	pandoc README.md | sed 's/<code/<code style="color:cyan;"/g'| elinks -dump -dump-color-mode 1 | sed -r 's/^/ /g;s/ *$$//' | (echo && cat && echo)
