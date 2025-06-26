import multiprocessing
import os
import traceback
import sys
import threading

# Server socket
bind = "0.0.0.0:" + str(os.getenv("PORT", "8000"))
backlog = 2048

# Worker processes
workers = 2
worker_class = 'sync'
threads = 4
worker_connections = 1000

# Timeouts
timeout = 120  # Reduced from 600 to fail faster
graceful_timeout = 60  # Reduced from 300 to fail faster
keepalive = 2  # Added keepalive

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'horizont'

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
max_requests = 100  # Reduced from 1000 to recycle workers more frequently
max_requests_jitter = 10  # Reduced jitter accordingly
worker_tmp_dir = "/dev/shm"  # Use shared memory for temp files

# Prevent workers from hanging
check_worker_timeout = 30  # Check worker health every 30 seconds

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

def worker_abort(worker):
    """Log when worker receives SIGABRT signal"""
    worker.log.info("worker received SIGABRT signal")

def worker_exit(server, worker):
    """Log when worker exits"""
    server.log.info("worker exited (pid: %s)", worker.pid)

def on_starting(server):
    """Log when server starts"""
    server.log.info("server is starting")

def on_reload(server):
    """Log when server reloads"""
    server.log.info("server is reloading")

def post_fork(server, worker):
    """Log when worker is forked"""
    server.log.info("worker forked (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Log before worker is forked"""
    server.log.info("pre-fork (worker_class: %s)", worker.worker_class)

def pre_exec(server):
    """Log before exec"""
    server.log.info("pre-exec")

def when_ready(server):
    """Log when server is ready"""
    server.log.info("server is ready")

def child_exit(server, worker):
    """Log when child exits"""
    server.log.info("child exited (pid: %s)", worker.pid)

def on_exit(server):
    server.log.info("server is shutting down") 