drop table if exists Fines cascade;
drop table if exists Borrow_log cascade;
drop table if exists User_Profiles cascade;
drop table if exists Users cascade;
drop table if exists Books cascade;
drop table if exists Genres cascade;
drop table if exists Reading_Halls cascade;

--таблиця читальних жанрів
create table Reading_Halls(
	hall_id serial primary key,
	name varchar(100) not null unique,
    capacity int not null check (capacity > 0)
);
-- таблиця жанрів 
create table Genres(
	genre_id serial primary key,
    name VARCHAR(50) not null unique,
    description TEXT
	
);
--таблиця книг
create table Books(
	book_id serial primary key,
    title varchar(200) not null,
    author varchar(200) not null,
    genre_id int references Genres(genre_id) on delete set null,
    hall_id int references Reading_Halls(hall_id) on delete set null,
    published_year int check (published_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    total_copies int not null check (total_copies >= 0)
);
--таблиця користувачів
create table Users(
	user_id serial primary key,
    first_name varchar(50) not null,
    last_name varchar(50) not null,
    email varchar(100) not null unique,
    phone varchar(20),
    registration_date date default CURRENT_DATE
);
--таблиця профілів користувачів (звязок  1:1 )
create table User_Profiles(
	profile_id serial primary key,
    user_id int not null unique references Users(user_id) on delete cascade,
    address varchar(200),
    passport_data varchar(50) not null unique,
    date_of_birth date not null check (date_of_birth < CURRENT_DATE)
);
--таблиця журналу видачі книг( звязок Many-to-many між Users та books)
create table Borrow_log(
	log_id serial primary key,
    user_id int not null references Users(user_id) on delete cascade,
    book_id  int not null references Books(book_id) on delete cascade,
    borrow_date date not null default CURRENT_DATE,
    due_date date not null,
    return_date date,
    constraint check_dates check (due_date >= borrow_date),
    constraint check_return_date check (return_date is null or return_date >= borrow_date)
);
-- таблиця штрафів
create table Fines(
	fine_id serial primary key,
    log_id int  not null unique REFERENCES Borrow_Log(log_id) on delete cascade,
    amount DECIMAL(10, 2) not null check (amount >= 0),
    is_paid BOOLEAN not null default false
);


-- Створення базових індексів для зовнішніх ключів
CREATE INDEX idx_books_genre ON Books(genre_id);
CREATE INDEX idx_books_hall ON Books(hall_id);
CREATE INDEX idx_borrow_user ON Borrow_Log(user_id);
CREATE INDEX idx_borrow_book ON Borrow_Log(book_id);
