# main.py
import os
import subprocess
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

STREAM_LOCK = threading.Lock()
STREAM_PROC = None
CURRENT = {}

def start_stream_process(stream_key, video_url, title="", loop=False):
    global STREAM_PROC, CURRENT
    with STREAM_LOCK:
        if STREAM_PROC and STREAM_PROC.poll() is None:
            return False, "Already running"
        # call helper in stream.py to build command
        from stream import build_ffmpeg_command
        cmd = build_ffmpeg_command(stream_key, video_url, title, loop)
        # start process
        STREAM_PROC = subprocess.Popen(cmd, shell=isinstance(cmd, str))
        CURRENT = {"stream_key": stream_key, "video_url": video_url, "title": title, "loop": loop, "pid": getattr(STREAM_PROC,'pid',None)}
        return True, "Stream started"

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json() or {}
    sk = data.get('stream_key') or os.environ.get('STREAM_KEY')
    video = data.get('video_url')
    title = data.get('title','')
    loop = bool(data.get('loop', False))
    if not sk or not video:
        return jsonify({"message":"stream_key and video_url required"}), 400
    ok, msg = start_stream_process(sk, video, title, loop)
    status = 200 if ok else 400
    return jsonify({"message": msg}), status

@app.route('/stop', methods=['POST'])
def stop():
    global STREAM_PROC, CURRENT
    with STREAM_LOCK:
        if not STREAM_PROC or STREAM_PROC.poll() is not None:
            return jsonify({"message":"No active stream"}), 400
        STREAM_PROC.terminate()
        try:
            STREAM_PROC.wait(timeout=10)
        except Exception:
            STREAM_PROC.kill()
        STREAM_PROC = None
        CURRENT = {}
        return jsonify({"message":"Stream stopped"}), 200

@app.route('/status', methods=['GET'])
def status():
    running = bool(STREAM_PROC and STREAM_PROC.poll() is None)
    info = dict(CURRENT)
    info['running'] = running
    return jsonify(info), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
