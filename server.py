from flask import Flask, request, jsonify
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import MutualTLSChannelError
import psycopg2
from psycopg2.extras import execute_values
from googleapiclient.errors import HttpError

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1SvGvOXTO-SMloCklizlcN252uaaOw-9XxEL-x-fDXGw"
RANGE_NAME = "Sheet1"
db_name = "superjoin"
db_user = "postgres"
db_password = "IamaCSstudent"
db_host = "localhost"

# creates an instance of the db connection and returns it
def get_db_instance():
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=5432
        )
        return conn
    except Exception as e:
        print(e)
        exit(1)

# creates a service connection to google sheets
def sheet_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=5000)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    try:
        service = build("sheets", "v4", credentials=creds)
        return service
    except MutualTLSChannelError as err:
        print(err)

# fetch the data in the database
def fetch_db(conn):
    cursor = conn.cursor()
    cursor.execute("""select * from company""")
    rows = cursor.fetchall()
    return rows

# fetch the data in the sheet practically became useless after discovering apps script
def fetch_sheet(sheet_service, id, sheet_name):
    sheet = sheet_service.spreadsheets()
    res = sheet.values().get(spreadsheetId=id, range=sheet_name).execute()

    vals = res.get("values", [])

    if not vals:
        print("Sheet is empty!")
        return
    
    return vals

# updates the database, generally triggered by edit from google apps script
def update_db(vals):
    conn = get_db_instance()
    cursor = conn.cursor()
    vals = vals[1:]
    
    cursor.execute("""truncate table company""")
    cursor.execute("""ALTER SEQUENCE company_id_seq RESTART WITH 1""")
    
    execute_values(cursor,
        """insert into company (company, contact, country) values %s""",
        [tuple(row) for row in vals]
    )
    conn.commit()
    conn.close()

# updates the google sheet, generally triggered by edit from the database
def update_sheet(sheet_service, id, sheet_name, data):
    no_index_data = [x[1:] for x in data]
    print(no_index_data)
    body = {"values": no_index_data}
    try:
        sheet_service.spreadsheets().values().update(
            spreadsheetId=id, range=sheet_name, valueInputOption="USER_ENTERED", body=body
        ).execute()
    except HttpError as e:
        print(f"Encountered error: {e} while trying to update sheet!")

# Start of CRUD

# Create
@app.route("/db/add", methods=["POST"])     # Route tested with Postman
def add_data():
    data = request.json
    conn = get_db_instance()
    cursor = conn.cursor()
    try:
        cursor.execute("""insert into company (company, contact, country) values (%s, %s, %s)""", (data["company"], data["contact"], data["country"]))
        conn.commit()
        sheet_sync()
        conn.close()
        return jsonify({"message": "Data added successfully"}), 200
    except Exception as e:
        print(f"Error: {e}")

# Read
@app.route("/db/fetch", methods=["GET"])        # Route tested with Postman
def fetch_data():
    conn = get_db_instance()
    try:
        data = fetch_db(conn)
        conn.close()
        return jsonify(data), 200
    except Exception as e:
        print(f"Error: {e}")

# Update
@app.route("/db/update/<int:id>", methods=["PUT"])     # Route tested with Postman
def update(id):
    data = request.json
    conn = get_db_instance()
    cursor = conn.cursor()

    try:
        for key, val in data.items():
            # print(key, val)
            cursor.execute(f"""update company set {key} = %s where id = %s""", (val, id,))
        conn.commit()
        conn.close()
        sheet_sync()
        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        print(f"Error: {e}")

# Delete
@app.route("/db/delete/<int:id>", methods=["DELETE"])       # Route tested with Postman
def delete(id):
    conn = get_db_instance()
    cursor = conn.cursor()
    try:
        cursor.execute("""delete from company where id = %s""", (id,))
        conn.commit()
        conn.close()
        sheet_sync()
        return jsonify({"message": "Data deleted successfully"}), 200
    except Exception as e:
        print(f"Error: {e}")

# Loading data from Apps Scripts
@app.route("/api/receiver", methods=["POST"])       # Tested
def receive_data():
    """
    Receives data from the Google Apps Script and stores it in a database.
    """
    try:
        data = request.json

        # Process the data and store it in your database
        # Replace this with your database logic
        update_db(data)
        # print(data)
        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

# Sheet sync
def sheet_sync():
    conn = get_db_instance()
    sheet_service_instance = sheet_service()
    data = fetch_db(conn)
    update_sheet(sheet_service_instance, SPREADSHEET_ID, RANGE_NAME, data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
