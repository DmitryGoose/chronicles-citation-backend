# Проектирование систем и продуктовая веб-разработка 2026 (Разработка Интернет Приложений)

### Тема: Цитирование летописей. Услуги — летописи и другие первичные источники с отрывками текста. Заявка — описание исторического события с комментариями на выбранные источники; отметка источников, в которых событие описано.

## API

Запуск: `docker compose up -d`, `pip install -r requirements.txt`, `uvicorn application:app --reload --port 8000`. Все методы API находятся под `http://127.0.0.1:8000/api`.

- При ошибке FastAPI возвращает JSON с полем `detail` и соответствующий HTTP-код (`404`, `409`, `422` и т. д.).
- Аутентификация создаёт серверную сессию в Redis и устанавливает HttpOnly cookie `chronicles_session`. Методы создателя получают пользователя только из сессии.
- Удаление летописных источников логическое: запись остаётся в БД и получает статус `удален`.
- В списке и ленте клиенту передаются только записи со статусом `опубликован`.
- Изображения и короткие видео загружаются в MinIO. Допустимые изображения: JPEG, PNG, WebP; видео: MP4, WebM.
- MinIO доступен на `http://localhost:9000`, консоль MinIO — `http://localhost:9001`, Adminer — `http://localhost:8081`.
- Swagger/OpenAPI доступен по адресу `http://127.0.0.1:8000/docs`. Публичные GET-методы работают без cookie; методы создателя отмечены схемой `CookieSession` и возвращают 401 без действующей сессии.

Тело ответа «летописный источник в ленте»:

```json
{
  "id": 11,
  "name": "Летопись Postman ЛР3",
  "short_description": "Источник, опубликованный через REST API",
  "authorship_year": 1500,
  "start_year": 1499,
  "image_url": "http://localhost:9000/chronicles/example-image.jpg",
  "video_url": "http://localhost:9000/chronicles/example-video.mp4",
  "is_owner": 1,
  "likes_count": 1,
  "is_liked": 1
}
```

### Летописные источники

| Метод | URL | Тело/параметры | Ответ |
| --- | --- | --- | --- |
| GET | `/chronicles` | `?start_year=N`: необязательный фильтр по первому описанному году, допустимо от 1 до 2100 | 200, массив опубликованных источников; у каждого дополнительно `is_owner`: 1, если источник принадлежит текущему пользователю, иначе 0 |
| GET | `/chronicles/feed` | Без параметров — первая опубликованная запись; `?chronicle_id=N` — конкретная запись; `?chronicle_id=N&next=true` — следующая после неё с циклическим переходом | 200, источник с `likes_count` и `is_liked`; 404, если опубликованных источников нет или переданный id не найден |
| GET | `/chronicles/draft` | — | 200, единственный черновик текущего пользователя; 404, если черновика нет |
| POST | `/chronicles` | form-data: `name`, `image` (jpeg/png/webp), `video` (mp4/webm) | 201, созданный черновик; 409, если у пользователя уже есть черновик; 422 при некорректных данных или типе медиа |
| PUT | `/chronicles/:id/publish` | JSON, все обязательны: `short_description`, `authorship_year`, `start_year` | 200, опубликованный источник; 404, если это не черновик текущего пользователя; 422 при ошибке валидации |
| DELETE | `/chronicles/:id` | —; логическое удаление собственного источника | 204 без тела; 404, если источник пользователя не найден |
| POST | `/chronicles/:id/like` | JSON `{"value": 1}` ставит лайк, `{"value": 0}` снимает | 200, источник с актуальными `likes_count` и `is_liked`; 404, если источник не опубликован или не найден |

### Пользователи

| Метод | URL | Тело/параметры | Ответ |
| --- | --- | --- | --- |
| POST | `/users/register` | JSON `{"username": "postman_user", "password": "password123"}` | 201, `{id, username}`; 409, если имя пользователя занято; 422 при ошибке валидации |
| POST | `/users/authenticate` | JSON `{"username": "postman_user", "password": "password123"}` | 200, данные пользователя и HttpOnly cookie `chronicles_session`; 401 при неверных данных |
| POST | `/users/logout` | Cookie `chronicles_session` | 200, удаление сессии из Redis и очистка cookie; 401 без сессии |

## Таблицы БД

### chronicles — летописные источники

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | первичный ключ |
| `name` | varchar(255) | название летописного источника, обязательное |
| `short_description` | text | краткое описание, заполняется при публикации |
| `status` | varchar(20) | `черновик`, `опубликован` или `удален` |
| `image_url` | varchar(500) | имя объекта изображения в MinIO либо готовый URL |
| `video_url` | varchar(500) | имя объекта видео в MinIO либо готовый URL |
| `authorship_year` | integer | год создания летописного списка |
| `start_year` | integer | первый описанный год |
| `created_at` | timestamp | дата и время создания, вычисляется сервером |
| `creator_id` | integer | владелец источника, внешний ключ на `users.id` |
| `published_at` | timestamp | дата и время публикации, вычисляется сервером |

Для `chronicles` действует проверка допустимых статусов и частичный уникальный индекс `one_draft_per_user`, который не позволяет одному пользователю иметь более одного черновика.

### users — пользователи

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | первичный ключ |
| `username` | varchar(100) | уникальное имя пользователя, обязательное |
| `password_hash` | varchar(255) | SHA-256 хеш пароля, обязательное поле |

### likes — лайки

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | integer | первичный ключ |
| `user_id` | integer | пользователь, поставивший лайк; внешний ключ на `users.id` |
| `chronicle_id` | integer | летописный источник; внешний ключ на `chronicles.id` |

Ограничение `one_like_per_user` запрещает одному пользователю поставить повторный лайк одной и той же записи.

## Хранилища и сервисы

| Сервис | Адрес | Назначение |
| --- | --- | --- |
| FastAPI | `http://127.0.0.1:8000` | REST API, Swagger и сервер приложения |
| PostgreSQL | `127.0.0.1:55433` | основная база данных |
| Redis | `127.0.0.1:6379` | серверное хранение пользовательских сессий |
| Adminer | `http://localhost:8081` | просмотр и проверка PostgreSQL |
| MinIO API | `http://localhost:9000` | хранение изображений и видео |
| MinIO Console | `http://localhost:9001` | управление объектным хранилищем |

Бакет MinIO: `chronicles`. При запуске через Docker Compose он создаётся автоматически и получает публичный доступ на скачивание объектов.

## Дополнительные материалы ЛР3

- `postman/chronicles-lab3.postman_collection.json` — коллекция запросов Postman для проверки REST API.
- `docs/class-diagram.mmd` — диаграмма классов и зависимостей.
- `database/init.sql` — начальная схема и данные PostgreSQL.
- `api/schemas.py` — Pydantic-схемы входных DTO и ответов API.
- `api/chronicles.py` — REST-методы домена летописных источников.
- `api/users.py` — регистрация пользователя и заглушки авторизации/выхода.
- `api/storage.py` — загрузка и выдача медиафайлов через MinIO.

## Авторизация и сессии ЛР4

Регистрация сохраняет пароль в формате PBKDF2-SHA256 с индивидуальной солью. Метод `POST /api/users/authenticate` проверяет пароль, создаёт случайный идентификатор сессии, сохраняет в Redis JSON с `user_id` и `username` на 3600 секунд и устанавливает HttpOnly cookie `chronicles_session`. Клиент не передаёт `creator_id`: при создании, получении черновика, публикации, лайке и удалении пользователь определяется зависимостью `get_current_user_id()` по сессии.

Публичные методы:

- `GET /api/chronicles` — список и фильтрация опубликованных источников;
- `GET /api/chronicles/feed` — получение записи ленты.

Защищённые методы возвращают `401 Unauthorized` без действующей cookie:

- `POST /api/chronicles`;
- `GET /api/chronicles/draft`;
- `PUT /api/chronicles/{chronicle_id}/publish`;
- `POST /api/chronicles/{chronicle_id}/like`;
- `DELETE /api/chronicles/{chronicle_id}`;
- `POST /api/users/logout`.

Проверка Redis из PowerShell после аутентификации:

```powershell
docker exec chronicles-redis redis-cli --scan --pattern "session:*"
docker exec chronicles-redis redis-cli GET "session:<идентификатор_из_предыдущей_команды>"
docker exec chronicles-redis redis-cli TTL "session:<идентификатор_из_предыдущей_команды>"
```

Переменные окружения:

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | подключение к Redis |
| `SESSION_TTL_SECONDS` | `3600` | время жизни сессии |
| `SESSION_COOKIE_SECURE` | `false` | передача cookie только по HTTPS в рабочем окружении |
