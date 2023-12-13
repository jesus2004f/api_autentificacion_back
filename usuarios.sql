CREATE TABLE usuarios (
    username TEXT PRIMARY KEY,
    password TEXT,
    token TEXT DEFAULT NULL
);


ALTER TABLE usuarios
ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE usuarios ADD COLUMN expiration_timestamp INTEGER;