pybuild:
	rm -rf dist/*
	python3 setup.py sdist bdist_wheel

testdeploy:
	twine upload --repository testpypi dist/*

deploy:
	twine upload dist/*

setup:
	pip3 install --user --upgrade setuptools wheel twine