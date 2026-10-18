"""Initialize a fresh hosted database once, without destructive legacy migrations."""
from pathlib import Path

import psycopg2

from config.database import get_db_config


def bootstrap():
    with psycopg2.connect(**get_db_config()) as connection:
        with connection.cursor() as cursor:
            # Serialize simultaneous starts and make initialization atomic.
            cursor.execute("SELECT pg_advisory_xact_lock(854070202)")
            cursor.execute("SELECT to_regclass('public.deployment_schema_versions')")
            if cursor.fetchone()[0] is None:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                if cursor.fetchall():
                    raise RuntimeError(
                        "Deployment bootstrap needs an empty database. Existing tables were "
                        "left untouched; migrate or back up the existing database separately."
                    )
                cursor.execute("CREATE TABLE deployment_schema_versions (version INTEGER PRIMARY KEY)")
            cursor.execute("SELECT 1 FROM deployment_schema_versions WHERE version = 1")
            if cursor.fetchone():
                print("Deployment schema is current; data preserved")
                return
            cursor.execute(Path(__file__).with_name("schema.sql").read_text())
            cursor.execute("INSERT INTO deployment_schema_versions (version) VALUES (1)")
    print("Deployment schema initialized")


if __name__ == "__main__":
    bootstrap()
