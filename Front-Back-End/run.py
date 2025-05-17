# run.py
from app import create_app

# Create the app
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)



# # run.py
# import os
# import sys
# from app import create_app, scheduler # Import create_app AND the global scheduler instance
# import traceback
# import atexit

# # Create the Flask app instance using the factory
# # This runs scheduler.init_app(app) inside create_app
# app = create_app()

# # --- This block runs only once in the final execution process ---
# # --- when invoked via `python run.py` (even with reloader) ---
# if __name__ == '__main__':
#     main_pid = os.getpid()
#     print(f"[PID {main_pid}] run.py: Entered __main__ block.", flush=True)

#     # Make sure the task function is importable before adding job
#     try:
#         from app.tasks import check_and_process_unsorted_events
#         task_func = check_and_process_unsorted_events
#         print(f"[PID {main_pid}] run.py: Task function imported successfully.", flush=True)
#     except ImportError:
#         print(f"[PID {main_pid}] run.py: ERROR - Could not import task function. Scheduler job will NOT be added.", flush=True)
#         task_func = None

#     # Start Scheduler and Add Job ONLY if task function was imported
#     if task_func:
#         # Start the scheduler if it's not already running
#         if not scheduler.running:
#             print(f"[PID {main_pid}] run.py: Scheduler not running. Attempting start...", flush=True)
#             try:
#                 scheduler.start(paused=False)
#                 print(f"[PID {main_pid}] run.py: Scheduler started successfully. State: {scheduler.state}", flush=True)
#             except Exception as e_start:
#                 print(f"[PID {main_pid}] run.py: Error starting scheduler: {e_start}", flush=True)
#                 traceback.print_exc()
#         else:
#              print(f"[PID {main_pid}] run.py: Scheduler reported as already running (unexpected here?).", flush=True)


#         # Add the job ONLY if the scheduler started successfully
#         job_id = 'process_unsorted_events_job'
#         if scheduler.running and not scheduler.get_job(job_id):
#             print(f"[PID {main_pid}] run.py: Adding job '{job_id}'...", flush=True)
#             try:
#                 # ====> SET YOUR DESIRED INTERVAL <====
#                 run_interval_minutes = 1
#                 # run_interval_seconds = 60 # For testing
#                 # =====================================
#                 scheduler.add_job(
#                     id=job_id,
#                     func=task_func, # Use the imported function
#                     args=[app], # Pass the app instance created above
#                     trigger='interval',
#                     minutes=run_interval_minutes,
#                     # seconds=run_interval_seconds, # Uncomment for testing
#                     misfire_grace_time=900, # Adjust as needed
#                     replace_existing=False, # Don't replace if it somehow exists
#                     max_instances=1
#                 )
#                 added_job = scheduler.get_job(job_id)
#                 if added_job:
#                     # Update log message to reflect interval
#                     print(f"[PID {main_pid}] run.py: Successfully added job '{job_id}' (Next Run: {added_job.next_run_time}). Interval: {run_interval_minutes} minutes.", flush=True)
#                     # print(f"[PID {main_pid}] run.py: Successfully added job '{job_id}' (Next Run: {added_job.next_run_time}). Interval: {run_interval_seconds} seconds.", flush=True) # For test interval
#                 else:
#                     print(f"[PID {main_pid}] run.py: ERROR - Failed to retrieve job '{job_id}' after add.", flush=True)
#             except Exception as e_add:
#                 print(f"[PID {main_pid}] run.py: Error adding job: {e_add}", flush=True)
#                 traceback.print_exc()
#         elif scheduler.get_job(job_id):
#              existing_job = scheduler.get_job(job_id)
#              print(f"[PID {main_pid}] run.py: Job '{job_id}' already exists (Next Run: {existing_job.next_run_time}).", flush=True)
#         elif not scheduler.running:
#             print(f"[PID {main_pid}] run.py: Scheduler failed to start. Cannot add job.", flush=True)


#     # Optional: Add exit handler here if needed, associated with the main process
#     def shutdown_scheduler_on_exit():
#          if scheduler.running:
#               print(f"\n[PID {os.getpid()}] run.py: Shutting down scheduler on exit...", flush=True)
#               try:
#                   # Set wait=False for quicker exit if needed, True waits for running jobs
#                   scheduler.shutdown(wait=False)
#                   print(f"[PID {os.getpid()}] run.py: Scheduler shut down.", flush=True)
#               except Exception as e_shutdown:
#                   print(f"[PID {os.getpid()}] run.py: Error shutting down scheduler: {e_shutdown}", flush=True)
#     atexit.register(shutdown_scheduler_on_exit)
#     print(f"[PID {main_pid}] run.py: Registered scheduler shutdown handler.", flush=True)


#     # Start the Flask development server
#     # use_reloader=True is the default when debug=True
#     print(f"[PID {main_pid}] run.py: Starting Flask app.run (Debug: {app.config.get('DEBUG', False)})...", flush=True)
#     # Ensure debug=True enables the reloader as intended for testing this fix
#     # Use app.config.get to avoid errors if DEBUG isn't set
#     use_debug = app.config.get('DEBUG', False)
#     app.run(host='0.0.0.0', port=5000, debug=use_debug, use_reloader=use_debug)

#     # Code here runs after app.run exits
#     print(f"[PID {main_pid}] run.py: Flask app.run has exited.", flush=True)
