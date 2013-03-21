
live-tests: test
	python setup.py livetest

doc:
	epydoc --html \
		-n "InterMine Python Webservice Client" \
		-u "http://www.intermine.org" \
		-v \
		--exclude="intermine.intermine" \
		--output docs \
		intermine
	cd docs && zip docs.zip *
	mv docs/docs.zip ./current-docs.zip

publish: test doc
	python setup.py sdist upload

test:
	python setup.py test

PHONY: test live-tests publish doc
