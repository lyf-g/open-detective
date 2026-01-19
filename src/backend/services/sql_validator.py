import sqlparse
import structlog

logger = structlog.get_logger()


def validate_sql(sql: str) -> bool:
    """Validates that the SQL query is a read-only SELECT statement.
    """
    # 1. Explicit Keyword Blacklist (Defense in Depth)
    forbidden = {
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
    }
    upper_sql = f" {sql.upper()} "
    for word in forbidden:
        if f" {word} " in upper_sql:
            logger.warning("forbidden_keyword_detected", keyword=word, sql=sql)
            return False

    # 2. Parser Validation
    parsed = sqlparse.parse(sql)
    for statement in parsed:
        if statement.get_type().upper() != "SELECT":
            logger.warning(
                "invalid_statement_type",
                statement_type=statement.get_type(),
                sql=sql,
            )
            return False
    return True
