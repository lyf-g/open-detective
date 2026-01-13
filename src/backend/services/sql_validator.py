import sqlparse

def validate_sql(sql: str) -> bool:
    """
    Validates that the SQL query is a read-only SELECT statement.
    """
    # 1. Explicit Keyword Blacklist (Defense in Depth)
    forbidden = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"}
    upper_sql = sql.upper()
    for word in forbidden:
        if f" {word} " in f" {upper_sql} ": # Check distinct words
            return False

    # 2. Parser Validation
    parsed = sqlparse.parse(sql)
    for statement in parsed:
        if statement.get_type().upper() != 'SELECT':
            return False
    return True
