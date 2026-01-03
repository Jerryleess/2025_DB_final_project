from utils.db_config import get_db_connection

def _fetch_as_dicts(cursor):
    cols = [c[0] for c in cursor.description] if cursor.description else []
    rows = cursor.fetchall() if cursor.description else []
    return [dict(zip(cols, row)) for row in rows]

def query_all(sql, params=None, *, conn=None):
    owns_conn = conn is None
    if owns_conn:
        conn = get_db_connection()

    cursor = conn.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        return _fetch_as_dicts(cursor)
    finally:
        cursor.close()
        if owns_conn:
            conn.close()

def query_one(sql, params=None, *, conn=None):
    owns_conn = conn is None
    if owns_conn:
        conn = get_db_connection()

    cursor = conn.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)

        row = cursor.fetchone()
        if not row or not cursor.description:
            return None

        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))
    finally:
        cursor.close()
        if owns_conn:
            conn.close()

def execute(sql, params=None, *, conn=None, commit=True):
    """
    用來做 INSERT/UPDATE/DELETE。
    - conn=None: 自己開連線，預設 commit=True
    - conn=外部transaction: 建議 commit=False，讓外層決定 commit/rollback
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_db_connection()

    cursor = conn.cursor()
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)

        if owns_conn and commit:
            conn.commit()

        return cursor.rowcount
    except Exception:
        if owns_conn:
            conn.rollback()
        raise
    finally:
        cursor.close()
        if owns_conn:
            conn.close()
