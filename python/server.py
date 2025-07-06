#!/usr/bin/env python3
"""
Web-based Audio Controller System
A single-file web application for remote audio playback control
"""

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
import os
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active rooms and their info
rooms = {}

# HTML Templates
CONTROLLER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Audio Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f7;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1d1d1f;
            margin-bottom: 30px;
            text-align: center;
        }
        .room-code {
            background: #007aff;
            color: white;
            font-size: 36px;
            font-weight: bold;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
            letter-spacing: 3px;
            font-family: monospace;
        }
        .play-button {
            width: 100%;
            padding: 20px;
            font-size: 24px;
            background: #34c759;
            color: white;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .play-button:hover {
            background: #2da548;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 199, 89, 0.3);
        }
        .play-button:active {
            transform: translateY(0);
        }
        .play-button:disabled {
            background: #c7c7cc;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            background: #f0f0f5;
        }
        .connected { color: #34c759; }
        .disconnected { color: #ff3b30; }
        .info {
            background: #e5f0ff;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: center;
            color: #007aff;
        }
        .receiver-count {
            font-size: 18px;
            font-weight: 600;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Audio Controller</h1>
        
        <div class="info">
            Share this room code with receivers:
        </div>
        
        <div class="room-code" id="roomCode">{{ room_code }}</div>
        
        <div class="status">
            <div class="receiver-count">
                <span id="receiverCount">0</span> receiver(s) connected
            </div>
            <div id="connectionStatus" class="disconnected">
                Connecting...
            </div>
        </div>
        
        <button class="play-button" id="playButton" onclick="playSound()" disabled>
            <span>🔊</span>
            <span>PLAY SOUND</span>
        </button>
        
        <div id="playbackStatus" style="text-align: center; margin-top: 20px; opacity: 0; transition: opacity 0.3s;">
            <span style="color: #34c759;">✓ Sound played!</span>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const roomCode = '{{ room_code }}';
        const socket = io();
        let connected = false;
        let receiverCount = 0;

        socket.on('connect', () => {
            connected = true;
            document.getElementById('connectionStatus').textContent = 'Connected';
            document.getElementById('connectionStatus').className = 'connected';
            socket.emit('controller_join', {room_code: roomCode});
        });

        socket.on('disconnect', () => {
            connected = false;
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            document.getElementById('connectionStatus').className = 'disconnected';
            document.getElementById('playButton').disabled = true;
        });

        socket.on('receiver_update', (data) => {
            receiverCount = data.count;
            document.getElementById('receiverCount').textContent = receiverCount;
            document.getElementById('playButton').disabled = !connected || receiverCount === 0;
        });

        function playSound() {
            if (connected && receiverCount > 0) {
                socket.emit('play_sound', {room_code: roomCode});
                
                // Show feedback
                const status = document.getElementById('playbackStatus');
                status.style.opacity = '1';
                setTimeout(() => {
                    status.style.opacity = '0';
                }, 2000);
            }
        }
    </script>
</body>
</html>
"""

RECEIVER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Audio Receiver</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f7;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1d1d1f;
            margin-bottom: 30px;
            text-align: center;
        }
        .join-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        input[type="text"] {
            padding: 15px;
            font-size: 20px;
            border: 2px solid #e5e5ea;
            border-radius: 10px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-family: monospace;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #007aff;
        }
        button {
            padding: 15px 30px;
            font-size: 18px;
            background: #007aff;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            background: #0051d5;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 122, 255, 0.3);
        }
        button:disabled {
            background: #c7c7cc;
            cursor: not-allowed;
            transform: none;
        }
        .audio-upload {
            margin: 20px 0;
            padding: 20px;
            border: 2px dashed #007aff;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .audio-upload:hover {
            background: #f0f7ff;
        }
        .upload-label {
            display: block;
            cursor: pointer;
            color: #007aff;
            font-weight: 600;
        }
        #fileInput {
            display: none;
        }
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            font-weight: 600;
        }
        .status.ready {
            background: #d1f7d1;
            color: #34c759;
        }
        .status.not-ready {
            background: #ffe5e5;
            color: #ff3b30;
        }
        .hidden {
            display: none;
        }
        .audio-info {
            background: #f0f0f5;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
        }
        .play-indicator {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(52, 199, 89, 0.9);
            color: white;
            padding: 40px 60px;
            border-radius: 20px;
            font-size: 36px;
            font-weight: bold;
            box-shadow: 0 10px 50px rgba(0,0,0,0.3);
            z-index: 1000;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎧 Audio Receiver</h1>
        
        <div id="joinSection">
            <form class="join-form" onsubmit="joinRoom(event)">
                <input type="text" id="roomCodeInput" placeholder="Enter Room Code" 
                       maxlength="6" required autocomplete="off">
                <button type="submit">Join Room</button>
            </form>
        </div>
        
        <div id="audioSection" class="hidden">
            <div class="audio-upload">
                <label for="fileInput" class="upload-label">
                    📁 Click to upload audio file (MP3, WAV, OGG)
                </label>
                <input type="file" id="fileInput" accept="audio/*" onchange="handleFileUpload(event)">
            </div>
            
            <div id="audioInfo" class="audio-info hidden">
                <div>Current audio: <strong id="fileName"></strong></div>
                <audio id="audioPlayer" controls style="width: 100%; margin-top: 10px;"></audio>
            </div>
            
            <div id="status" class="status not-ready">
                No audio file loaded
            </div>
            
            <button onclick="leaveRoom()" style="background: #ff3b30; margin-top: 20px;">
                Leave Room
            </button>
        </div>
    </div>
    
    <div id="playIndicator" class="play-indicator">
        🔊 Playing!
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let currentRoom = null;
        let audioReady = false;

        function joinRoom(event) {
            event.preventDefault();
            const roomCode = document.getElementById('roomCodeInput').value.toUpperCase();
            socket.emit('receiver_join', {room_code: roomCode});
        }

        function leaveRoom() {
            if (currentRoom) {
                socket.emit('receiver_leave', {room_code: currentRoom});
                currentRoom = null;
                document.getElementById('joinSection').classList.remove('hidden');
                document.getElementById('audioSection').classList.add('hidden');
                document.getElementById('roomCodeInput').value = '';
            }
        }

        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (file && file.type.startsWith('audio/')) {
                const url = URL.createObjectURL(file);
                const audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.src = url;
                
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('audioInfo').classList.remove('hidden');
                document.getElementById('status').textContent = 'Ready to play!';
                document.getElementById('status').className = 'status ready';
                
                audioReady = true;
            }
        }

        socket.on('join_success', (data) => {
            currentRoom = data.room_code;
            document.getElementById('joinSection').classList.add('hidden');
            document.getElementById('audioSection').classList.remove('hidden');
        });

        socket.on('join_error', (data) => {
            alert(data.message);
            document.getElementById('roomCodeInput').value = '';
        });

        socket.on('play_command', () => {
            if (audioReady) {
                const audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.play();
                
                // Show play indicator
                const indicator = document.getElementById('playIndicator');
                indicator.style.display = 'block';
                setTimeout(() => {
                    indicator.style.display = 'none';
                }, 2000);
            }
        });

        socket.on('room_closed', () => {
            alert('The controller has closed this room.');
            leaveRoom();
        });
    </script>
</body>
</html>
"""

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Audio Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f7;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        h1 {
            color: #1d1d1f;
            margin-bottom: 20px;
            font-size: 36px;
        }
        .subtitle {
            color: #86868b;
            margin-bottom: 40px;
            font-size: 18px;
        }
        .options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .option-card {
            background: #f5f5f7;
            padding: 30px;
            border-radius: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
        }
        .option-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .option-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .option-title {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .option-desc {
            color: #86868b;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Web Audio Controller</h1>
        <p class="subtitle">Control audio playback remotely through the web</p>
        
        <div class="options">
            <a href="/controller" class="option-card">
                <div class="option-icon">🎮</div>
                <div class="option-title">Controller</div>
                <div class="option-desc">Create a room and control when audio plays</div>
            </a>
            
            <a href="/receiver" class="option-card">
                <div class="option-icon">🎧</div>
                <div class="option-title">Receiver</div>
                <div class="option-desc">Join a room and play audio on command</div>
            </a>
        </div>
    </div>
</body>
</html>
"""


def generate_room_code():
    """Generate a unique 6-character room code"""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in rooms:
            return code


# Routes
@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/controller")
def controller():
    room_code = generate_room_code()
    rooms[room_code] = {
        "created_at": datetime.now(),
        "controller_sid": None,
        "receivers": [],
    }
    return render_template_string(CONTROLLER_HTML, room_code=room_code)


@app.route("/receiver")
def receiver():
    return render_template_string(RECEIVER_HTML)


# WebSocket Events
@socketio.on("controller_join")
def handle_controller_join(data):
    room_code = data["room_code"]
    if room_code in rooms:
        rooms[room_code]["controller_sid"] = request.sid
        join_room(room_code)
        emit("receiver_update", {"count": len(rooms[room_code]["receivers"])})


@socketio.on("receiver_join")
def handle_receiver_join(data):
    room_code = data["room_code"].upper()
    if room_code not in rooms:
        emit("join_error", {"message": "Invalid room code"})
        return

    join_room(room_code)
    rooms[room_code]["receivers"].append(request.sid)
    emit("join_success", {"room_code": room_code})

    # Notify controller
    if rooms[room_code]["controller_sid"]:
        emit(
            "receiver_update",
            {"count": len(rooms[room_code]["receivers"])},
            room=rooms[room_code]["controller_sid"],
        )


@socketio.on("receiver_leave")
def handle_receiver_leave(data):
    room_code = data["room_code"]
    if room_code in rooms and request.sid in rooms[room_code]["receivers"]:
        leave_room(room_code)
        rooms[room_code]["receivers"].remove(request.sid)

        # Notify controller
        if rooms[room_code]["controller_sid"]:
            emit(
                "receiver_update",
                {"count": len(rooms[room_code]["receivers"])},
                room=rooms[room_code]["controller_sid"],
            )


@socketio.on("play_sound")
def handle_play_sound(data):
    room_code = data["room_code"]
    if room_code in rooms and rooms[room_code]["controller_sid"] == request.sid:
        # Send play command to all receivers in the room
        emit("play_command", room=room_code, skip_sid=request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    # Clean up when someone disconnects
    for room_code, room_data in list(rooms.items()):
        if room_data["controller_sid"] == request.sid:
            # Controller disconnected - notify receivers and close room
            emit("room_closed", room=room_code)
            del rooms[room_code]
        elif request.sid in room_data["receivers"]:
            # Receiver disconnected
            room_data["receivers"].remove(request.sid)
            if room_data["controller_sid"]:
                emit(
                    "receiver_update",
                    {"count": len(room_data["receivers"])},
                    room=room_data["controller_sid"],
                )


if __name__ == "__main__":
    print("Starting Web Audio Controller Server...")
    print("Open http://localhost:5000 in your browser")
    print("\nHow to use:")
    print("1. Controller: Go to /controller to create a room")
    print("2. Receiver: Go to /receiver and enter the room code")
    print("3. Receiver uploads an audio file")
    print("4. Controller clicks 'PLAY SOUND' to trigger playback")

    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
