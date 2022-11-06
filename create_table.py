import json
import psycopg2

# читаем файл с фильмами
with open("films.json", "r") as f:
    films = json.load(f)

# подключаемся к БД
con = psycopg2.connect(
    dbname="online_shop_flask_db",
    user="postgres",
    password="Millioner1000000",
    host="localhost",
    port=5432
)

#  создаем экземпляр курсора, который непосредственно выполняет запросы
cur = con.cursor()

# выполняем создание таблицы
cur.execute("CREATE TABLE ad(id serial PRIMARY KEY, name varchar, price real, description varchar, quantity integer, category varchar)")

# коммитим изменения в БД, чтобы они сохранились
con.commit()

# подготавливаем inserts для создания записей о фильмах
inserts = ''
for film in films:
    inserts += f"INSERT INTO ad values ({film['id']}, '{film['name']}', {film['price']}, '{film['description']}', {film['quantity']}, '{film['category']}');\n"

# выполняем inserts
cur.execute(inserts)
# коммитим изменения
con.commit()

# закрываем подключение к БД
cur.close()
con.close()
