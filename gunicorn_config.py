import multiprocessing
import os
import traceback
import sys
import threading

# Server socket
bind = "0.0.0.0:10000"
backlog = 1024  # Reduced from 2048

# Worker processes - optimized for free tier
workers = 1  # Single worker for limited memory
worker_class = 'sync'
threads = 2  # Reduced from 4
worker_connections = 500  # Reduced from 1000

# Timeouts
timeout = 60  # Reduced from 180 to 60 seconds
graceful_timeout = 30  # Reduced from 120 to 30 seconds
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'  # Changed from debug to reduce log volume

# Process naming
proc_name = 'horizont'
default_proc_name = 'gunicorn'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Error handling
capture_output = True
enable_stdio_inheritance = True

# Memory management
max_requests = 25  # Reduced from 50
max_requests_jitter = 5
worker_tmp_dir = "/tmp"

# Prevent workers from hanging
check_worker_timeout = 30

# SSL
ssl_version = 'TLSv1_2'
cert_reqs = 'CERT_NONE'
ca_certs = None
suppress_ragged_eofs = True
do_handshake_on_connect = False

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Debugging
reload = False
reload_engine = 'auto'
spew = False
check_config = False

# Server hooks
def on_starting(server):
    server.log.info("server is starting")

def on_reload(server):
    pass

def when_ready(server):
    server.log.info("server is ready")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    pass

def pre_exec(server):
    pass

def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))

def post_request(worker, req, environ, resp):
    pass

def child_exit(server, worker):
    pass

def on_exit(server):
    pass

def worker_exit(server, worker):
    """Log when worker exits"""
    server.log.info("worker exited (pid: %s)", worker.pid)

def worker_int(worker):
    """Log when worker receives INT or QUIT signal"""
    worker.log.info("worker received INT or QUIT signal")
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code)) 