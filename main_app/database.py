from psycopg_pool import ConnectionPool
from app.config.main_config import settings

DB_URL = settings.db_config.db_url

MINIMUM_NUMBER_OF_CONNECTIONS = settings.db_config.min_connections

MAXIMUM_NUMBER_OF_CONNECTIONS = settings.db_config.max_connections

pool = ConnectionPool(
    conninfo=DB_URL,
    min_size=MINIMUM_NUMBER_OF_CONNECTIONS,
    max_size=MAXIMUM_NUMBER_OF_CONNECTIONS,
    kwargs={"autocommit": True},
)


def create_user_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            age SMALLINT CHECK (age >= 0 AND age <= 100) NOT NULL,
            email VARCHAR(255) UNIQUE,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            password TEXT NOT NULL,
            balance DECIMAL(10,2) NOT NULL CHECK (balance >= 0)
            );
        """)
    pool.putconn(conn)


def create_book_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books(
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author_id bigint REFERENCES authors(id) ON DELETE CASCADE,
            price DECIMAL(10,2) NOT NULL,
            count SMALLINT NOT NULL CHECK (count >= 0)
            );
        """)
    pool.putconn(conn)


def create_author_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS authors(
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            password TEXT NOT NULL
            );
        """)
    pool.putconn(conn)


def create_orders_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id SERIAL PRIMARY KEY,
            total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE,
            status VARCHAR(20) NOT NULL CHECK (status IN ('in_transit', 'delivered')) DEFAULT 'in_transit'
        ); 
        """)
    pool.putconn(conn)


def create_cart_items_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart_items(
            id SERIAL PRIMARY KEY,
            book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            is_order_placed BOOLEAN DEFAULT FALSE,
            cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE
            );
        """)
    pool.putconn(conn)


def create_cart_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS carts(
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            is_order_placed BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
    pool.putconn(conn)


def create_access_token_blacklist():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS access_token_blacklist(
            id SERIAL PRIMARY KEY,
            access_token VARCHAR(300) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    pool.putconn(conn)


def create_refresh_token_blacklist():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS refresh_token_blacklist(
            id SERIAL PRIMARY KEY,
            refresh_token VARCHAR(300) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    pool.putconn(conn)


def create_admin_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            token VARCHAR(255) NOT NULL,
            password TEXT NOT NULL);
        """)
    pool.putconn(conn)


def create_all_tables():
    create_author_table()
    create_book_table()
    create_user_table()
    create_refresh_token_blacklist()
    create_access_token_blacklist()
    create_cart_table()
    create_cart_items_table()
    create_orders_table()
    create_admin_table()

    conn = pool.getconn()
    exists = conn.execute("""SELECT EXISTS(SELECT * FROM admins)""").fetchone()[0]

    if not exists:
        conn.execute(
            """
            INSERT INTO admins(email, token, password) VALUES (%s, %s, %s)
            """,
            ("admin@gmail.com", "fa5943e5-9805-40ac-8537-a8e4010394d5", "1234"),
        )
    pool.putconn(conn)