import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


def main():
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    table = os.getenv("SUPABASE_TABLE", "radar")

    if not url or not key:
        print("Defina SUPABASE_URL e SUPABASE_SERVICE_KEY no arquivo .env antes de executar este script.")
        return

    supabase = create_client(url, key)
    response = supabase.table(table).select("*").limit(5).execute()
    print(response.data)


if __name__ == "__main__":
    main()
