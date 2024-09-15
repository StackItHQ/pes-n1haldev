import psycopg2

db_name = "superjoin"
db_user = "postgres"
db_password = "IamaCSstudent"
db_host = "localhost"

def get_db_instance():
    try:
        conn = psycopg2.connect(
            host = db_host,
            database = db_name,
            user = db_user,
            password = db_password,
            port = 5432 # This is generally default port ig?
        )
    
        return conn
    
    except Exception as e:
        print(e)