# scheduler.py
import os
import traceback
from app import create_app, scheduler
from app.tasks import check_and_process_unsorted_events
import atexit

app = create_app()

main_pid = os.getpid()
print(f"[PID {main_pid}] scheduler.py: Starting scheduler process...", flush=True)

# Initialize and start scheduler
job_id = 'process_unsorted_events_job'

try:
    if not scheduler.running:
        scheduler.start(paused=False)
        print(f"[PID {main_pid}] scheduler.py: Scheduler started successfully. State: {scheduler.state}", flush=True)
    else:
        print(f"[PID {main_pid}] scheduler.py: Scheduler already running (unexpected).", flush=True)

    if not scheduler.get_job(job_id):
        run_interval_minutes = 1
        scheduler.add_job(
            id=job_id,
            func=check_and_process_unsorted_events,
            args=[app],
            trigger='interval',
            minutes=run_interval_minutes,
            misfire_grace_time=900,
            replace_existing=False,
            max_instances=1
        )
        added_job = scheduler.get_job(job_id)
        print(f"[PID {main_pid}] scheduler.py: Job '{job_id}' added. Next run: {added_job.next_run_time}", flush=True)
    else:
        existing_job = scheduler.get_job(job_id)
        print(f"[PID {main_pid}] scheduler.py: Job '{job_id}' already exists. Next run: {existing_job.next_run_time}", flush=True)

except Exception as e:
    print(f"[PID {main_pid}] scheduler.py: Error in scheduler setup: {e}", flush=True)
    traceback.print_exc()

# Ensure scheduler shuts down cleanly on exit
def shutdown_scheduler_on_exit():
    if scheduler.running:
        print(f"[PID {os.getpid()}] scheduler.py: Shutting down scheduler...", flush=True)
        try:
            scheduler.shutdown(wait=False)
            print(f"[PID {os.getpid()}] scheduler.py: Scheduler shut down.", flush=True)
        except Exception as e_shutdown:
            print(f"[PID {os.getpid()}] scheduler.py: Error shutting down scheduler: {e_shutdown}", flush=True)

atexit.register(shutdown_scheduler_on_exit)

import time

try:
    print(f"[PID {os.getpid()}] scheduler.py: Scheduler running. Press Ctrl+C to exit.", flush=True)
    while True:
        time.sleep(1)  # Keeps the process alive
except (KeyboardInterrupt, SystemExit):
    print(f"[PID {os.getpid()}] scheduler.py: Caught exit signal.", flush=True)
finally:
    if scheduler.running:
        print(f"[PID {os.getpid()}] scheduler.py: Shutting down scheduler...", flush=True)
        scheduler.shutdown()
        print(f"[PID {os.getpid()}] scheduler.py: Scheduler shut down.", flush=True)
# scheduler.py
import os
import traceback
from app import create_app, scheduler
from app.tasks import check_and_process_unsorted_events
import atexit

app = create_app()

main_pid = os.getpid()
print(f"[PID {main_pid}] scheduler.py: Starting scheduler process...", flush=True)

# Initialize and start scheduler
job_id = 'process_unsorted_events_job'

try:
    if not scheduler.running:
        scheduler.start(paused=False)
        print(f"[PID {main_pid}] scheduler.py: Scheduler started successfully. State: {scheduler.state}", flush=True)
    else:
        print(f"[PID {main_pid}] scheduler.py: Scheduler already running (unexpected).", flush=True)

    if not scheduler.get_job(job_id):
        run_interval_minutes = 1
        scheduler.add_job(
            id=job_id,
            func=check_and_process_unsorted_events,
            args=[app],
            trigger='interval',
            minutes=run_interval_minutes,
            misfire_grace_time=900,
            replace_existing=False,
            max_instances=1
        )
        added_job = scheduler.get_job(job_id)
        print(f"[PID {main_pid}] scheduler.py: Job '{job_id}' added. Next run: {added_job.next_run_time}", flush=True)
    else:
        existing_job = scheduler.get_job(job_id)
        print(f"[PID {main_pid}] scheduler.py: Job '{job_id}' already exists. Next run: {existing_job.next_run_time}", flush=True)

except Exception as e:
    print(f"[PID {main_pid}] scheduler.py: Error in scheduler setup: {e}", flush=True)
    traceback.print_exc()

# Ensure scheduler shuts down cleanly on exit
def shutdown_scheduler_on_exit():
    if scheduler.running:
        print(f"[PID {os.getpid()}] scheduler.py: Shutting down scheduler...", flush=True)
        try:
            scheduler.shutdown(wait=False)
            print(f"[PID {os.getpid()}] scheduler.py: Scheduler shut down.", flush=True)
        except Exception as e_shutdown:
            print(f"[PID {os.getpid()}] scheduler.py: Error shutting down scheduler: {e_shutdown}", flush=True)

atexit.register(shutdown_scheduler_on_exit)

import time

try:
    print(f"[PID {os.getpid()}] scheduler.py: Scheduler running. Press Ctrl+C to exit.", flush=True)
    while True:
        time.sleep(1)  # Keeps the process alive
except (KeyboardInterrupt, SystemExit):
    print(f"[PID {os.getpid()}] scheduler.py: Caught exit signal.", flush=True)
finally:
    if scheduler.running:
        print(f"[PID {os.getpid()}] scheduler.py: Shutting down scheduler...", flush=True)
        scheduler.shutdown()
        print(f"[PID {os.getpid()}] scheduler.py: Scheduler shut down.", flush=True)
