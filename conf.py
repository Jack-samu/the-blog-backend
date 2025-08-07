import multiprocessing
import gevent.monkey

gevent.monkey.patch_all()

bind = "0.0.0.0:8088"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
worker_connections = 1000
timeout = 30
keepalive = 5
preload_app = False

log_path = 'logs/app.log'
accesslog = log_path
errorlog = log_path
loglevel = "debug"