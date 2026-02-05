-- 기존 통계 테이블
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    path TEXT,
    label TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 직접 작성하는 블로그 포스트 테이블
CREATE TABLE IF NOT EXISTS manual_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT NOT NULL,
    category TEXT,
    image_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);