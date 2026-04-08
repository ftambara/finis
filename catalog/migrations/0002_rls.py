# Generated manually

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE catalog_category ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_category
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE catalog_categoryparent ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_categoryparent
            USING (category_id IN (SELECT id FROM catalog_category WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (category_id IN (SELECT id FROM catalog_category WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_brand ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_brand
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE catalog_product ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_product
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);

            ALTER TABLE catalog_productbrand ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_productbrand
            USING (product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_productvariant ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_productvariant
            USING (product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_productvariantattribute ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_productvariantattribute
            USING (variant_id IN (SELECT id FROM catalog_productvariant WHERE product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)))
            WITH CHECK (variant_id IN (SELECT id FROM catalog_productvariant WHERE product_id IN (SELECT id FROM catalog_product WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)));

            ALTER TABLE catalog_order ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_order
            USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)
            WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer);
            
            ALTER TABLE catalog_order_brands ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_order_brands
            USING (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_ordersellerdetails ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_ordersellerdetails
            USING (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_orderitem ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_orderitem
            USING (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer))
            WITH CHECK (order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer));

            ALTER TABLE catalog_orderitemlink ENABLE ROW LEVEL SECURITY;
            CREATE POLICY tenant_isolation_policy ON catalog_orderitemlink
            USING (order_item_id IN (SELECT id FROM catalog_orderitem WHERE order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)))
            WITH CHECK (order_item_id IN (SELECT id FROM catalog_orderitem WHERE order_id IN (SELECT id FROM catalog_order WHERE organization_id = NULLIF(current_setting('app.tenant_id', true), '')::integer)));
            """,
            reverse_sql="""
            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_orderitemlink;
            ALTER TABLE catalog_orderitemlink DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_orderitem;
            ALTER TABLE catalog_orderitem DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_ordersellerdetails;
            ALTER TABLE catalog_ordersellerdetails DISABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_order_brands;
            ALTER TABLE catalog_order_brands DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_order;
            ALTER TABLE catalog_order DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_productvariantattribute;
            ALTER TABLE catalog_productvariantattribute DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_productvariant;
            ALTER TABLE catalog_productvariant DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_productbrand;
            ALTER TABLE catalog_productbrand DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_product;
            ALTER TABLE catalog_product DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_brand;
            ALTER TABLE catalog_brand DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_categoryparent;
            ALTER TABLE catalog_categoryparent DISABLE ROW LEVEL SECURITY;

            DROP POLICY IF EXISTS tenant_isolation_policy ON catalog_category;
            ALTER TABLE catalog_category DISABLE ROW LEVEL SECURITY;
            """,
        )
    ]
