from database import get_db_instance

def spawn_table():
    conn = get_db_instance()

    query = """create table if not exists company (
        id serial primary key,
        company text,
        contact numeric(10),
        country text
    )"""

    cursor = conn.cursor()
    cursor.execute(query)

    conn.commit()