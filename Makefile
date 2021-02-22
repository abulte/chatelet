serve:
	adev runserver chatelet/app.py
work:
	rq worker --with-scheduler
