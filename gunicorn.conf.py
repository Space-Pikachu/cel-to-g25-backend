# gunicorn.conf.py
timeout = 300  # seconds (5 minutes)
worker_class = "sync"
workers = 1
threads = 1
