#!/bin/bash
# Script to select and activate a virtual environment

if [[ "$0" == "${BASH_SOURCE[0]}" ]]; then
    echo "Please use 'source ./activate-env.sh' to run this script."
    exit 1
fi

# Define the absolute path to the Python-Environments folder
ENV_DIR="$HOME/Python-Environments"

if [ ! -d "$ENV_DIR" ]; then
    echo "Error: Directory '$ENV_DIR' does not exist!"
    echo "If you dont have the environment then enter these commands:"
    echo "1) mkdir ~/Python-Environments"
    echo "2) python -m venv ~/Python-Environments/flaskenv"
    echo "3) Run this script again."
    echo "4) pip install -r requirements.txt"
    return 1
fi

echo "If you dont have the environment then enter these commands:"
echo "1) python -m venv ~/Python-Environments/Your-Env-Name"
echo "3) Run this script again."
echo "4) pip install -r requirements.txt (if it exists)"

echo "Available Virtual Environments:"
echo "--------------------------------"

# List all directories in the Python-Environments folder
ENVS=($(ls -d "$ENV_DIR"/*/))

# Display each virtual environment with a number
for i in "${!ENVS[@]}"; do
    echo "$((i+1)). $(basename "${ENVS[$i]}")"
done

echo "--------------------------------"
read -p "Select the environment number to activate: " ENV_NUMBER

if [[ $ENV_NUMBER =~ ^[0-9]+$ ]] && (( ENV_NUMBER >= 1 && ENV_NUMBER <= ${#ENVS[@]} )); then
    ENV_NAME="${ENVS[$((ENV_NUMBER-1))]}"
    echo "Activating environment: $(basename "$ENV_NAME")"
    source "$ENV_NAME/bin/activate"
else
    echo "Invalid selection. Please try again."
fi

