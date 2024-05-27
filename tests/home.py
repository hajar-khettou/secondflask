from flask import Flask, flash, session, render_template, request, redirect, url_for, jsonify
from datetime import timedelta
import requests
from flask_cors import CORS
import pyrebase
import os
from flask_session import Session



app = Flask(__name__)
# For Flask:
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:3000"}})  # Only allow this origin to access your API routes


# The URL for the Rasa server to send messages
RASA_API_URL = 'http://localhost:5005/webhooks/rest/webhook'

config = {
    'apiKey': "AIzaSyDxO-WC60pOCjlahv31Park9-vNR6734UI",
    'authDomain': "authentpy.firebaseapp.com",
    'projectId': "authentpy",
    'storageBucket': "authentpy.appspot.com",
    'messagingSenderId': "724408922965",
    'appId': "1:724408922965:web:0510ff18f006efea9b75dc",
    'measurementId': "G-JMTRQKZLZT",
    'databaseURL': "https://authentpy-default-rtdb.firebaseio.com/",
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
secret_key = 'secretjijiapplication'


app.config['SECRET_KEY'] = 'secretjijiapplication'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Ensure the session directory exists and is writable
session_file_dir = './session_files'
if not os.path.exists(session_file_dir):
    os.makedirs(session_file_dir)

# Check if the directory is writable
if os.access(session_file_dir, os.W_OK):
    print(f"Directory {session_file_dir} is writable")
else:
    print(f"Directory {session_file_dir} is not writable")

app.config['SESSION_FILE_DIR'] = session_file_dir

Session(app)

ADMIN_USER_ID = os.getenv('ADMIN_USER_ID', 'ktlboVCr3kf4mdnQufC8NMODgF13')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'khettouhajar@gmail.com')



@app.before_request
def before_request():
    print("Session state before request:", dict(session))

@app.after_request
def after_request(response):
    print("Session state after request:", dict(session))
    return response



@app.route('/check_admin')
def check_admin():
    return f"Admin ID: {ADMIN_USER_ID}, Admin Email: {ADMIN_EMAIL}"


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            id_token = user.get('idToken')
            if id_token:
                session['idToken'] = id_token
                print("ID Token set in session:", session.get('idToken'))  # Debug print
                # Verify the ID token and get user account details
                user_details = auth.get_account_info(id_token)
                user_data = user_details['users'][0]
                email_verified = user_data['emailVerified']
                admin_email = os.getenv('ADMIN_EMAIL')
                admin_user_id = os.getenv('ADMIN_USER_ID')
                if email_verified and email == admin_email and user_data['localId'] == admin_user_id:
                    session['user_id'] = user_data['localId']
                    session['user_email'] = email
                    session['is_admin'] = True
                    return redirect(url_for('admin_dashboard'))
                else:
                    print("Unauthorized access attempt or email not verified.")
                    return "Unauthorized", 403
        except KeyError as e:
            print(f"Key error: {str(e)} - Check the keys in your returned user data")
            return f"Login Failed: Key error {str(e)}", 401
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return f"Login Failed: {str(e)}", 401
    return render_template('admin_login.html')

def is_admin():
    # Check against session values directly
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    return user_email == ADMIN_EMAIL and user_id == ADMIN_USER_ID

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():  # Assuming this function checks your admin condition correctly
        return redirect(url_for('admin_login'))  # Redirect to login if not admin

    # Assuming 'idToken' is stored in session after successful admin login
    id_token = session.get('idToken')
    try:
        # Fetch reservations from the database using the authenticated user's token
        reservations = db.child("reservations").get(id_token).val()
        if reservations is None:
            reservations = {}  # Fallback to an empty dictionary if no data is found
    except Exception as e:
        print(f"Error fetching reservations: {str(e)}")
        reservations = {}  # Use an empty dictionary on error to avoid passing None to Jinja

    return render_template('admin_dashboard.html', reservations=reservations)






@app.route('/', methods=['GET'])
def home():
    # Redirect users to the sign-up page by default
    return redirect(url_for('signup'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('firstp'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            print("User created: ", user)  # Log the response from Firebase
            auth.send_email_verification(user['idToken'])
            return redirect(url_for('thank_you', message='verification_sent'))
        except Exception as e:
            print("Error creating user:", e)  # Log any errors
            return render_template('signup.html', error=str(e))
    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        session.clear()  # Clear the session first
        email = request.form.get('emailInput')
        password = request.form.get('passwordInput')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            id_token = user.get('idToken')
            email_verified = user['emailVerified']
            if id_token and email_verified:
                session['idToken'] = id_token
                session['user_id'] = user['localId']
                session['user_email'] = user['email']
                session.modified = True
                return redirect(url_for('firstp'))
            elif not email_verified:
                flash("Please verify your email before logging in.", "warning")
            else:
                flash("Login failed: ID token not found.", "error")
        except Exception as e:
            flash(f"Login failed: {str(e)}", "error")
    return render_template('signin.html')




@app.route('/firstp', methods=['GET', 'POST'])
def firstp():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    return render_template('firstp.html')


@app.route('/ticket')
def ticket():
    return render_template('ticket.html')
@app.route('/chatbot')
def chatbot():
    if 'user' not in session:
        # Redirect to login if user not logged in
        return redirect(url_for('signin'))
    # Render bot chat interface if logged in
    return render_template('firstp.html')



@app.route('/thank_you', methods=['GET', 'POST'])
def thank_you():
    message = request.args.get('message', 'Default message if none provided')
    return render_template('thankyou.html', message=message)



@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    session.permanent = True
    print("Entering reservation route")

    if request.method == 'POST':
        print("Session contents before request:", dict(session))  # Debugging session state

        if 'idToken' not in session:
            print("idToken not found in session, redirecting to login.")
            flash("User is not authenticated.", "error")
            return redirect(url_for('login'))

        print("idToken found:", session['idToken'])

        hardware = request.form.get('hardware')
        software = request.form.get('software')

        # Check if either hardware or software is filled, but not both
        if (hardware and software) or (not hardware and not software):
            flash("Please specify either hardware or software, not both.", "error")
            return render_template('ticket.html')

        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'department': request.form.get('select1'),
            'category': request.form.get('category'),
            'software': software if software else "No software specified",
            'hardware': hardware if hardware else "No hardware specified",
            'description': request.form.get('message')
        }
        print("Data collected:", data)  # Debugging what data is being processed

        try:
            new_reservation = db.child("reservations").push(data, session['idToken'])
            reservation_id = new_reservation['name']
            session['reservation_id'] = reservation_id
            print("Reservation ID set in session:", session['reservation_id'])
            return redirect(url_for('success'))
        except Exception as e:
            print(f"Failed to push data: {str(e)}")
            flash(f"Failed to reserve: {str(e)}", "error")
            return render_template('ticket.html')

    return render_template('ticket.html')


@app.route('/delete_reservation/<reservation_id>')
def delete_reservation(reservation_id):
    id_token = session.get('idToken')
    if not id_token:
        flash("User is not authenticated.", "error")
        return redirect(url_for('signin'))

    # Now use id_token to perform the deletion, assuming it's necessary for database operations
    try:
        db.child("reservations").child(reservation_id).remove(id_token)
        flash("Reservation deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete reservation: {e}", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/respond_to_reservation/<reservation_id>', methods=['GET', 'POST'])
def respond_to_reservation(reservation_id):
    id_token = session.get('idToken')
    if not id_token:
        flash("User authentication required.", "error")
        return redirect(url_for('admin_login'))

    try:
        reservation = db.child("reservations").child(reservation_id).get(id_token).val()
        if not reservation:
            return redirect(url_for('reservations_dashboard'))  # Redirect back to the dashboard

        if request.method == 'POST':
            response_message = request.form['message']
            db.child("reservations").child(reservation_id).update({'response': response_message}, id_token)
            flash("Response saved successfully!", "success")
            return redirect(url_for('reservations_dashboard'))  # Redirect to the dashboard after posting a response
        else:
            # Pass reservation details including any existing response to the form for possible editing
            return render_template('respond_form.html', reservation_id=reservation_id, reservation=reservation)
    except Exception as e:
        return redirect(url_for('reservations_dashboard'))

@app.route('/reservations_dashboard')
def reservations_dashboard():
    # Fetch the reservation ID from the session
    reservation_id = session.get('reservation_id')
    if not reservation_id:
        return redirect(url_for('reservation'))  # Redirect to reservation page if no ID is found

    id_token = session.get('idToken')
    if not id_token:
        flash("User authentication required.", "error")

    try:
        # Fetch reservation details from Firebase using the reservation ID
        reservation = db.child("reservations").child(reservation_id).get(id_token).val()
        if not reservation:
            return redirect(url_for('reservation'))  # Redirect back if no reservation data is found

        # If reservation data is found, render it on the reservations dashboard
        return render_template('view_reservation.html', reservation=reservation)
    except Exception as e:
        return redirect(url_for('reservation'))  # Redirect on error

@app.route('/logout')
def logout():
    session.clear()  # This will remove all the data in the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('signin'))



@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/send_message', methods=['POST', 'OPTIONS'])
def send_message():
    if request.method == 'OPTIONS':
        return ('', 204)
    user_message = request.json['message']
    try:
        response = requests.post(RASA_API_URL, json={"sender": "user", "message": user_message})
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed fto fetch response from Rasa"}), response.status_code
    except requests.exceptions.RequestException as e:
        print(e)
        return jsonify({"error": "Connection to Rasa server failed"}), 503

if __name__ == '__main__':
    app.run(debug=True, port=3000)