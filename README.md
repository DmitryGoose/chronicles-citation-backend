# Летописные источники — лабораторная работа 3

В проекте реализован REST-веб-сервис для будущего SPA. Все методы API начинаются с `/api`, работают с PostgreSQL через SQLAlchemy ORM и не возвращают записи со статусом `удален`. До реализации авторизации текущим пользователем считается пользователь с `id = 1`; его возвращает singleton-функция `get_current_user_id()`.

## Запуск

1. Запустить PostgreSQL, Adminer и MinIO: `docker compose up -d`.
2. Установить зависимости: `pip install -r requirements.txt`.
3. Запустить сервер: `uvicorn application:app --reload`.
4. Документация OpenAPI доступна по адресу `http://127.0.0.1:8000/docs`.

## HTTP-методы

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api/chronicles?start_year=1016` | Список опубликованных источников с необязательным фильтром; `is_owner` равен 0 или 1 |
| POST | `/api/chronicles` | Создание черновика; `name`, `image`, `video` передаются как `multipart/form-data`, файлы сохраняются в MinIO |
| GET | `/api/chronicles/draft` | Единственный черновик текущего пользователя без передачи id |
| PUT | `/api/chronicles/{id}/publish` | Публикация собственного черновика; переход обратно в черновик отсутствует |
| GET | `/api/chronicles/feed` | Первая опубликованная запись ленты без id; содержит `is_liked` |
| GET | `/api/chronicles/feed?chronicle_id={id}&next=true` | Следующая опубликованная запись с циклическим переходом |
| POST | `/api/chronicles/{id}/like` | Установка (`value=1`) или отмена (`value=0`) лайка текущего пользователя |
| DELETE | `/api/chronicles/{id}` | Логическое удаление только собственного источника |
| POST | `/api/users/register` | Регистрация пользователя |
| POST | `/api/users/authenticate` | Заглушка аутентификации для ЛР4 |
| POST | `/api/users/logout` | Заглушка деавторизации для ЛР4 |

Системные поля `id`, `status`, `creator_id`, `published_at` и `created_at` не принимаются от клиента. Они вычисляются на сервере. Имя загружаемого объекта генерируется латиницей и сохраняется в `image_url` или `video_url`; клиент получает полный HTTP URL MinIO.

## Таблицы базы данных

### `users`

| Поле | Тип | Ограничение |
|---|---|---|
| `id` | integer | PK, автоинкремент |
| `username` | varchar(100) | NOT NULL, UNIQUE |
| `password_hash` | varchar(255) | NOT NULL, хеш пароля пользователя |

### `chronicles`

| Поле | Тип | Назначение |
|---|---|---|
| `id` | integer | PK |
| `name` | varchar(255) | название источника |
| `short_description` | text | краткое описание |
| `status` | varchar(20) | `черновик`, `опубликован` или `удален` |
| `image_url` | varchar(500) | имя объекта изображения в MinIO либо URL существующей записи |
| `video_url` | varchar(500) | имя объекта видео в MinIO либо URL существующей записи |
| `authorship_year` | integer | год создания списка |
| `start_year` | integer | первый описанный год |
| `created_at` | timestamp | дата создания, вычисляется сервером |
| `creator_id` | integer | FK → `users.id` |
| `published_at` | timestamp | дата публикации, вычисляется сервером |

Частичный уникальный индекс `one_draft_per_user` не позволяет одному пользователю иметь более одного черновика.

### `likes`

| Поле | Тип | Ограничение |
|---|---|---|
| `id` | integer | PK |
| `user_id` | integer | FK → `users.id` |
| `chronicle_id` | integer | FK → `chronicles.id` |

Ограничение `one_like_per_user` запрещает повторный лайк одной записи тем же пользователем.

## Файлы документации

- `postman/chronicles-lab3.postman_collection.json` — коллекция запросов для порядка показа.
- `docs/class-diagram.mmd` — диаграмма классов, доменов API, моделей, таблиц и страниц фронтенда.
