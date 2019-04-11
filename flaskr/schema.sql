DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS likedPosts;

CREATE TABLE user (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL
);

CREATE TABLE post (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	author_id INTEGER NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	title TEXT NOT NULL,
	body TEXT NPT NULL,
	FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE likedPosts (
	postId INTEGER NOT NULL,
	userId INTEGER NOT NULL
);

INSERT INTO likedPosts (postId, userId)
VALUES (0,0);