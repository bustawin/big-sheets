.PHONY: test

clean:
	rm -rf build dist

build: clean
	pyinstaller main.spec

build-run: build
	./dist/main

coverage:
	coverage run -m pytest
	coverage report

test:
	pytest

icons:
	iconutil --convert icns assets/app.iconset
