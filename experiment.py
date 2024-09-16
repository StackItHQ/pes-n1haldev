from flask import Flask, request, jsonify
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import MutualTLSChannelError
from pymongo import MongoClient, errors
from googleapiclient.errors import HttpError

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# MongoDB configuration
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["superjoin"]

table_managers = {}

# Utility function to handle Google Sheets service creation
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

# Utility class to manage collections dynamically in MongoDB
class TableManager:
    def __init__(self, sheet_id, sheet_name, columns=None):
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.collection_name = f"{sheet_name}_{sheet_id}".replace("-", "_")
        self.columns = columns or []

    # Fetch data from a specific collection
    def fetch_data(self):
        collection = db[self.collection_name]
        try:
            data = list(collection.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
            return data
        except errors.PyMongoError as e:
            print(f"Error fetching data: {e}")
            return []

    # Insert data into collection
    def insert_data(self, values):
        collection = db[self.collection_name]
        try:
            docs = [dict(zip(self.columns, value)) for value in values]
            collection.insert_many(docs)
        except errors.BulkWriteError as bwe:
            print(f"Error inserting data: {bwe.details}")
        except Exception as e:
            print(f"General error: {e}")

    # Upsert specific document in the collection based on row and column
    def upsert_data(self, row, column, value):
        collection = db[self.collection_name]
        try:
            query = {"row": row}
            update = {"$set": {self.columns[column - 1]: value}}
            collection.update_one(query, update, upsert=True)
        except errors.PyMongoError as e:
            print(f"Error upserting data: {e}")

    # Truncate collection (reset data)
    def truncate_collection(self):
        collection = db[self.collection_name]
        try:
            collection.delete_many({})  # Delete all documents in the collection
        except errors.PyMongoError as e:
            print(f"Error truncating collection: {e}")

# CRUD operations using the TableManager

@app.route("/db/add", methods=["POST"])
def add_data():
    data = request.json
    sheet_id = data['sheetId']
    sheet_name = data['sheetName']
    values = data['values']
    columns = data['columns']
    table_name = f"{sheet_name}_{sheet_id}".replace("-", "_")

    table_manager = table_managers.get(table_name)
    if not table_manager:
        table_manager = TableManager(sheet_id, sheet_name, columns)
        table_managers[table_name] = table_manager

    table_manager.insert_data(values)
    return jsonify({"message": f"Data added to {sheet_name} successfully"}), 200

@app.route("/db/fetch", methods=["GET"])
def fetch_data():
    sheet_id = request.args.get('sheetId')
    sheet_name = request.args.get('sheetName')
    table_name = f"{sheet_name}_{sheet_id}".replace("-", "_")

    table_manager = table_managers.get(table_name)
    if not table_manager:
        return jsonify({"error": "Table not found"}), 404

    data = table_manager.fetch_data()
    return jsonify(data), 200

@app.route("/api/init", methods=["POST"])
def init_db():
    data = request.json
    sheet_id = data['sheetId']
    sheet_name = data['sheetName']
    columns = data['data'][0]  # Assuming first row contains columns
    values = [tuple(row) for row in data['data'][1:]]  # Remaining rows are data

    table_name = f"{sheet_name}_{sheet_id}".replace("-", "_")
    table_manager = TableManager(sheet_id, sheet_name, columns)
    table_managers[table_name] = table_manager

    table_manager.truncate_collection()  # Clear previous data
    table_manager.insert_data(values)

    return jsonify({"message": f"Database initialized for {sheet_name}"}), 200

@app.route("/api/receiver", methods=["POST"])
def receive_data():
    data = request.json
    sheet_id = data['sheetId']
    sheet_name = data['sheetName']
    row = data["row"]
    column = data["column"]
    updated_data = data['data']
    table_name = f"{sheet_name}_{sheet_id}".replace("-", "_")

    table_manager = table_managers.get(table_name)
    if not table_manager:
        return jsonify({"error": "Table not found"}), 404

    # Upsert logic: update if exists, insert if not
    table_manager.upsert_data(row, column, updated_data)

    return jsonify({"message": "Data received and upserted successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
