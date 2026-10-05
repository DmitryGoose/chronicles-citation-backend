DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS chronicles;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE chronicles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_description TEXT,
    status VARCHAR(20) NOT NULL CHECK (status IN ('черновик', 'опубликован', 'удален')),
    image_url VARCHAR(500),
    video_url VARCHAR(500),
    authorship_year INTEGER,
    start_year INTEGER,
    created_at TIMESTAMP NOT NULL,
    creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    published_at TIMESTAMP
);

CREATE UNIQUE INDEX one_draft_per_user
ON chronicles (creator_id)
WHERE status = 'черновик';

CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    chronicle_id INTEGER NOT NULL REFERENCES chronicles(id) ON DELETE RESTRICT,
    CONSTRAINT one_like_per_user UNIQUE (user_id, chronicle_id)
);

INSERT INTO users (username) VALUES
    ('dmitry'), ('anna'), ('maria'), ('ivan'), ('sergey'), ('olga');

INSERT INTO chronicles
    (name, short_description, status, image_url, video_url, authorship_year, start_year, created_at, creator_id, published_at)
VALUES
    ('Повесть временных лет', 'Древнерусский летописный свод о ранней истории Руси и событиях IX–XII веков.', 'опубликован', 'http://localhost:9000/chronicles/povest-vremennyh-let.jpg', 'http://localhost:9000/chronicles/povest-vremennyh-let.mp4', 1116, 852, NOW(), 1, NOW()),
    ('Лаврентьевская летопись', 'Один из важнейших сохранившихся списков древнерусского летописания.', 'опубликован', 'http://localhost:9000/chronicles/lavrentevskaya-letopis.jpg', 'http://localhost:9000/chronicles/lavrentevskaya-letopis.mp4', 1377, 852, NOW(), 2, NOW()),
    ('Ипатьевская летопись', 'Летописный памятник, объединяющий киевскую, галицкую и волынскую традиции.', 'опубликован', 'http://localhost:9000/chronicles/ipatevskaya-letopis.jpg', 'http://localhost:9000/chronicles/ipatevskaya-letopis.mp4', 1425, 852, NOW(), 3, NOW()),
    ('Новгородская первая летопись', 'Один из основных письменных источников по истории средневекового Новгорода.', 'опубликован', 'http://localhost:9000/chronicles/novgorodskaya-pervaya.jpg', 'http://localhost:9000/chronicles/novgorodskaya-pervaya.mp4', 1250, 1016, NOW(), 4, NOW()),
    ('Новгородская четвёртая летопись', 'Памятник новгородского летописания, отражающий историю Новгорода и Руси.', 'опубликован', 'http://localhost:9000/chronicles/novgorodskaya-chetvertaya.jpg', 'http://localhost:9000/chronicles/novgorodskaya-chetvertaya.mp4', 1437, 862, NOW(), 5, NOW()),
    ('Псковская первая летопись', 'Основной летописный источник по истории средневекового Пскова.', 'опубликован', 'http://localhost:9000/chronicles/pskovskaya-pervaya.jpg', 'http://localhost:9000/chronicles/pskovskaya-pervaya.mp4', 1450, 859, NOW(), 6, NOW()),
    ('Московский летописный свод', 'Общерусский летописный свод конца XV века, созданный в Москве.', 'опубликован', 'http://localhost:9000/chronicles/moskovskiy-svod.jpg', 'http://localhost:9000/chronicles/moskovskiy-svod.mp4', 1479, 852, NOW(), 2, NOW()),
    ('Черновик нового источника', NULL, 'черновик', 'http://localhost:9000/chronicles/pending-image.jpg', 'http://localhost:9000/chronicles/pending-video.mp4', NULL, NULL, NOW(), 1, NULL),
    ('Удалённая Тверская летопись', 'Запись для демонстрации логического удаления.', 'удален', 'http://localhost:9000/chronicles/tverskaya.jpg', 'http://localhost:9000/chronicles/tverskaya.mp4', 1534, 1205, NOW(), 3, NOW());

INSERT INTO likes (user_id, chronicle_id) VALUES
    (1,1), (2,1), (3,1), (4,1),
    (1,2), (2,2), (5,2),
    (2,3), (3,3), (4,3), (5,3), (6,3),
    (1,4), (3,4),
    (2,5), (4,5), (6,5),
    (1,6), (4,6), (5,6), (6,6),
    (1,7), (2,7), (3,7);
