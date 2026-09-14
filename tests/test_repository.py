import sqlite3
import unittest

from uzquant import Repository


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repository()
        self.repo.initialize()
        self.source_id = self.repo.add_source(
            name="Synthetic Test Source",
            domain="example.invalid",
            authority_level="PRIMARY",
            access_status="VERIFIED_MANUAL",
        )
        self.snapshot_id = self.repo.archive_snapshot(
            source_id=self.source_id,
            source_url="https://example.invalid/synthetic-fixture",
            raw_content=b"synthetic fixture only",
            media_type="text/plain",
            retrieved_at="2025-01-02T00:00:00+00:00",
            publication_at="2025-01-01T00:00:00+00:00",
        )

    def tearDown(self) -> None:
        self.repo.close()

    def test_issuer_and_security_are_separate(self) -> None:
        issuer_id = self.repo.add_issuer("Synthetic Issuer")
        common_id = self.repo.add_security(
            issuer_id=issuer_id, security_class="COMMON", currency="UZS"
        )
        preferred_id = self.repo.add_security(
            issuer_id=issuer_id, security_class="PREFERRED", currency="UZS"
        )
        self.assertNotEqual(common_id, preferred_id)

    def test_snapshot_cannot_be_changed_or_deleted(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.connection.execute(
                "UPDATE source_snapshots SET raw_content = ? WHERE snapshot_id = ?",
                (b"changed", self.snapshot_id),
            )
        self.repo.connection.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.connection.execute(
                "DELETE FROM source_snapshots WHERE snapshot_id = ?",
                (self.snapshot_id,),
            )
        self.repo.connection.rollback()

    def test_point_in_time_query_excludes_future_knowledge(self) -> None:
        issuer_id = self.repo.add_issuer("Synthetic Issuer")
        self.repo.add_reported_fact(
            issuer_id=issuer_id,
            snapshot_id=self.snapshot_id,
            fact_name="revenue",
            value_numeric="100.00",
            unit="million",
            currency="UZS",
            known_at="2025-01-02T00:00:00+00:00",
            period_start="2024-01-01",
            period_end="2024-12-31",
            value_kind="REPORTED",
            confidence="HIGH",
        )
        self.assertEqual(
            self.repo.facts_known_at(as_of="2025-01-01T23:59:59+00:00"), []
        )
        self.assertEqual(
            len(self.repo.facts_known_at(as_of="2025-01-02T00:00:00+00:00")), 1
        )

    def test_missing_value_cannot_be_stored_as_a_fact(self) -> None:
        issuer_id = self.repo.add_issuer("Synthetic Issuer")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.add_reported_fact(
                issuer_id=issuer_id,
                snapshot_id=self.snapshot_id,
                fact_name="unknown_value",
                known_at="2025-01-02T00:00:00+00:00",
                value_kind="REPORTED",
                confidence="UNKNOWN",
            )

    def test_fact_requires_provenance(self) -> None:
        issuer_id = self.repo.add_issuer("Synthetic Issuer")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.add_reported_fact(
                issuer_id=issuer_id,
                snapshot_id=999,
                fact_name="revenue",
                value_numeric="100",
                known_at="2025-01-02T00:00:00+00:00",
                value_kind="REPORTED",
                confidence="HIGH",
            )


if __name__ == "__main__":
    unittest.main()
