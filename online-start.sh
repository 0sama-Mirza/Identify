#!/bin/bash

SESSION="online-identify"

# Kill previous session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Start a new tmux session
tmux new-session -d -s $SESSION

# Window 1: Gunicorn
tmux rename-window -t $SESSION:0 'gunicorn'
tmux send-keys -t $SESSION 'pkill -f "gunicorn.*:5000"' C-m
tmux send-keys -t $SESSION 'source ~/Python-Environments/flaskenv/bin/activate' C-m
tmux send-keys -t $SESSION 'cd /home/archmax/startup/FYP-Project/identify/Front-Back-End' C-m
tmux send-keys -t $SESSION 'gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 run:app' C-m

# Window 2: Scheduler
tmux new-window -t $SESSION -n 'scheduler'
tmux send-keys -t $SESSION:1 'source ~/Python-Environments/flaskenv/bin/activate' C-m
tmux send-keys -t $SESSION:1 'cd /home/archmax/startup/FYP-Project/identify/Front-Back-End' C-m
tmux send-keys -t $SESSION:1 'python scheduler.py' C-m

# Window 3: Uvicorn (FastAPI)
tmux new-window -t $SESSION -n 'uvicorn'
tmux send-keys -t $SESSION:2 'source ~/Python-Environments/Cuda-Deep-Fast/bin/activate' C-m
tmux send-keys -t $SESSION:2 'cd /home/archmax/startup/FYP-Project/identify/FDRP' C-m
tmux send-keys -t $SESSION:2 'uvicorn main:app --reload' C-m

# Window 4: Retinaface Manager
tmux new-window -t $SESSION -n 'retinaface'
tmux send-keys -t $SESSION:3 'source ~/Python-Environments/Cuda-Deep-Fast/bin/activate' C-m
tmux send-keys -t $SESSION:3 'cd /home/archmax/startup/FYP-Project/identify/FDRP' C-m
tmux send-keys -t $SESSION:3 'python retinaface_processing_manager.py' C-m

# Window 5: Facenet Manager
tmux new-window -t $SESSION -n 'facenet'
tmux send-keys -t $SESSION:4 'source ~/Python-Environments/Cuda-Deep-Fast/bin/activate' C-m
tmux send-keys -t $SESSION:4 'cd /home/archmax/startup/FYP-Project/identify/FDRP' C-m
tmux send-keys -t $SESSION:4 'python facenet_processing_manager.py' C-m

# Window 6: HDBSCAN Manager
tmux new-window -t $SESSION -n 'hdbscan'
tmux send-keys -t $SESSION:5 'source ~/Python-Environments/Sorting_Algos-env/bin/activate' C-m
tmux send-keys -t $SESSION:5 'cd /home/archmax/startup/FYP-Project/identify/FDRP' C-m
tmux send-keys -t $SESSION:5 'python hdbscan_processing_manager.py' C-m

# Window 7: Cloudflared 8000
tmux new-window -t $SESSION -n 'cf-8000'
tmux send-keys -t $SESSION:6 'cloudflared tunnel --url http://localhost:8000 --loglevel debug --protocol http2 2>&1 | tee /tmp/cloudflared8000.log' C-m

# Window 8: Cloudflared 5000
tmux new-window -t $SESSION -n 'cf-5000'
tmux send-keys -t $SESSION:7 'cloudflared tunnel --url http://localhost:5000 --loglevel debug --protocol http2 2>&1 | tee /tmp/cloudflared5000.log' C-m

# Window 9: Adding new URL
tmux new-window -t $SESSION -n 'add_tunnel_url'
tmux send-keys -t $SESSION:8 './start_tunnel_and_print_url.sh' C-m

# Attach to the session
tmux attach-session -t $SESSION

