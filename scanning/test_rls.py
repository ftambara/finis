import pytest
from django.db import connection
from django.db.utils import ProgrammingError

from accounts.models import Organization, User
from scanning.models import Seller


@pytest.fixture
def org_a(db: None) -> Organization:
    from accounts.models import SpendingTier

    tier = SpendingTier.objects.using("admin").create(name="Tier A", token_limit=1000)
    return Organization.objects.using("admin").create(name="Org A", spending_tier=tier)


@pytest.fixture
def org_b(db: None) -> Organization:
    from accounts.models import SpendingTier

    tier = SpendingTier.objects.using("admin").create(name="Tier B", token_limit=1000)
    return Organization.objects.using("admin").create(name="Org B", spending_tier=tier)


@pytest.fixture
def user_a(org_a: Organization) -> User:
    return User.objects.db_manager("admin").create_user(email="user_a@orga.com", organization=org_a)


def set_tenant(org_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"SET app.tenant_id = '{org_id}'")


def clear_tenant() -> None:
    with connection.cursor() as cursor:
        cursor.execute("RESET app.tenant_id")


@pytest.mark.django_db(databases={"default", "admin"}, transaction=True)
class TestRLSBoundaries:
    def test_select_isolation(self, org_a: Organization, org_b: Organization, user_a: User) -> None:
        # Create data for both orgs as admin
        Seller.objects.using("admin").create(name="Seller A", organization=org_a)
        Seller.objects.using("admin").create(name="Seller B", organization=org_b)

        # Act as Org A
        set_tenant(org_a.id)
        try:
            sellers = list(Seller.objects.all())
            assert len(sellers) == 1
            assert sellers[0].name == "Seller A"
        finally:
            clear_tenant()

    def test_insert_isolation(self, org_a: Organization, org_b: Organization) -> None:
        # Act as Org A
        set_tenant(org_a.id)
        try:
            # Should succeed for own org
            Seller.objects.create(name="My Seller", organization=org_a)

            # Should fail for other org (WITH CHECK violation)
            with pytest.raises(
                ProgrammingError, match="new row violates row-level security policy"
            ):
                Seller.objects.create(name="Evil Seller", organization=org_b)
        finally:
            clear_tenant()

    def test_update_isolation(self, org_a: Organization, org_b: Organization) -> None:
        seller_b = Seller.objects.using("admin").create(name="Seller B", organization=org_b)

        # Act as Org A
        set_tenant(org_a.id)
        try:
            # Should not be able to update Org B's seller because it's not even visible (USING)
            # or it would violate WITH CHECK if we tried to move it to Org A.
            updated_count = Seller.objects.filter(id=seller_b.id).update(name="Hacked")
            assert updated_count == 0

            # Double check with a direct save if it was somehow visible
            with pytest.raises(
                ProgrammingError, match="new row violates row-level security policy"
            ):
                # This is tricky because Django might not even find it.
                # But if we try to force an update on a non-visible row,
                # it usually just does nothing.
                # The WITH CHECK handles the case where a visible row is
                # updated to an invisible state.
                # Let's try to update a visible row to an invalid organization.
                seller_a = Seller.objects.using("admin").create(name="Seller A", organization=org_a)
                Seller.objects.filter(id=seller_a.id).update(organization=org_b)
        finally:
            clear_tenant()

        # Verify Org B's seller was NOT updated
        seller_b_final = Seller.objects.using("admin").get(id=seller_b.id)
        assert seller_b_final.name == "Seller B"

    def test_delete_isolation(self, org_a: Organization, org_b: Organization) -> None:
        seller_b = Seller.objects.using("admin").create(name="Seller B", organization=org_b)

        # Act as Org A
        set_tenant(org_a.id)
        try:
            deleted_count, _ = Seller.objects.filter(id=seller_b.id).delete()
            assert deleted_count == 0
        finally:
            clear_tenant()

        # Verify Org B's seller still exists
        assert Seller.objects.using("admin").filter(id=seller_b.id).exists()
