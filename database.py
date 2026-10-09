import os

import psycopg2
from dotenv import load_dotenv
from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

load_dotenv()


def run_query(sql, values=(), fetch="all"):
    # Open a short-lived connection for each request.
    connection = None
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "task_manager"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=5,
        )
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Values are passed separately to prevent SQL injection.
                cursor.execute(sql, values)
                if fetch == "one":
                    row = cursor.fetchone()
                    if row is None:
                        return None
                    return dict(row)
                rows = cursor.fetchall()
                tasks = []
                for row in rows:
                    tasks.append(dict(row))
                return tasks
    except psycopg2.OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check PostgreSQL and your local .env settings.",
        )
    finally:
        if connection is not None:
            connection.close()
