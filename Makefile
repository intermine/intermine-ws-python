
live-tests: test
	python setup.py livetest

test:
	python setup.py test

PHONY: test live-tests
