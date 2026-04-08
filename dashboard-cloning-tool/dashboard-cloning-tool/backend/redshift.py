import redshift_connector
from backend.config import config

def get_connection():
    return redshift_connector.connect(
        host=config.REDSHIFT_HOST,
        port=config.REDSHIFT_PORT,
        database=config.REDSHIFT_DB,
        user=config.REDSHIFT_USER,
        password=config.REDSHIFT_PASSWORD
    )

def test_connection() -> dict:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"success": True, "message": "Redshift connection successful"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_table_columns(table_name: str, schema: str = None) -> list:
    schema = schema or config.REDSHIFT_SCHEMA
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        rows = cursor.fetchall()
        conn.close()
        return [{"name": row[0], "type": row[1], "position": row[2]} for row in rows]
    except Exception as e:
        raise Exception(f"Failed to get columns for {schema}.{table_name}: {str(e)}")

def table_exists(table_name: str, schema: str = None) -> bool:
    schema = schema or config.REDSHIFT_SCHEMA
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        """, (schema, table_name))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False

def create_client_view(client_name: str, client_table: str, standard_columns: list, schema: str = None):
    """
    Create a SQL view for a client that maps their columns to standard dummy columns.
    standard_columns: list of dicts with 'dummy' and 'real' keys
    """
    schema = schema or config.REDSHIFT_SCHEMA
    view_name = f"{client_name}_standard_view"

    select_parts = []
    for col in standard_columns:
        real = col.get("real")
        dummy = col.get("dummy")
        if real:
            select_parts.append(f'"{real}" AS "{dummy}"')
        else:
            select_parts.append(f'NULL AS "{dummy}"')

    select_sql = ",\n  ".join(select_parts)
    view_sql = f"""
CREATE OR REPLACE VIEW {schema}.{view_name} AS
SELECT
  {select_sql}
FROM {schema}.{client_table}
    """.strip()

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(view_sql)
        conn.commit()
        conn.close()
        return {"success": True, "view_name": f"{schema}.{view_name}", "sql": view_sql}
    except Exception as e:
        return {"success": False, "error": str(e), "sql": view_sql}
