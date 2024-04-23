from flask import Flask, render_template, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows the server to accept requests from different domains than its own, which is essential for APIs accessed by web pages from other domains.

# The URL for the Rasa server to send messages
RASA_API_URL = 'http://localhost:5005/webhooks/rest/webhook'

@app.route('/')
def home():
    """Render the home page with the chat interface."""
    return render_template('index.html')  # Ensure you have 'index.html' in your templates directory

@app.route('/send_message', methods=['POST', 'OPTIONS'])
def send_message():
    """Send message to Rasa server and get the response, handle OPTIONS preflight request."""
    if request.method == 'OPTIONS':
        # The default 200 OK response with CORS headers is fine.
        # Flask-CORS handles this response automatically with the above `after_request_func`.
        return ('', 204)
    user_message = request.json['message']
    try:
        response = requests.post(RASA_API_URL, json={
            "sender": "user",
            "message": user_message
        })
        # Check if the request was successful
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch response from Rasa"}), response.status_code
    except requests.exceptions.RequestException as e:
        # Log the error and return an error message
        print(e)
        return jsonify({"error": "Connection to Rasa server failed"}), 503

if __name__ == '__main__':
    app.run(debug=True, port=3000)
