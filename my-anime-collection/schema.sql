DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS anime_shows;
DROP TABLE IF EXISTS anime_releases;
DROP TABLE IF EXISTS anime_collections;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE anime_shows (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL
);

CREATE TABLE anime_releases (
    id INTEGER PRIMARY KEY,
    anime_id INTEGER NOT NULL,
    disc_type TEXT NOT NULL,
    edition TEXT NOT NULL DEFAULT "Standard",
    release_date TIMESTAMP NOT NULL,
    FOREIGN KEY (anime_id) REFERENCES anime_shows (id)
);

CREATE TABLE anime_collections (
    user_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    release_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (anime_id) REFERENCES anime_shows(id),
    FOREIGN KEY (release_id) REFERENCES anime_releases (id)
);
