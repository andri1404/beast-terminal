# FTS Rebuild Verification Recipe

## When to use
After rebuilding FTS indexes on state.db, verify writes actually work before declaring victory.

## Verification script

```python
import sqlite3, time

db_path = "/home/ubuntu/.hermes/state.db"
conn = sqlite3.connect(db_path)

try:
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO messages(session_id, role, content, timestamp) VALUES(?, ?, ?, ?)",
        ('fts_verify_test', 'user', 'fts rebuild verification', time.time())
    )
    conn.execute("COMMIT")
    print("✓ Write SUCCESS — FTS corruption fixed")
    # Clean up
    conn.execute("DELETE FROM messages WHERE session_id='fts_verify_test'")
    conn.execute("COMMIT")
    print("✓ Cleanup done")
except Exception as e:
    conn.execute("ROLLBACK")
    print(f"✗ Write FAILED: {e}")

conn.close()
```

## Post-repair checklist

1. FTS rebuild (`INSERT INTO fts_table(fts_table) VALUES('rebuild')`)
2. WAL checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`)
3. Write test (script above)
4. Verify `state.db-wal` shrunk (should be < 1MB after checkpoint)
5. Clean up disk: `rm -f ~/.hermes/skills-hub.db` (if using MCP API instead)

## Reproduced symptom (2026-08-14)

```
grep "database disk image is malformed" ~/.hermes/logs/agent.log
→ 2026-08-14 16:01:34,957 run_agent: Session DB append_message failed: database disk image is malformed
→ 2026-08-14 16:01:39,915 run_agent: Session DB append_message failed: database disk image is malformed
... (repeated)

PRAGMA integrity_check → ok  (FALSE NEGATIVE — FTS corruption invisible to integrity_check)
hermes sessions repair → "no repair needed"  (FALSE NEGATIVE)
hermes doctor --fix → no issues detected  (FALSE NEGATIVE)
```

Root cause: FTS5 content tables corrupt, main DB schema intact. Only `INSERT INTO messages_fts(messages_fts) VALUES('rebuild')` fixed it.