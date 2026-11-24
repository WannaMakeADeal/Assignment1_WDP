from .db import get_db
from .services.parsers import STOCK_COLUMNS


def seed_templates():
    db=get_db()
    if db.execute('SELECT 1 FROM templates').fetchone():
        return
    tid=db.execute("INSERT INTO templates(name,kind) VALUES ('Ovol Stock Valuation - Sep 2026','stock')").lastrowid
    db.executemany('INSERT INTO template_columns(template_id,position,name,data_type,required) VALUES (?,?,?,?,?)',
                   [(tid,i,name,kind,int(required)) for i,(name,kind,required) in enumerate(STOCK_COLUMNS)])
    tid=db.execute("INSERT INTO templates(name,kind,delimiter) VALUES ('Simple delimited TXT','delimited','|')").lastrowid
    columns=[('Item Code','text',1),('Description','text',1),('Quantity','decimal',1),('Total Value','decimal',1)]
    db.executemany('INSERT INTO template_columns(template_id,position,name,data_type,required) VALUES (?,?,?,?,?)',
                   [(tid,i,*c) for i,c in enumerate(columns)])
    db.commit()
