import os
import time
import threading
from flask import Flask
from twelvedata import TDClient

# 1. THE RENDER FIX: A tiny web server to stay online
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. THE CREDIT FIX: Optimized Scanner
def signal_loop():
    td = TDClient(apikey="YOUR_API_KEY")
    while True:
        try:
            print("🔎 Scanning markets...")
            # Your scanning logic here...
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Slower sleep: 300 seconds = 5 minutes
        # This ensures you stay under the 800/day limit
        time.sleep(300) 

if __name__ == "__main__":
    # Start the web server in the background
    threading.Thread(target=run_flask, daemon=True).start()
    # Start your bot loop
    signal_loop()
