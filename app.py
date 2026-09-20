from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os

app = Flask(__name__)

# MySQL Database Configuration
# REPLACE 'root123' WITH YOUR ACTUAL MYSQL ROOT PASSWORD!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_mysql_password',
    'database': 'hydrogrid_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# Home Dashboard
@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:

        cursor.execute("SELECT COUNT(*) AS count FROM consumers")
        total_consumers = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) AS count FROM complaints WHERE status != 'Resolved'")
        active_complaints = cursor.fetchone()['count']
        cursor.execute("SELECT SUM(total_amount) AS revenue FROM billing WHERE payment_status = 'Paid'")
        total_revenue = cursor.fetchone()['revenue'] or 0
    conn.close()
    return render_template('index.html', consumers=total_consumers, complaints=active_complaints, revenue=total_revenue)

# View Consumers (VIEW Command)
@app.route('/consumers')
def consumers():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM consumers")
        consumer_list = cursor.fetchall()
    conn.close()
    return render_template('consumers.html', consumers=consumer_list)

# Add New Consumer (INSERT Command)
@app.route('/add_consumer', methods=['POST'])
def add_consumer():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    conn_type = request.form['connection_type']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "INSERT INTO consumers (name, email, phone, address, connection_type) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (name, email, phone, address, conn_type))
        conn.commit()
    conn.close()
    return redirect(url_for('consumers'))

# Delete Consumer (DELETE Command)
@app.route('/delete_consumer/<int:id>')
def delete_consumer(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM consumers WHERE consumer_id = %s", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('consumers'))

# View Complaints & Maintenance (JOIN / VIEW / UPDATE Commands)
@app.route('/complaints')
def complaints():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """
            SELECT c.complaint_id, c.leak_location, c.severity, c.status, 
                   u.name AS consumer_name, e.engineer_name 
            FROM complaints c
            JOIN consumers u ON c.consumer_id = u.consumer_id
            LEFT JOIN engineers_maintenance e ON c.complaint_id = e.complaint_id
        """
        cursor.execute(sql)
        complaint_list = cursor.fetchall()
    conn.close()
    return render_template('complaints.html', complaints=complaint_list)

# Update Complaint Status (UPDATE Command)
@app.route('/resolve_complaint/<int:id>')
def resolve_complaint(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE complaints SET status = 'Resolved' WHERE complaint_id = %s", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('complaints'))
@app.route('/add_complaint', methods=['POST'])
def add_complaint():
    consumer_id = request.form['consumer_id']
    location = request.form['location']
    severity = request.form['severity']
    engineer = request.form['assigned_engineer']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO complaints (consumer_id, location, severity, assigned_engineer, status) VALUES (%s, %s, %s, %s, 'Pending')",
            (consumer_id, location, severity, engineer)
        )
        conn.commit()
    conn.close()
    return redirect('/complaints')

if __name__ == '__main__':
    app.run(debug=True)
