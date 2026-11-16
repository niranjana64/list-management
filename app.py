import os
from datetime import date, datetime, timedelta
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

REGIONS = {"International", "North", "South", "SouthCentral", "West"}
STATUSES = {"RECEIVED", "ACKNOWLEDGED", "WIP", "TECH-COMPLETED", "CLOSED"}


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "admin"),
        database=os.getenv("DB_NAME", "list_management_db"),
    )


def record_to_json(row):
    for key in ("created_at", "updated_at"):
        if row.get(key) is not None:
            row[key] = row[key].isoformat(sep=" ")
    return row


def error_response(message, status=400):
    return jsonify({"ok": False, "error": message}), status


@app.get("/")
def dashboard():
    return render_template("index.html")


@app.get("/api/health")
def health():
    try:
        connection = get_db_connection()
        connection.close()
        return jsonify({"ok": True, "message": "Flask and MySQL connection successful"})
    except Error as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500


@app.get("/api/options")
def get_filter_options():
    """Return distinct locations so the Location filter stays data-driven."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT location FROM records WHERE location <> '' ORDER BY location")
        locations = [row[0] for row in cursor.fetchall()]
        return jsonify({
            "locations": locations,
            "regions": sorted(REGIONS),
            "statuses": ["RECEIVED", "ACKNOWLEDGED", "WIP", "TECH-COMPLETED", "CLOSED"],
        })
    except Error as exc:
        return jsonify({"error": "Could not load filter options", "details": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_date_bounds():
    """Return inclusive start and exclusive end datetimes for the selected period."""
    period = request.args.get("date", "all")
    today = date.today()
    if period == "last7":
        start = today - timedelta(days=6)
        return datetime.combine(start, datetime.min.time()), datetime.combine(today + timedelta(days=1), datetime.min.time())
    if period == "last30":
        start = today - timedelta(days=29)
        return datetime.combine(start, datetime.min.time()), datetime.combine(today + timedelta(days=1), datetime.min.time())
    if period == "last90":
        start = today - timedelta(days=89)
        return datetime.combine(start, datetime.min.time()), datetime.combine(today + timedelta(days=1), datetime.min.time())
    if period == "this_month":
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return datetime.combine(start, datetime.min.time()), datetime.combine(next_month, datetime.min.time())
    if period == "last_month":
        this_month = today.replace(day=1)
        last_month_end = this_month
        last_month_start = (this_month - timedelta(days=1)).replace(day=1)
        return datetime.combine(last_month_start, datetime.min.time()), datetime.combine(last_month_end, datetime.min.time())
    fy_map = {
        "fy2026": (date(2026, 4, 1), date(2027, 4, 1)),
        "fy2025": (date(2025, 4, 1), date(2026, 4, 1)),
        "fy2024": (date(2024, 4, 1), date(2025, 4, 1)),
    }
    if period in fy_map:
        start, end = fy_map[period]
        return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())
    if period == "custom":
        start_text = request.args.get("start_date", "")
        end_text = request.args.get("end_date", "")
        try:
            start = date.fromisoformat(start_text)
            end = date.fromisoformat(end_text)
            if end < start:
                raise ValueError("End date must be on or after start date.")
            return datetime.combine(start, datetime.min.time()), datetime.combine(end + timedelta(days=1), datetime.min.time())
        except ValueError as exc:
            raise ValueError("Choose a valid custom start and end date. " + str(exc))
    return None, None


@app.get("/api/records")
def get_records():
    connection = None
    cursor = None
    try:
        clauses = []
        params = []

        search = request.args.get("search", "").strip()
        if search:
            like = f"%{search}%"
            clauses.append("(record_title LIKE %s OR description LIKE %s OR location LIKE %s OR region LIKE %s OR status LIKE %s)")
            params.extend([like, like, like, like, like])

        locations = request.args.getlist("location")
        if locations:
            placeholders = ", ".join(["%s"] * len(locations))
            clauses.append(f"location IN ({placeholders})")
            params.extend(locations)

        region = request.args.get("region", "").strip()
        if region:
            if region not in REGIONS:
                return error_response("Invalid region filter.")
            clauses.append("region = %s")
            params.append(region)

        status = request.args.get("status", "").strip()
        if status:
            if status not in STATUSES:
                return error_response("Invalid status filter.")
            clauses.append("status = %s")
            params.append(status)

        start, end = get_date_bounds()
        if start and end:
            clauses.append("created_at >= %s AND created_at < %s")
            params.extend([start, end])

        sql = """SELECT id, record_title, description, location, region, status, created_at, updated_at
                 FROM records"""
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC, id DESC"

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = [record_to_json(row) for row in cursor.fetchall()]
        return jsonify(rows)
    except ValueError as exc:
        return error_response(str(exc))
    except Error as exc:
        return jsonify({"error": "Database query failed", "details": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def validate_record(data):
    title = str(data.get("record_title", "")).strip()
    description = str(data.get("description", "")).strip()
    location = str(data.get("location", "")).strip()
    region = str(data.get("region", "")).strip()
    status = str(data.get("status", "RECEIVED")).strip()

    if not title:
        return None, "Record title is required."
    if not location:
        return None, "Location is required."
    if region not in REGIONS:
        return None, "Choose a valid region."
    if status not in STATUSES:
        return None, "Choose a valid status."
    if len(title) > 200:
        return None, "Record title must be 200 characters or fewer."
    if len(location) > 100:
        return None, "Location must be 100 characters or fewer."
    return {
        "record_title": title,
        "description": description or None,
        "location": location,
        "region": region,
        "status": status,
    }, None


@app.post("/api/records")
def create_record():
    data = request.get_json(silent=True) or {}
    record, validation_error = validate_record(data)
    if validation_error:
        return error_response(validation_error)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO records (record_title, description, location, region, status)
               VALUES (%s, %s, %s, %s, %s)""",
            (record["record_title"], record["description"], record["location"], record["region"], record["status"]),
        )
        connection.commit()
        new_id = cursor.lastrowid
        return jsonify({"ok": True, "message": "Record created successfully.", "id": new_id}), 201
    except Error as exc:
        if connection:
            connection.rollback()
        return jsonify({"error": "Could not create record", "details": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.put("/api/records/<int:record_id>")
def update_record(record_id):
    data = request.get_json(silent=True) or {}
    record, validation_error = validate_record(data)
    if validation_error:
        return error_response(validation_error)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """UPDATE records
               SET record_title=%s, description=%s, location=%s, region=%s, status=%s
               WHERE id=%s""",
            (record["record_title"], record["description"], record["location"], record["region"], record["status"], record_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            cursor.execute("SELECT id FROM records WHERE id=%s", (record_id,))
            exists = cursor.fetchone()
            if not exists:
                return error_response("Record not found.", 404)
        return jsonify({"ok": True, "message": "Record updated successfully."})
    except Error as exc:
        if connection:
            connection.rollback()
        return jsonify({"error": "Could not update record", "details": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.delete("/api/records/<int:record_id>")
def delete_record(record_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM records WHERE id=%s", (record_id,))
        connection.commit()
        if cursor.rowcount == 0:
            return error_response("Record not found.", 404)
        return jsonify({"ok": True, "message": "Record deleted successfully."})
    except Error as exc:
        if connection:
            connection.rollback()
        return jsonify({"error": "Could not delete record", "details": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)
