import logging
import os
import sqlite3
import threading
import string
import random

DATA_DIR = os.getenv("DATA_DIR", "app/data")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = os.path.join(DATA_DIR, "file_metadata.db")

logger = logging.getLogger(__name__)

# 使用线程锁来确保多线程环境下的数据库访问安全
db_lock = threading.Lock()

def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接。"""
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def generate_short_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def init_db() -> None:
    """初始化数据库，创建表。"""
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_id TEXT NOT NULL UNIQUE,
                    filesize INTEGER NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    short_id TEXT UNIQUE,
                    channel_name TEXT,
                    tags TEXT
                );
            """)
            
            # 检查现有列信息，做简单 migration
            cursor.execute("PRAGMA table_info(files)")
            columns = [info[1] for info in cursor.fetchall()]

            # 迁移: 补充 short_id 列
            if "short_id" not in columns:
                logger.info("Migrating database: adding short_id column...")
                try:
                    # SQLite 不支持在 ADD COLUMN 时直接指定 UNIQUE，需拆分为两步
                    cursor.execute("ALTER TABLE files ADD COLUMN short_id TEXT")
                except Exception as e:
                    logger.error("Migration warning: Failed to add short_id column: %s", e)

            # 迁移: 补充 channel_name 列
            if "channel_name" not in columns:
                logger.info("Migrating database: adding channel_name column...")
                try:
                    cursor.execute("ALTER TABLE files ADD COLUMN channel_name TEXT")
                except Exception as e:
                    logger.error("Migration warning: Failed to add channel_name column: %s", e)
                else:
                    # 尝试将历史数据的 channel_name 用当前 app_settings 的 channel_name 兜底填充
                    try:
                        cursor.execute(
                            """
                            UPDATE files
                            SET channel_name = (
                                SELECT channel_name FROM app_settings WHERE id = 1
                            )
                            WHERE channel_name IS NULL OR channel_name = ''
                            """
                        )
                    except Exception as e:  # pragma: no cover - 仅在迁移出错时记录
                        logger.error("Migration warning: Failed to backfill channel_name: %s", e)

            # 迁移: 补充 tags 列
            if "tags" not in columns:
                logger.info("Migrating database: adding tags column...")
                try:
                    cursor.execute("ALTER TABLE files ADD COLUMN tags TEXT")
                except Exception as e:
                    logger.error("Migration warning: Failed to add tags column: %s", e)

            # 确保唯一索引存在（幂等操作）
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_files_short_id ON files(short_id)")
            except Exception as e:
                logger.error("Migration warning: Failed to create index idx_files_short_id: %s", e)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    bot_token TEXT,
                    channel_name TEXT,
                    pass_word TEXT,
                    picgo_api_key TEXT,
                    base_url TEXT
                );
            """)
            # 确保存在单行设置记录
            cursor.execute("INSERT OR IGNORE INTO app_settings (id) VALUES (1)")
            conn.commit()
            logger.info("数据库已成功初始化")
        finally:
            conn.close()

def add_file_metadata(filename: str, file_id: str, filesize: int, channel_name: str | None = None) -> str:
    """
    向数据库中添加一个新的文件元数据记录。
    如果 file_id 已存在，则忽略。
    返回: short_id
    """
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # 归一化 channel_name，允许为 None
            ch = (channel_name or "").strip() or None
            tags = None  # 初始无标签
            
            # 尝试生成唯一的 short_id
            for _ in range(5):
                short_id = generate_short_id()
                try:
                    cursor.execute(
                        "INSERT INTO files (filename, file_id, filesize, short_id, channel_name, tags) VALUES (?, ?, ?, ?, ?, ?)",
                        (filename, file_id, filesize, short_id, ch, tags)
                    )
                    conn.commit()
                    logger.info("已添加文件元数据: %s, short_id: %s, channel: %s", filename, short_id, ch)
                    return short_id
                except sqlite3.IntegrityError as e:
                    if "short_id" in str(e):
                        continue  # 冲突重试
                    # 可能是 file_id 冲突，如果是这样，查询现有的 short_id
                    cursor.execute("SELECT short_id FROM files WHERE file_id = ?", (file_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        return row[0]
                    # 如果有记录但没 short_id (旧数据)，更新它
                    if row:
                        short_id = generate_short_id()
                        cursor.execute("UPDATE files SET short_id = ? WHERE file_id = ?", (short_id, file_id))
                        conn.commit()
                        return short_id
                    raise e
            
            # 如果多次重试失败（极低概率），抛错
            raise Exception("Failed to generate unique short_id")
            
        finally:
            conn.close()

def get_all_files() -> list[dict]:
    """从数据库中获取所有文件的元数据。"""
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename, file_id, filesize, upload_date, short_id, channel_name, tags "
                "FROM files ORDER BY upload_date DESC"
            )
            files = []
            for row in cursor.fetchall():
                d = dict(row)
                files.append(d)
            return files
        finally:
            conn.close()

def get_file_by_id(identifier: str) -> dict | None:
    """通过 file_id 或 short_id 从数据库中获取单个文件元数据。"""
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # 优先匹配 short_id，然后 file_id
            cursor.execute(
                "SELECT filename, filesize, upload_date, file_id, short_id, channel_name, tags "
                "FROM files WHERE short_id = ? OR file_id = ?",
                (identifier, identifier),
            )
            result = cursor.fetchone()
            if result:
                return {
                    "filename": result["filename"],
                    "filesize": result["filesize"],
                    "upload_date": result["upload_date"],
                    "file_id": result["file_id"],
                    "short_id": result["short_id"],
                    "channel_name": result["channel_name"],
                    "tags": result["tags"],
                }
            return None
        finally:
            conn.close()

def delete_file_metadata(file_id: str) -> bool:
    """
    根据 file_id 从数据库中删除文件元数据。
    返回: 如果成功删除了一行，则为 True，否则为 False。
    """
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
            conn.commit()
            # cursor.rowcount 会返回受影响的行数
            return cursor.rowcount > 0
        finally:
            conn.close()

def delete_file_by_message_id(message_id: int) -> str | None:
    """
    根据 message_id 从数据库中删除文件元数据，并返回其 file_id。
    因为一个消息ID只对应一个文件，所以我们可以这样做。
    """
    file_id_to_delete = None
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # 首先，根据 message_id 找到对应的 file_id
            # 我们使用 LIKE 操作符，因为 file_id 是 "message_id:actual_file_id" 的格式
            cursor.execute("SELECT file_id FROM files WHERE file_id LIKE ?", (f"{message_id}:%",))
            result = cursor.fetchone()
            if result:
                file_id_to_delete = result[0]
                # 然后，删除这条记录
                cursor.execute("DELETE FROM files WHERE file_id = ?", (file_id_to_delete,))
                conn.commit()
                logger.info("已从数据库中删除与消息ID %s 关联的文件: %s", message_id, file_id_to_delete)
            return file_id_to_delete
        finally:
            conn.close()

def get_app_settings_from_db() -> dict:
    """获取应用设置（从数据库单行配置）。"""
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT bot_token, channel_name, pass_word, picgo_api_key, base_url FROM app_settings WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return {}
            return {
                "BOT_TOKEN": row[0],
                "CHANNEL_NAME": row[1],
                "PASS_WORD": row[2],
                "PICGO_API_KEY": row[3],
                "BASE_URL": row[4],
            }
        finally:
            conn.close()

def save_app_settings_to_db(payload: dict) -> None:
    """保存应用设置到数据库（单行更新）。"""
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            def norm(v):
                if v is None:
                    return None
                if isinstance(v, str):
                    s = v.strip()
                    return s if s else None
                return v

            cursor.execute(
                """
                UPDATE app_settings
                SET bot_token = ?, channel_name = ?, pass_word = ?, picgo_api_key = ?, base_url = ?
                WHERE id = 1
                """,
                (
                    norm(payload.get("BOT_TOKEN")),
                    norm(payload.get("CHANNEL_NAME")),
                    norm(payload.get("PASS_WORD")),
                    norm(payload.get("PICGO_API_KEY")),
                    norm(payload.get("BASE_URL")),
                )
            )
            conn.commit()
        finally:
            conn.close()

def update_file_tags(file_id: str, tags: list[str] | None) -> bool:
    """
    更新指定文件的标签（以逗号分隔存储在 tags 字段中）。
    返回: 是否更新到至少一行。
    """
    tags_str = None
    if tags:
        # 去重 + 去空白
        cleaned = []
        seen = set()
        for t in tags:
            s = (t or "").strip()
            if not s:
                continue
            if s in seen:
                continue
            seen.add(s)
            cleaned.append(s)
        if cleaned:
            tags_str = ",".join(cleaned)

    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE files SET tags = ? WHERE file_id = ?",
                (tags_str, file_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def reset_app_settings_in_db() -> None:
    """重置应用设置（清空配置）。"""
    save_app_settings_to_db(
        {
            "BOT_TOKEN": None,
            "CHANNEL_NAME": None,
            "PASS_WORD": None,
            "PICGO_API_KEY": None,
            "BASE_URL": None,
        }
    )
