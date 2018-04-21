import unittest
from proj4 import *

DBNAME = 'food.db'

class TestGetData(unittest.TestCase):
    restaurants = get_data('ann arbor')

    def test_Yelp(self):
        data = self.restaurants[0]
        self.assertEqual(data[0].name, 'Poke Fish')
        self.assertEqual(data[0].rating, 4.5)
        self.assertEqual(data[0].address, '3500 Washtenaw Ave')
        self.assertEqual(data[10].name, 'Isalita')
        self.assertEqual(data[10].avg_rating, 4.15)
        self.assertEqual(data[10].address, '341 E Liberty St')


    def test_Google(self):
        data = self.restaurants[1]
        self.assertEqual(data[0].name, 'Poke fish sushi')
        self.assertEqual(data[0].avg_rating, 4.55)
        self.assertEqual(data[0].address, '3500 Washtenaw Ave')
        self.assertEqual(data[10].name, 'Isalita')
        self.assertEqual(data[10].rating, 4.3)
        self.assertEqual(data[10].address, '341 E Liberty St')

    def test_categories(self):
        data = self.restaurants[2]
        self.assertEqual(data['Bars'], 4)
        self.assertEqual(data['Desserts'], 1)



class TestMakeDatabase(unittest.TestCase):
    make_database(get_data('ann arbor'))

    def test_Yelp(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        statement = 'SELECT Count(*) '
        statement += 'FROM Yelp as Y '
        statement += 'WHERE Y.Categories LIKE "%,Bars,%" '

        cur.execute(statement)
        for row in cur:
            self.assertEqual(row[0], 4)


        statement = 'SELECT Rating '
        statement += 'FROM Yelp as Y '
        statement += 'WHERE Y.Categories LIKE "%,Indian,%" '

        cur.execute(statement)
        for row in cur:
            self.assertEqual(row[0], 4.0)


        statement = 'SELECT Count(*) '
        statement += 'FROM Yelp as Y '
        statement += 'WHERE Y.Categories LIKE "%,Barbeque,%" '

        cur.execute(statement)
        for row in cur:
            self.assertEqual(row[0], 1)


        statement = 'SELECT Address '
        statement += 'FROM Yelp as Y '
        statement += 'WHERE Y.Categories LIKE "%,Asian Fusion,%" '

        cur.execute(statement)
        for row in cur:
            self.assertEqual(row[0], '114 W Liberty St')

        conn.close()


    def test_Google(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        statement = 'SELECT * '
        statement += 'FROM Google as G '

        cur.execute(statement)
        row = cur.fetchone()
        self.assertEqual(row[1], 'Poke fish sushi')
        self.assertEqual(row[3], 4.55)
        self.assertEqual(row[9], -83.689106)


        statement = 'SELECT * '
        statement += 'FROM Google as G '
        statement += 'WHERE G.Name LIKE "%Isalita%" '

        cur.execute(statement)
        for row in cur:
            self.assertEqual(row[3], 4.15)
            self.assertEqual(row[5], '341 E Liberty St')
            self.assertEqual(row[10], -1)

        conn.close()



class TestProcessing(unittest.TestCase):
    restaurants = get_data('ann arbor')
    make_database(restaurants)
    top_yelp_cats = restaurants[2].most_common(10)

    def test_find_average_rating_cat(self):
        data = find_average_rating_cat(top_yelp_cats)
        self.assertEqual(data[0][0], 'Bars')
        self.assertEqual(data[0][1], 4)
        self.assertEqual(data[0][2], 4.0)
        self.assertEqual(data[0][3], 4.2375)
        self.assertEqual(data[0][4], 4.475)

    def test_find_average_rating_cat(self):
        data = find_average_rating_res('Bars')
        self.assertEqual(data[1][0], 'Mikette Bistro and Bar')
        self.assertEqual(data[1][1], 4.0)
        self.assertEqual(data[1][2], 4.25)
        self.assertEqual(data[1][3], 4.5)



unittest.main()
