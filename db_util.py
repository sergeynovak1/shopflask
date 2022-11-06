import psycopg2


class Database:
    def __init__(self):
        self.con = psycopg2.connect(
            dbname="online_shop_flask_db",
            user="postgres",
            password="Millioner1000000",
            host="localhost",
            port=5432
        )
        self.cur = self.con.cursor()

    def get_data(self):
        pass

    def insert(self, query):
        self.cur.execute(query)
        self.con.commit()

    def select(self):
        data = self.prepare_data(self.cur.fetchall())
        if len(data) == 1:
            data = data[0]

        return data

    def execute(self, query):
        self.cur.execute(query)
        data = self.prepare_data(self.cur.fetchall())
        if len(data) == 1:
            data = data[0]

        return data

    def prepare_data(self, data):
        films = []
        if len(data):
            column_names = [desc[0] for desc in self.cur.description]
            for row in data:
                films += [{c_name: row[key] for key, c_name in enumerate(column_names)}]

        return films