# Generated manually

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$ 
            BEGIN
              IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'finis_admin') THEN
                CREATE ROLE finis_admin BYPASSRLS;
              END IF;
              IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'finis_customer') THEN
                CREATE ROLE finis_customer LOGIN PASSWORD 'secret';
              END IF;
            END
            $$;
            
            GRANT ALL PRIVILEGES ON DATABASE finis TO finis_admin;
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finis_customer;
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finis_customer;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO finis_customer;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO finis_customer;
            """,
            reverse_sql="""
            DROP ROLE IF EXISTS finis_customer;
            DROP ROLE IF EXISTS finis_admin;
            """,
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE accounts_organization ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON accounts_organization
            USING (id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE accounts_user ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON accounts_user
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE accounts_tokenusage ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON accounts_tokenusage
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);
            """,
            reverse_sql="""
            DROP POLICY IF EXISTS tenant_isolation_policy ON accounts_tokenusage;
            ALTER TABLE accounts_tokenusage DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON accounts_user;
            ALTER TABLE accounts_user DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON accounts_organization;
            ALTER TABLE accounts_organization DISABLE ROW LEVEL SECURITY;
            """,
        ),
    ]
