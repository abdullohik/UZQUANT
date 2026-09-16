from __future__ import annotations

import json
import uuid

from .repository import Repository,utc_now


def migrate_legacy_lineage(database):
    with Repository(database) as repo:
        repo.initialize(); c=repo.connection; linked=signals=0
        for table,pk in (("fundamental_metrics","metric_id"),("valuation_records","valuation_id")):
            for row in c.execute(f"SELECT {pk},source_observation_ids_json FROM {table}").fetchall():
                for old_id in json.loads(row[1] or "[]"):
                    version=c.execute("SELECT version_id FROM financial_observation_versions WHERE observation_id=? ORDER BY created_at LIMIT 1",(old_id,)).fetchone()
                    if version:
                        c.execute("INSERT OR IGNORE INTO analytical_observation_lineage VALUES(?,?,?,?,?)",(str(uuid.uuid4()),table,row[0],version[0],utc_now())); linked+=c.execute("SELECT changes()").fetchone()[0]
        for signal in c.execute("SELECT signal_id,security_id,generated_at FROM research_signals").fetchall():
            issuer=c.execute("SELECT issuer_id FROM securities WHERE security_id=?",(signal[1],)).fetchone()
            if not issuer: continue
            for version in c.execute("SELECT version_id FROM financial_observation_versions WHERE issuer_id=? AND publication_date<=? AND created_at<=?",(issuer[0],signal[2][:10],signal[2])).fetchall():
                c.execute("INSERT OR IGNORE INTO signal_observation_lineage VALUES(?,?,?,?)",(signal[0],version[0],"LEGACY_INFERRED",utc_now())); signals+=c.execute("SELECT changes()").fetchone()[0]
        c.commit()
        return {"financial_versions":c.execute("SELECT count(*) FROM financial_observation_versions").fetchone()[0],"analytical_links":linked,"legacy_signal_links":signals,"legacy_snapshots":c.execute("SELECT count(*) FROM prospective_snapshot_evidence WHERE standard='LEGACY_SNAPSHOT_LIMITED'").fetchone()[0]}
