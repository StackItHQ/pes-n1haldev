import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import MutualTLSChannelError
import psycopg2
from psycopg2.extras import execute_values

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SAMPLE_SPREADSHEET_ID = "1SvGvOXTO-SMloCklizlcN252uaaOw-9XxEL-x-fDXGw"
SAMPLE_RANGE_NAME = "Sheet1"
db_name = "superjoin"
db_user = "postgres"
db_password = "IamaCSstudent"
db_host = "localhost"

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

def spawn_table(conn, name):
    # conn = get_db_instance()

    query = f"""create table if not exists {name} (
        id serial primary key,
        company text,
        contact text,
        country text
    )"""

    cursor = conn.cursor()
    cursor.execute(query)

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

def fetch_db(conn):
    cursor = conn.cursor()
    cursor.execute("""select * from company""")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    return rows

def fetch_sheet(sheet_service, id, sheet_name):
    sheet = sheet_service.spreadsheets()
    res = sheet.values().get(spreadsheetId=id, range=sheet_name).execute()

    vals = res.get("values", [])

    if not vals:
        print("Sheet is empty!")
        return
    
    return vals

def update_db(conn, vals):
    cursor = conn.cursor()
    vals = vals[1:]
    # cursor.execute("""drop table company""")
    cursor.execute("""truncate table company""")
    cursor.execute("""ALTER SEQUENCE company_id_seq RESTART WITH 1""")
    # spawn_table(conn, 'company')
    # print("test")
    execute_values(cursor,
        """insert into company (company, contact, country) values %s""",
        [tuple(row) for row in vals]
    )
    conn.commit()

def update_sheet(sheet_service, id, sheet_name, data):
    body = {"values": data}
    sheet_service.spreadsheets().values().update(
        spreadsheetId=id, range=sheet_name, valueInputOption="RAW", body=body
    ).execute()

conn = get_db_instance()
sheet_service = sheet_service()
spawn_table(conn, 'company')
data = fetch_sheet(sheet_service, SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
print(len(data))
update_db(conn, data)
print(fetch_db(conn))
