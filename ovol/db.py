"""Connection lifetime and repositories keep SQL out of page templates."""
import json
import sqlite3
from pathlib import Path
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def init_db():
    db = get_db()
    db.executescript(Path(__file__).with_name('schema.sql').read_text())
    db.commit()


def audit(entity, entity_id, action, details, report_id=None):
    get_db().execute(
        'INSERT INTO audit_events(report_id,entity,entity_id,action,details) VALUES (?,?,?,?,?)',
        (report_id,entity,entity_id,action,json.dumps(details,ensure_ascii=False)))


class ReportRepository:
    def __init__(self, db):
        self._db = db

    def get(self, report_id):
        return self._db.execute('SELECT * FROM reports WHERE id=?',(report_id,)).fetchone()

    def columns(self, report_id):
        return self._db.execute('SELECT * FROM report_columns WHERE report_id=? ORDER BY position',(report_id,)).fetchall()

    def records(self, report_id):
        rows = self._db.execute('SELECT * FROM records WHERE report_id=? ORDER BY line_no,id',(report_id,)).fetchall()
        values = {}
        for c in self._db.execute('SELECT c.* FROM cells c JOIN records r ON r.id=c.record_id WHERE r.report_id=?',(report_id,)):
            values.setdefault(c['record_id'],{})[c['column_id']] = c['value']
        return [dict(r, values=values.get(r['id'],{})) for r in rows]
