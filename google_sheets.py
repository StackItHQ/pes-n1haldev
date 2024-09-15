from database import get_db_instance

def fetch_from_db(conn):
    cursor = conn.cursor()
    print(cursor.description)

def fetch_sheet(conn, sheet_service, id, sheet_name):
    sheet = sheet_service.spreadsheets()
    res = sheet.values().get(spreadsheetId=id, range=sheet_name).execute()

    vals = res.get("values", [])

    if not vals:
        print("Sheet is empty!")
        return
    
    cursor = conn.cursor()
    for row in vals:
        cursor.execute(
            """insert into company (company, contact, country) values (%s, %s, %s)""",
            (row[0], row[1], row[2])
        )

    conn.commit()

# def update_sheet(conn, sheet_service, id, sheet_name):

conn = get_db_instance()
fetch_from_db(conn)