from database.connection import engine

try:
    with engine.connect():
        print("Подключение к PostgreSQL успешно")
except Exception as error:
    print("Ошибка подключения:", error)
