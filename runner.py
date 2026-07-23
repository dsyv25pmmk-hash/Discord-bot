"""
VCBotY - Forever Online Runner
This script keeps your bot alive 24/7 with auto-restart and keep-alive server.
Made by Turki (the best) 🔥
"""

import os
import sys
import subprocess
import time
import threading
import socket

# ============ CONFIG ============
BOT_FILE = "Bot.py"  # Your bot's main file
PORT = 8080  # Port for keep-alive server
CHECK_INTERVAL = 30  # Check bot every 30 seconds

# ============ KEEP-ALIVE SERVER ============
def start_keep_alive():
    """Starts a tiny web server to keep the bot alive on hosting platforms"""
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "✅ VCBotY is alive and running! | Made by Turki (the best)"
        
        @app.route('/ping')
        def ping():
            return "pong"
        
        # Run in a separate thread
        def run_server():
            app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        print(f"🌐 Keep-alive server running on port {PORT}")
        print(f"📡 Ping it at: http://localhost:{PORT}/ping")
        return True
    except ImportError:
        print("⚠️ Flask not installed. Keep-alive server disabled.")
        print("   Install it with: pip install flask")
        return False
    except Exception as e:
        print(f"⚠️ Could not start keep-alive server: {e}")
        return False

# ============ BOT RUNNER ============
def run_bot():
    """Runs the bot and restarts it if it crashes"""
    print("🚀 Starting VCBotY...")
    print("=" * 40)
    
    while True:
        try:
            # Run the bot
            process = subprocess.Popen(
                [sys.executable, BOT_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            print(f"✅ Bot started (PID: {process.pid})")
            
            # Monitor the process
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"[BOT] {output.strip()}")
                
                # Check if process is still alive
                if process.poll() is not None:
                    break
                
                time.sleep(0.1)
            
            # Process ended — check why
            exit_code = process.returncode
            if exit_code == 0:
                print("✅ Bot stopped normally.")
            else:
                print(f"⚠️ Bot crashed with exit code {exit_code}")
            
            print("🔄 Restarting in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user.")
            break
        except Exception as e:
            print(f"❌ Runner error: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)

# ============ MAIN ============
if __name__ == "__main__":
    print("=" * 40)
    print("🎵 VCBotY Forever Online Runner")
    print("Made by Turki (the best) ✨")
    print("=" * 40)
    
    # Check if bot file exists
    if not os.path.exists(BOT_FILE):
        print(f"❌ Error: {BOT_FILE} not found!")
        print(f"   Make sure {BOT_FILE} is in the same folder.")
        sys.exit(1)
    
    # Start keep-alive server (optional)
    start_keep_alive()
    
    # Run the bot with auto-restart
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
