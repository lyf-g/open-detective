import sqlparse

def validate_sql(sql: str) -> bool:
    """
    Validates that the SQL query is a read-only SELECT statement.
    """
    parsed = sqlparse.parse(sql)
    for statement in parsed:
        if statement.get_type().upper() != 'SELECT':
            return False
    return True
