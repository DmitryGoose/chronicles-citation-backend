from database.connection import SessionLocal
from models.chronicle import Chronicle

db = SessionLocal()
try:
    chronicles = db.query(Chronicle).order_by(Chronicle.id).all()
    print(f"Найдено летописей: {len(chronicles)}")
    for chronicle in chronicles:
        print(chronicle.id, chronicle.name, chronicle.status)
finally:
    db.close()
