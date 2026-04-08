# Generated manually

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("scanning", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE scanning_seller ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_seller
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE scanning_pointofsale ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_pointofsale
            USING (seller_id IN (SELECT id FROM scanning_seller WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (seller_id IN (SELECT id FROM scanning_seller WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE scanning_receipt ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_receipt
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE scanning_receiptimage ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_receiptimage
            USING (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE scanning_receiptresult ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_receiptresult
            USING (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE scanning_receipterror ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_receipterror
            USING (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE scanning_processedreceipt ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_processedreceipt
            USING (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE scanning_paymentmethod ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_paymentmethod
            USING (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)))
            WITH CHECK (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)));

            ALTER TABLE scanning_sellerorderid ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_sellerorderid
            USING (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)))
            WITH CHECK (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)));

            ALTER TABLE scanning_receiptlineitem ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_receiptlineitem
            USING (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)))
            WITH CHECK (processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)));

            ALTER TABLE scanning_lineitemdiscount ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON scanning_lineitemdiscount
            USING (line_item_id IN (SELECT id FROM scanning_receiptlineitem WHERE processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))))
            WITH CHECK (line_item_id IN (SELECT id FROM scanning_receiptlineitem WHERE processed_receipt_id IN (SELECT receipt_id FROM scanning_processedreceipt WHERE receipt_id IN (SELECT id FROM scanning_receipt WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))));
            """,
            reverse_sql="""
            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_lineitemdiscount;
            ALTER TABLE scanning_lineitemdiscount DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_receiptlineitem;
            ALTER TABLE scanning_receiptlineitem DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_sellerorderid;
            ALTER TABLE scanning_sellerorderid DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_paymentmethod;
            ALTER TABLE scanning_paymentmethod DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_processedreceipt;
            ALTER TABLE scanning_processedreceipt DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_receipterror;
            ALTER TABLE scanning_receipterror DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_receiptresult;
            ALTER TABLE scanning_receiptresult DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_receiptimage;
            ALTER TABLE scanning_receiptimage DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_receipt;
            ALTER TABLE scanning_receipt DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_pointofsale;
            ALTER TABLE scanning_pointofsale DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON scanning_seller;
            ALTER TABLE scanning_seller DISABLE ROW LEVEL SECURITY;
            """,
        )
    ]
