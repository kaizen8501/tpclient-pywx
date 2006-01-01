
release:
	rm -rf dist
	python setup.py sdist --formats=gztar,zip
	cp dist/* ../web/downloads/tpclient-pywx
	cd ../web/downloads/tpclient-pywx ; darcs add *.* ; darcs record

windows:
	echo python setup.py py2exe

clean:
	rm -rf dist
	rm -rf build
