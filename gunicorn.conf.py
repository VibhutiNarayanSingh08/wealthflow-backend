import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 1
threads = 4
worker_class = "gthread"
timeout = 120
graceful_timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
preload_app = True
