from random import randint

from fastapi import HTTPException
from starlette import status

from ..schemes.jwt import ResponseJWTTokensSchema
from ..schemes.users import ResponseUserProfileSchema
from database import pool
from handler import handle_not_found, handle_unique
from security import get_hashed_password, get_jwt_tokens, is_password_correct

from celery_app import celery_app
from verify_code import save_verify_code_to_cache, get_verify_code_from_cache


def register_user(
    first_name: str, last_name: str, email: str, age: int, password: str, connection
):
    """
    Регистрирует пользователя с указанными данными.

    Получает и сохраняет хеш пароля.
    Получает и отдает jwt токены для аунтентификации.

    Args:
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        email: Почта пользователя.
        age: Возраст пользователя.
        password: Необработанный пароль пользователя.
        connection: Объект соединения для работы с БД.

    Returns:
        - Объект-схема ResponseJWTTokensSchema, с атрибутами (access_token, refresh_token).
    Raises:
        HTTPException:
            - status_code=HTTP_409_CONFLICT, detail="User already exists", если пользователь с такими данными уже существует.
    """

    hashed_password = get_hashed_password(password)

    user_id = save_user_to_db(
        first_name, last_name, email, age, hashed_password, connection=connection
    )

    jwt_tokens = get_jwt_tokens({"user_id": user_id})

    return ResponseJWTTokensSchema(
        access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
    )


def get_user_profile(user_id: int, connection):
    """
    Возвращает обработанные данные о профиле пользователя.

    В конце возвращает в пул соединение.

    Args:
        user_id: ID пользователя чей профиль нужно получить.
        connection: Объект соединения для работы с БД.

    Returns:
        - ResponseUserProfileSchema, объект-схема профиля с полями (first_name, last_name, email, age, balance).
    """

    raw_user_data = connection.execute(
        """
    SELECT first_name, last_name, email, age, balance FROM users WHERE id = %s;""",
        (user_id,),
    ).fetchone()

    processed_user_data = build_user_profile_data_response(raw_user_data)

    pool.putconn(connection)

    return processed_user_data


@handle_not_found
def build_user_profile_data_response(raw_user_profile: tuple):
    """
    Формирует объект ResponseUserProfileSchema из необработанных данных о профиле пользователя.

    Args:
        raw_user_profile: объект tuple, представляющий необработанную запись из БД.

    Returns:
        - Объект ResponseUserProfileSchema с атрибутами (first_name, last_name, email, age, balance).

    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="User not found, если передано None, в качестве аргумента.
    """

    processed_user_profile = ResponseUserProfileSchema(
        first_name=raw_user_profile[0],
        last_name=raw_user_profile[1],
        email=raw_user_profile[2],
        age=raw_user_profile[3],
        balance=raw_user_profile[4],
    )
    return processed_user_profile


@handle_unique
def save_user_to_db(
    first_name: str,
    last_name: str,
    email: str,
    age: int,
    hashed_password: str,
    connection,
):
    """
    Сохраняет данные о пользователе в БД.

    Args:
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        email: Почта пользователя.
        age: Возраст пользователя.
        hashed_password: Хеш пользовательского пароля.
        connection: Объект соединения для работы с БД.

    Returns:
        user_id - ID пользователя.
    """

    user_id = connection.execute(
        """
    INSERT INTO users (first_name, last_name, email, age, password, balance)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;""",
        (first_name, last_name, email, age, hashed_password, 0),
    ).fetchone()[0]

    pool.putconn(connection)

    return user_id


def get_raw_user_by_email(email: str, connection):
    """
    Возвращает, необработанные данные о пользователе по его email.

    Args:
        email: Почта, по которой нужно получить пользователя.
        connection: Объект соединения для работы с БД.

    Returns:
        - Возвращает tuple, в котором необработанные данные пользователя.
        - None, если пользователь с таким email не существует.
    """

    user = connection.execute(
        """SELECT id, email, age, first_name, password FROM users WHERE email = %s;""",
        (email,),
    ).fetchone()

    return user


def login_user(email: str, password: str, connection):
    """
    Аутентифицирует пользователя по email и password.

    Args:
        email: Почта пользователя, которую нужно проверить.
        password: Пароль пользователя, который нужно проверить.
        connection: Объект соединения для работы с БД.

    Returns:
        - Объект-схема ResponseJWTTokensSchema, с атрибутами (access_token, refresh_token).
    Raises:
        HTTPException:
            - status_code=400, detail="Incorrect email or password", если почта или пароль не были подтверждены.
    """

    user = get_raw_user_by_email(email, connection)

    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    hashed_password = user[4].encode()

    if is_password_correct(password.encode(), hashed_password):
        jwt_tokens = get_jwt_tokens({"user_id": user[0]})
        pool.putconn(connection)
        return ResponseJWTTokensSchema(
            access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
        )

    raise HTTPException(status_code=400, detail="Incorrect email or password")


def is_user_exists(email: str, connection):
    """
    Проверяет, существует ли пользователь с таким email.

    Args:
        email: Почта, по которой ищем пользователя.
        connection: Объект соединения для работы с базой данных.

    Returns:
        - True, если пользователь найден.
        - False, если пользователь не найден.
    """

    user = get_raw_user_by_email(email, connection)

    if user is not None:
        return True

    return False


def logout_user(access_token: str, refresh_token: str, connection):
    """
    Отзывает access и refresh токены и добавляет их в blacklist, и больше по ним нельзя будет зайти в систему.

    Управляет транзакцией: открывает и откатывает все изменения в случае ошибки, или сохраняет все изменения,
    если всё хорошо.

    Args:
        access_token: Коротко живущий токен пользователя, который будет добавлен в blacklist.
        refresh_token: Долго живущий токен пользователя, который будет добавлен в blacklist.
        connection: Объект соединения для работы с базой данных.

    Returns:
        None.
    """

    try:
        connection.execute("""BEGIN""")

        connection.execute(
            """INSERT INTO access_token_blacklist(access_token)
               VALUES (%s);
            """,
            (access_token,),
        )

        connection.execute(
            """
                INSERT INTO refresh_token_blacklist(refresh_token)
                VALUES (%s);
            """,
            (refresh_token,),
        )

        connection.execute("""COMMIT""")

        return None

    except:
        connection.execute("""ROLLBACK""")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
        )

    finally:
        pool.putconn(connection)


def update_balance(amount: float, user_id: int, connection, is_top_up: bool = True):
    """
    Обновляет баланс пользователя и либо уменьшает его, либо увеличивает.

    Args:
        amount: сумма (в рублях), на которую либо уменьшится баланс, либо увеличиться.
        is_top_up: Флаг, который определяет действие с балансом: увеличиваем (если True, который по умолчанию)
         или уменьшаем (если False).
        user_id: ID пользователя, чей баланс нужно изменять.
        connection: объект соединения для работы с БД.

    Returns:
        - None.
    """

    operator = "+" if is_top_up else "-"
    connection.execute(
        f"""
        UPDATE users
        SET balance = balance {operator} %s
        WHERE id = %s
        """,
        (amount, user_id),
    )
    return None


def check_if_enough_money_in_the_account_balance(
    amount: float, user_id: int, connection
):
    """
    Проверяет, достаточно ли у пользователя денег на балансе, чтобы списать определенную сумму.

    Args:
        amount: Сумма (в руб.), которая будет потенциально списана.
        user_id: ID пользователя, для которого нужно проверить баланс.
        connection: объект соединения для работы c БД.

    Returns:
        - None.

    Raises:
        HTTPException:
            - status_code=HTTP_400_BAD_REQUEST, detail="Incorrect balance", если денег на балансе пользователя недостаточно.
    """

    user_balance = connection.execute(
        """SELECT balance FROM users WHERE id = %s""",
        (user_id,),
    ).fetchone()[0]

    if user_balance < amount:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect balance"
        )

    return None


def top_up_balance(amount: float, user_id: int, connection):
    """
    Пополняет баланс пользователя на указанную сумму.

    Args:
        amount: сумма (в руб.), на которую пополняет сумму.
        user_id: ID пользователя, для которого пополняет баланс.
        connection: объект соединения для работы с БД.

    Returns:
        - None
    """

    connection.execute(
        """
        UPDATE users
        SET balance = balance + %s
        WHERE id = %s
        """,
        (amount, user_id),
    )

    return None


def send_email_task(user_email: str, message: str):
    """
    Отправляет задачу (отправить письмо с указанным сообщением) в брокер, чтобы потом воркеры обработали.

    Args:
        user_email: почта пользователя, на которую отправится письмо.
        message: сообщение, которое будет в письме.

    Returns:
        None.
    """

    celery_app.send_task("send_email", args=[message, user_email])

    return None


def verify_email(user_email: str, connection):
    """
    Проверяет, что пользователя с таким email не существует в БД, и если email
    не использованный, то отправляет на почту код подтверждения.

    Args:
        user_email: почта пользователя, которую нужно проверить и верифицировать.
        connection: объект соединения для работы с БД.

    Returns:
        None.
    """

    if is_user_exists(user_email, connection):
        pool.putconn(connection)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    pool.putconn(connection)

    # Формируем рандомный код подтверждения.
    # Если цифр не хватает до 6-значного числа, то добавляем в начало нули.
    verify_code = str(randint(0, 999_999))
    verify_code = verify_code.zfill(6)

    save_verify_code_to_cache(
        user_email, verify_code
    )  # Сохраняем код в кеш, чтобы быстро проверять его по email, с ttl 2 минуты.

    send_email_task(user_email, verify_code)

    return None


def check_verify_code(user_email: str, verify_code: str):
    """
    Проверяет, правильность введенного кода подтверждения для пользователя с заданной почтой.

    Сверяет код подтверждения с тем, что лежит в кешэ.

    Args:
        user_email: почта, по которой будет искать код подтверждения.
        verify_code: код подтверждения, который нужно проверить.

    Returns:
        None.
    """

    true_verify_code = get_verify_code_from_cache(user_email)

    if verify_code != true_verify_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect verify_code"
        )

    return None


def get_user_email_by_order_id(order_id: int, connection):
    """
    Возвращает почту пользователя, которому принадлежит заказ с таким order_id.

    Args:
        order_id: ID заказа, почту владельца которого нужно получить.
        connection: объект соединения для работы с БД.

    Returns:
        - Объект str представляющий почту пользователя.
    """

    user_email = connection.execute(
        """
        SELECT u.email FROM users u
        JOIN orders o ON o.user_id = u.id
        WHERE o.id = %s
        """,
        (order_id,),
    ).fetchone()[0]

    return user_email
