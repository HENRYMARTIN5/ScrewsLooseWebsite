from flask import Flask, render_template
import schedule
import time
import threading
import json

try:
    data = json.load(open("data.json"))
except FileNotFoundError:
    open("data.json", "w").write("[]")
    data = json.load(open("data.json"))

def reload_data():
    global data
    data = json.load(open("data.json"))
    
def save_data():
    global data
    open("data.json", "w").write(
        json.dumps(data, indent=4)
    )

def update_data():
    print("made it")

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
    #schedule.every(20).minutes.do(update_data)
    schedule.every(1).seconds.do(update_data)
    thread = threading.Thread(target=background_update_worker)
    thread.start()
    app.run(host="0.0.0.0", port=8080, debug=False)
    running = False
    thread.join()