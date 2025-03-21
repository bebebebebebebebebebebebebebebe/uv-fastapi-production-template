.PHONY: worker listen

worker:
	PYTHONPATH=$(CURDIR) uv run celery --app src.app.worker.tasks worker -l INFO

send-email:
	PYTHONPATH=$(CURDIR) uv run python -m src.app.core.send_email
