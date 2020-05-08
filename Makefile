clean:
	rm -rf build dist

build: clean
	pyinstaller main.spec

build-run: build
	./dist/main

icons:
	iconutil --convert icns assets/app.iconset
