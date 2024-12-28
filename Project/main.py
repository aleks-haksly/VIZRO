from include.supabase import select


result = select("""
set statement_timeout = '30min';

CREATE INDEX ON "vizro"."yandex_data" USING hash ("platform");
""")
print(result)