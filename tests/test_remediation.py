from datetime import date

from uzquant.remediation import verified_shares_as_of
from uzquant.repository import Repository


def _seed(repo):
    repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('i','Issuer','TEST','2020-01-01')")
    repo.connection.execute("INSERT INTO securities VALUES('s','i','PREFERRED','EQUITY',NULL,'UZS','2020-01-01')")


def test_verified_shares_are_point_in_time_and_class_specific():
    with Repository() as repo:
        repo.initialize(); _seed(repo)
        repo.connection.execute("INSERT INTO share_capital_observations VALUES('p','i','s','2023-01-01','2023-02-01','1000',NULL,NULL,NULL,'PARTIAL','issuer total only',NULL,NULL,NULL,'test','2023-02-01')")
        repo.connection.execute("INSERT INTO share_capital_observations VALUES('v','i','s','2024-01-01','2024-02-01','1000','100',NULL,'UZS','VERIFIED',NULL,NULL,NULL,'preferred class', 'test','2024-02-01')")
        assert verified_shares_as_of(repo,'s',date(2023,12,31)) is None
        assert verified_shares_as_of(repo,'s',date(2024,2,1))["class_shares_outstanding"] == "100"


def test_unavailable_share_record_never_becomes_verified():
    with Repository() as repo:
        repo.initialize(); _seed(repo)
        repo.connection.execute("INSERT INTO share_capital_observations VALUES('u','i','s','2024-01-01','2024-01-02',NULL,NULL,NULL,NULL,'UNAVAILABLE','no public class count',NULL,'https://official.example',NULL,'test','2024-01-02')")
        assert verified_shares_as_of(repo,'s',date(2025,1,1)) is None

