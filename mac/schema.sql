DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS anime_shows;
DROP TABLE IF EXISTS anime_releases;
DROP TABLE IF EXISTS anime_collections;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE anime_shows (
    anime_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    precision TEXT NOT NULL
);

CREATE TABLE anime_releases (
    release_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    release_title TEXT NOT NULL,
    disc_type TEXT NOT NULL,
    edition TEXT NOT NULL DEFAULT "Standard",
    release_date TEXT NOT NULL,
    image TEXT,
    FOREIGN KEY (anime_id) REFERENCES anime_shows (anime_id),
    PRIMARY KEY (release_id, anime_id)
);

CREATE TABLE anime_collections (
    user_id INTEGER NOT NULL,
    anime_id INTEGER NOT NULL,
    release_id INTEGER NOT NULL,
    price_bought INTEGER,
    date_bought TEXT,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (anime_id) REFERENCES anime_shows (anime_id),
    FOREIGN KEY (release_id) REFERENCES anime_releases (release_id),
    PRIMARY KEY (user_id, release_id)
);
