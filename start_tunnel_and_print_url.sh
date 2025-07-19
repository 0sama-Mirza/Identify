#!/bin/bash

LOG_8000="/tmp/cloudflared8000.log"
LOG_5000="/tmp/cloudflared5000.log"
MAIN_PY=~/startup/FYP-Project/identify/FDRP/main.py
HTML_JS_FILE=~/startup/FYP-Project/identify/Front-Back-End/templates/event_detail.html

echo "⏳ Waiting for Cloudflare Tunnels to initialize..."

found_8000=""
found_5000=""

# Try to extract both URLs, retrying for up to ~10 seconds
for i in {1..10}; do
    sleep 1

    if [[ -z "$found_8000" && -f "$LOG_8000" ]]; then
        found_8000=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$LOG_8000" | head -n1)
    fi

    if [[ -z "$found_5000" && -f "$LOG_5000" ]]; then
        found_5000=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$LOG_5000" | head -n1)
    fi

    if [[ -n "$found_8000" && -n "$found_5000" ]]; then
        break
    fi
done

echo ""

# ==== 8000 Tunnel ====
if [[ -n "$found_8000" ]]; then
    echo "✅ 8000 Tunnel URL: $found_8000"
else
    echo "❌ Could not find 8000 tunnel URL."
fi

# ==== 5000 Tunnel ====
if [[ -n "$found_5000" ]]; then
    echo "✅ 5000 Tunnel URL: $found_5000"

    ESCAPED_URL=$(printf '%s\n' "$found_5000" | sed 's/[&/\]/\\&/g')

    if grep -q '\.trycloudflare\.com' "$MAIN_PY"; then
        echo "🔄 Replacing old .trycloudflare.com URL in allow_origins..."
        sed -i "s|\"https://[^\"]*\.trycloudflare\.com\"|\"$ESCAPED_URL\"|g" "$MAIN_PY"
        echo "✅ Replaced existing Cloudflare URL in main.py"
    elif grep -q "$ESCAPED_URL" "$MAIN_PY"; then
        echo "ℹ️  5000 URL already present in main.py. No changes made."
    else
        echo "➕ Appending 5000 URL to allow_origins in main.py..."
        sed -i "/allow_origins=\[/ s/\]/, \"$ESCAPED_URL\"]/" "$MAIN_PY"
        echo "✅ Successfully appended 5000 tunnel URL in main.py"
    fi
else
    echo "❌ Could not find 5000 tunnel URL. Skipping injection into main.py."
fi

# ==== Update cloudURL in JS ====
if [[ -n "$found_8000" ]]; then
    echo "🔧 Updating cloudURL in event_detail.html..."
    sed -i "s|^ *const cloudURL = \".*\";|const cloudURL = \"$found_8000/match-face/\";|" "$HTML_JS_FILE"
    echo "✅ Successfully updated cloudURL in event_detail.html"
else
    echo "❌ Could not find 8000 tunnel URL. Skipping JS update."
fi

# ==== Tmux tips ====
echo ""
echo "📦 To list the current tmux session run:"
echo "   tmux ls"
echo "🧨 To kill a session run:"
echo "   tmux kill-session -t online-identify"
