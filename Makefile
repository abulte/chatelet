serve:
	adev runserver chatelet/app.py
work:
	rq worker --with-scheduler
apidoc:
	python cli.py apidoc
	npx swagger-markdown -i docs/swagger.json -o docs/apidoc.md
