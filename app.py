from flask import Flask, request, render_template, redirect, url_for, session, jsonify 
import MySQLdb
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to a secure secret key

def get_db_connection():
    return MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",
        db="project1",
        port=3306
    )

# ---------- Authentication Routes ----------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "login":
            username = request.form["username"]
            password = request.form["password"]

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Assuming that user[0] is the user's ID and user[2] is the stored password.
            if user and user[2] == password:
                # Store the user's ID in session
                session["user_id"] = user[0]
                return redirect(url_for('welcome'))
            else:
                return render_template("login.html", error="Incorrect username or password!")

        elif action == "register":
            username = request.form["username"]
            password = request.form["password"]

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('login'))

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Main User Routes ----------

@app.route("/new.html")
def welcome():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("new.html")

@app.route("/service.html")
def service():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("service.html")

@app.route("/acservices.html")
def acservices():
    if not session.get("user_id"):
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name, phone, service_name FROM service_provider WHERE service_name = 'AC'")
    providers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("acservices.html", providers=providers)




@app.route("/plumber.html")
def plumber():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name, phone, service_name FROM service_provider WHERE service_name = 'Plumbing Specialist'")
    providers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("plumber.html",providers=providers)

@app.route("/painting.html")
def painting():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("painting.html")

@app.route("/electrical.html")
def electrical():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT name, phone, service_name FROM service_provider WHERE service_name = 'Electrical'")
    providers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("electrical.html", providers=providers)

@app.route("/carpenter.html")
def carpenter():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("carpenter.html")

@app.route("/cleaning.html")
def cleaning_service():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("cleaning.html")

@app.route("/bookings.html")
def mybooking():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("bookings.html")

# ---------- Booking API Routes ----------


@app.route("/get-bookings", methods=["GET"])
def get_bookings():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
                        SELECT id, customer_name, service_name, service_type, 
                            DATE_FORMAT(booking_date, '%%Y-%%m-%%d') AS booking_date, 
                            street_address, city, postal_code, booking_status, admin_message,
                            assigned_provider
                        FROM bookings WHERE user_id = %s
                    """, (user_id,))

        bookings = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "bookings": bookings}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Optional: Check that the booking belongs to the current user
        cursor.execute("DELETE FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Booking canceled successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/book-cleaning", methods=["POST"])
def book_cleaning():
    try:
        customer_name = request.form.get("customer_name")
        contact = request.form.get("contact")
        service_name = request.form.get("service_name")
        service_type = request.form.get("service_type")
        date = request.form.get("date")
        street = request.form.get("street")
        city = request.form.get("city")
        postal_code = request.form.get("postal_code")

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "User not logged in"}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        query = """
            INSERT INTO bookings 
            (user_id, customer_name, contact, service_name, service_type, booking_date, street_address, city, postal_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (user_id, customer_name, contact, service_name, service_type, date, street, city, postal_code)

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Booking Confirmed"}), 200

    except mysql.connector.Error as err: # type: ignore
        print(f"SQL Error: {err}")
        return jsonify({"success": False, "message": str(err)}), 500

    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ---------- Contact and Admin Routes ----------

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contact (name, email, phone, message) VALUES (%s, %s, %s, %s)", 
                       (name, email, phone, message))
        conn.commit()
        cursor.close()
        conn.close()

        return render_template('contact.html', success="Your message has been sent!")

    return render_template("contact.html")

@app.route("/contact.html")
def contact_html():
    return render_template("contact.html")


# admin

@app.route('/admin', methods=["GET", "POST"])
def admin():
    if 'logged_in' not in session or not session.get('logged_in'):
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            # Hardcoded admin credentials
            if username == "admin" and password == "1234":
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('admin'))
            else:
                return render_template('admin.html', error="Incorrect username or password.")
        return render_template('admin.html')

    users = []
    contacts = []
    bookings = []

    if request.method == "POST":
        action = request.form.get('action')
        if action == "show_contacts":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contact")
            contacts = cursor.fetchall()
            cursor.close()
            conn.close()
        elif action == "show_bookings":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bookings")
            bookings = cursor.fetchall()
            cursor.close()
            conn.close()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            cursor.close()
            conn.close()

    return render_template('admin.html', users=users, contacts=contacts, bookings=bookings)

@app.route('/delete_user/<int:user_id>', methods=["POST"])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_contact/<int:contact_id>', methods=["POST"])
def delete_contact(contact_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM contact WHERE id = %s", (contact_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_booking/<int:booking_id>', methods=["POST"])
def delete_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin'))

@app.route('/update_booking/<int:booking_id>', methods=["POST"])
def update_booking(booking_id):
    # Ensure only an admin can perform this action
    if 'logged_in' not in session or not session.get('logged_in'):
        return redirect(url_for('admin'))

    # Get the admin's message and the desired booking status
    admin_message = request.form.get('admin_message')
    booking_status = request.form.get('booking_status')  # expected 'pending' or 'completed'
    
    # Update the booking in the database
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            "UPDATE bookings SET admin_message=%s, booking_status=%s WHERE id=%s",
            (admin_message, booking_status, booking_id)
        )
        conn.commit()
        
        # Fetch the customer's contact number from the booking record
        cursor.execute("SELECT contact FROM bookings WHERE id = %s", (booking_id,))
        result = cursor.fetchone()
        customer_contact = result.get('contact') if result else None
        
        # If a contact number is found, send the SMS via Twilio
        if customer_contact:
            from twilio.rest import Client

            # Twilio credentials (use secure storage or environment variables in production)
            ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Your Twilio number

            client = Client(ACCOUNT_SID, AUTH_TOKEN)
            message = client.messages.create(
                body=admin_message,
                from_=TWILIO_PHONE_NUMBER,
                to=customer_contact
            )
            print(f"Message sent with SID: {message.sid}")

    except Exception as e:
        conn.rollback()
        print(f"Error updating booking: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/assign_provider/<int:booking_id>', methods=["GET", "POST"])
def assign_provider(booking_id):
    if 'logged_in' not in session or not session.get('logged_in'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the booking
    cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        cursor.close()
        conn.close()
        return "Booking not found", 404

    # Fetch all service providers
    cursor.execute("SELECT id, name, service_name FROM service_provider")
    providers = cursor.fetchall()

    # On form submission
    if request.method == "POST":
        selected_provider_id = request.form.get("provider_id")
        if selected_provider_id:
            cursor.execute("SELECT name FROM service_provider WHERE id = %s", (selected_provider_id,))
            provider = cursor.fetchone()
            if provider:
                provider_name = provider['name']
                cursor.execute("UPDATE bookings SET assigned_provider = %s WHERE id = %s", (provider_name, booking_id))
                conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin'))

    cursor.close()
    conn.close()
    return render_template("assign_provider.html", booking=booking, providers=providers)





if __name__ == "__main__":
    app.run(debug=True)