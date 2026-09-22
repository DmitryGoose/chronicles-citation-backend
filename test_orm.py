from database.connection import SessionLocal
from models.chronicle import Chronicle


db = SessionLocal()

try:
    chronicles = db.query(Chronicle).all()

    print(f"Найдено летописей: {len(chronicles)}")

    for chronicle in chronicles:
        print(
            f"ID: {chronicle.id} | "
            f"Название: {chronicle.название} | "
            f"Статус: {chronicle.статус}"
        )

finally:
    db.close()
