from flask import Flask, render_template
import schedule
import time
import threading
import json
import subprocess
import os

DEBUG = False

try:
    data = json.load(open("data.json"))
except FileNotFoundError:
    open("data.json", "w").write("[]")
    data = json.load(open("data.json"))

def reload_data():
    global data
    data = json.load(open("data.json"))

def save_data(scraped_data):
    global data
    unique_data = {item["link"]: item for item in data}
    for item in scraped_data:
        unique_data[item["link"]] = item
    data = list(unique_data.values())
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def update_data():
    global data
    if os.name == 'nt':
        subprocess.call("env\\Scripts\\python amazon.py")
    else:
        subprocess.call("env\\bin\\python amazon.py")
    if os.path.exists("amazon_results_DELETEME.json"):
        with open("amazon_results_DELETEME.json") as f:
            amazon_data = json.load(f)
        os.remove("amazon_results_DELETEME.json")
        save_data(amazon_data)

running = True
def background_update_worker():
    global running
    while running:
        schedule.run_pending()
        time.sleep(1)

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    if DEBUG:
        update_data()
    thread = threading.Thread(target=background_update_worker)
    thread.start()
    app.run(host="0.0.0.0", port=8080, debug=False)
    running = False
    thread.join()
