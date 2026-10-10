from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="postgres://shop:1234@shop-postgres:5432/shop_db",
    min_size=10,
    max_size=15,
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


def create_cart_table():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS carts(
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            is_order_placed BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)


def create_token_blacklist():
    conn = pool.getconn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_blacklist(
            id SERIAL PRIMARY KEY,
            token VARCHAR(300) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)


def create_all_tables():
    create_author_table()
    create_book_table()
    create_user_table()
    create_token_blacklist()
    create_cart_table()
    create_cart_items_table()
    create_orders_table()
