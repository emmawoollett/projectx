
up:
	docker-compose up

manage:
	docker-compose exec projectx /home/user/venv/bin/python /home/user/backend/app/manage.py

build:
	cd frontend && yarn install
	cd frontend && yarn build
	cd tests && yarn install
	docker-compose build projectx

lint:
	pycodestyle backend/app/ backend/tests/
	isort --check-only --diff backend/app backend/tests
	unify --check-only --recursive --quote \" backend/app backend/tests

fix_lint:
	autopep8 -i -r backend/app/ backend/tests/
	isort backend/app backend/tests
	unify --in-place --recursive --quote \" backend/app backend/tests
