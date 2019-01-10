
all: edit-ghi.venv

edit-ghi.venv:
	virtualenv -p python3 edit-ghi.venv && \
	. edit-ghi.venv/bin/activate && \
	./edit-ghi.venv/bin/pip install -r requirements.txt

clean:
	rm -rf edit-ghi.venv *.pyc

test: edit-ghi.venv
	. edit-ghi.venv/bin/activate && \
	./func_test.py
