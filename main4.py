
# все зроблено за шаблоном викладача з дз 2 тільки вставлено мої дані

import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

# Налаштування підключення
HOST = 'localhost'
USER = 'postgres'
PASSWORD = 'musliM12'
DATABASE = 'homework4'
PORT = '5432'

# Налаштування обсягів даних
USERS_COUNT = 10_000        # Кількість користувачів
BOOKS_COUNT = 15_000        # Кількість книг
BORROWS_COUNT = 500_000     # Цільова таблиця на 500к+ рядків
CHUNK_SIZE = 10_000         # Розмір порції для вставки

fake = Faker()

def insert_static_data(cursor):
    print("Inserting into Reading_Halls and Genres...")

    # 1. Читальні зали
    halls_data = [
        ("Головний зал імені Сковороди", 150),
        ("Науковий читальний зал", 80),
        ("Зал періодики та журналів", 50),
        ("Зал іноземної літератури", 60),
        ("Дитячий сектор читання", 40)
    ]
    execute_values(cursor, "INSERT INTO Reading_Halls (name, capacity) VALUES %s ON CONFLICT DO NOTHING;", halls_data)

    # 2. Жанри
    genres_list = ["Фантастика", "Детектив", "Класика", "Історія", "Наука", "Поезія", "Біографія", "Психологія", "Роман", "Фентезі"]
    genres_data = [(genre, fake.text(max_nb_chars=100)) for genre in genres_list]
    execute_values(cursor, "INSERT INTO Genres (name, description) VALUES %s ON CONFLICT DO NOTHING;", genres_data)

    # Забираємо згенеровані ID
    cursor.execute("SELECT hall_id FROM Reading_Halls;")
    hall_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT genre_id FROM Genres;")
    genre_ids = [row[0] for row in cursor.fetchall()]

    return hall_ids, genre_ids

def insert_books(cursor, hall_ids, genre_ids):
    print("Inserting into Books...")
    book_insert_query = """
                        INSERT INTO Books (title, author, genre_id, hall_id, published_year, total_copies)
                        VALUES %s RETURNING book_id \
                        """

    book_ids = []
    # Генеруємо книги порціями
    for start in range(0, BOOKS_COUNT, CHUNK_SIZE):
        current_chunk_size = min(CHUNK_SIZE, BOOKS_COUNT - start)
        books_data = [
            (
                fake.sentence(nb_words=3).rstrip('.'),
                fake.name(),
                random.choice(genre_ids),
                random.choice(hall_ids),
                random.randint(1950, 2024),
                random.randint(3, 15)
            )
            for _ in range(current_chunk_size)
        ]
        # Використовуємо execute_values з поверненням id (потрібно для журналу)
        results = execute_values(cursor, book_insert_query, books_data, fetch=True)
        book_ids.extend([row[0] for row in results])
        print(f"Inserted {len(book_ids)} books...")

    return book_ids

def insert_users_and_profiles(cursor):
    print("Inserting into Users and User_Profiles...")
    user_insert_query = """
                        INSERT INTO Users (first_name, last_name, email, phone, registration_date)
                        VALUES %s RETURNING user_id \
                        """
    profile_insert_query = """
                           INSERT INTO User_Profiles (user_id, address, passport_data, date_of_birth)
                           VALUES %s \
                           """

    user_ids = []
    for start in range(0, USERS_COUNT, CHUNK_SIZE):
        current_chunk_size = min(CHUNK_SIZE, USERS_COUNT - start)
        users_data = []

        for _ in range(current_chunk_size):
            users_data.append((
                fake.first_name(),
                fake.last_name(),
                fake.unique.email(),
                fake.phone_number()[:20],
                fake.date_between(start_date='-3y', end_date='today')
            ))

        results = execute_values(cursor, user_insert_query, users_data, fetch=True)
        chunk_user_ids = [row[0] for row in results]
        user_ids.extend(chunk_user_ids)

        # Одразу створюємо профілі 1:1 для цього чанку користувачів
        profiles_data = [
            (
                u_id,
                fake.address().replace('\n', ', ')[:200],
                f"ID{random.randint(100000, 999999)}{u_id}",  # гарантія унікальності паспорта
                fake.date_of_birth(minimum_age=16, maximum_age=70)
            )
            for u_id in chunk_user_ids
        ]
        execute_values(cursor, profile_insert_query, profiles_data)
        print(f"Inserted {len(user_ids)} users and 1:1 profiles...")

    return user_ids

def insert_borrows(cursor, user_ids, book_ids):
    print("Inserting into Borrow_Log (500k rows)...")
    borrow_insert_query = """
                          INSERT INTO Borrow_Log (user_id, book_id, borrow_date, due_date, return_date)
                          VALUES %s \
                          """

    # Генеруємо історію за останні 3 роки
    for start in range(0, BORROWS_COUNT, CHUNK_SIZE):
        current_chunk_size = min(CHUNK_SIZE, BORROWS_COUNT - start)
        borrows_data = []

        for _ in range(current_chunk_size):
            borrow_date = fake.date_between(start_date='-3y', end_date='today')
            due_date = borrow_date + timedelta(days=random.randint(7, 30))
            # 80% книг повернуто, 20% — ще читають
            return_date = borrow_date + timedelta(days=random.randint(1, 40)) if random.random() < 0.8 else None

            borrows_data.append((
                random.choice(user_ids),
                random.choice(book_ids),
                borrow_date,
                due_date,
                return_date
            ))

        execute_values(cursor, borrow_insert_query, borrows_data)
        print(f"Inserted {start + current_chunk_size} rows into Borrow_Log...")

def main():
    # Створюємо підключення
    connection = psycopg2.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        dbname=DATABASE,
        port=PORT,
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                # Очищення таблиць перед запуском (опціонально, але зручно для тестів)
                print("Clearing tables...")
                cursor.execute("TRUNCATE Reading_Halls, Genres, Books, Users, User_Profiles, Borrow_Log, Fines CASCADE;")

                # Послідовний запуск усього процесу
                hall_ids, genre_ids = insert_static_data(cursor)
                book_ids = insert_books(cursor, hall_ids, genre_ids)
                user_ids = insert_users_and_profiles(cursor)
                insert_borrows(cursor, user_ids, book_ids)

                print("Базу даних бібліотеки успішно наповнено!")
    finally:
        connection.close()

if __name__ == "__main__":
    main()