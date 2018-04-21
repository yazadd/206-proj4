import requests
import sqlite3
import csv
import json
import sys
import urllib
import pprint
import secrets
from collections import Counter
import plotly.plotly as py
import plotly.graph_objs as go
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.parse import urlencode

#### API CREDENTIALS AND DATABASE NAME####
places_key = secrets.google_places_key
yelp_key = secrets.yelp_fusion_key
DBNAME = 'food.db'


#### CACHING FUNCTION ####
# On startup, try to load data from the cache file
CACHE_FNAME = 'proj4_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}


# A helper function that accepts 2 parameters
# and returns a string that uniquely represents the request
# that could be made with this info (url + params)
def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

# The main cache function: it will always return the result for this
# url+params combo. However, it will first look to see if we have already
# cached the result and, if so, return the result from cache.
# If we haven't cached the result, it will get a new one (and cache it)
def make_request_using_cache(baseurl, params, headers):
    unique_ident = params_unique_combination(baseurl, params)

    # First, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        # print("Fetching cached data...")
        return CACHE_DICTION[unique_ident]

    # If not, fetch the data, add it to the cache, then write the cache to file
    else:
        # print("Making a request for new data...")
        # Make the request and cache the new data
        if headers == "google":
            resp = requests.get(baseurl, params)
        else:
            resp = requests.get(baseurl, params=params, headers=headers)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME, "w")
        fw.write(dumped_json_cache)
        fw.close()  # Close the open file
        return CACHE_DICTION[unique_ident]

# Gets data from the Google Places API, using the cache
def get_place_details(place_id):
    baseurl = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {'key': places_key, 'placeid': place_id}
    headers = "google"
    return make_request_using_cache(baseurl, params, headers)

# Gets data from the Google Places API, using the cache
def get_nearby_places(lat, lng, name):
    baseurl = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {'key': places_key, 'location': str(lat) + ',' + str(lng),
     'rankby': 'distance', 'keyword': name.replace(' ', '+')}
    headers = "google"
    return make_request_using_cache(baseurl, params, headers)

# Gets data from the Google Places API, using the cache
def get_yelp_data(city):
    baseurl = 'https://api.yelp.com/v3/businesses/search'
    params = {'location': city.replace(' ', '+'), 'term': 'restaurant'}
    headers = {'Authorization': 'Bearer %s' % yelp_key, }
    return make_request_using_cache(baseurl, params, headers)


class Business:
    def __init__(self, id, name, rating, avg_rating,
                num_reviews, address, city, state, latitude, longitude,
                price, categories, source_count = 1):
        self.id = id
        self.name = name
        self.rating = rating
        self.avg_rating = avg_rating
        self.num_reviews = num_reviews
        self.address = address
        self.city = city
        self.state = state
        self.latitude = latitude
        self.longitude = longitude
        self.price = price
        self.categories = categories
        self.source_count = source_count


def get_data(city):
    # Find Yelp restaurants
    yelp_restaurants = []
    google_restaurants = []
    yelp_categories = []
    google_categories = []
    data = get_yelp_data(city)

    if len(data['businesses']) == 0:
        print("No data is available for this city. Please try a different city.")
        return False

    i = 0
    for business in data['businesses']:
        cats = []
        for cat in business['categories']:
            cats.append(cat['title'])
        yelp_categories.extend(cats)

        temp_biz = Business(
            i,
            business['name'],
            business['rating'],
            -1,
            business['review_count'],
            business['location']['display_address'][0],
            business['location']['city'],
            business['location']['state'],
            business['coordinates']['latitude'],
            business['coordinates']['longitude'],
            business['price'],
            cats
        )

        yelp_restaurants.append(temp_biz)
        i += 1

    # Find Google Places restaurants
    for restaurant in yelp_restaurants:
        places = get_nearby_places(restaurant.latitude, restaurant.longitude, restaurant.name)

        if places['status'] == "OK":
            details = get_place_details(places['results'][0]['place_id'])

            if details['status'] == "OK":
                business = details['result']

                avg_rat = float((restaurant.rating + float(business['rating'])) / 2)
                restaurant.avg_rating = round(avg_rat, 2)

                temp_biz = Business(
                    restaurant.id,
                    business['name'],
                    business['rating'],
                    restaurant.avg_rating,
                    -1,
                    restaurant.address,
                    restaurant.city,
                    restaurant.state,
                    business['geometry']['location']['lat'],
                    business['geometry']['location']['lng'],
                    -1,
                    business['types']
                )
                google_categories.extend(business['types'])
                restaurant.source_count = 2
                google_restaurants.append(temp_biz)

    return [yelp_restaurants, google_restaurants, Counter(yelp_categories), Counter(google_categories)]



def make_database(restaurants):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Yelp';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Google';
    '''
    cur.execute(statement)
    conn.commit()

    # Create tables in choc.db
    statement = '''
        CREATE TABLE 'Yelp' (
            'Id' INTEGER PRIMARY KEY,
            'Name' TEXT NOT NULL,
            'Rating' REAL,
            'AverageRating' REAL,
            'ReviewCount' INTEGER,
            'Address' TEXT NOT NULL,
            'City' TEXT NOT NULL,
            'State' TEXT NOT NULL,
            'Latitude' REAL NOT NULL,
            'Longitude' REAL NOT NULL,
            'Price' TEXT,
            'Categories' TEXT
        );
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Google' (
            'Id' INTEGER PRIMARY KEY,
            'Name' TEXT NOT NULL,
            'Rating' REAL,
            'AverageRating' REAL,
            'ReviewCount' INTEGER,
            'Address' TEXT NOT NULL,
            'City' TEXT NOT NULL,
            'State' TEXT NOT NULL,
            'Latitude' REAL NOT NULL,
            'Longitude' REAL NOT NULL,
            'Price' INTEGER,
            'Categories' TEXT
        );
    '''
    cur.execute(statement)
    conn.commit()

    # Read data into tables
    for restaurant in restaurants[0]:
        insertion = (restaurant.id, restaurant.name, restaurant.rating,
                     restaurant.avg_rating, restaurant.num_reviews, restaurant.address, restaurant.city, restaurant.state, restaurant.latitude, restaurant.longitude, restaurant.price, ','+','.join(restaurant.categories)+',')
        statement = 'INSERT INTO "Yelp" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

    for restaurant in restaurants[1]:
        insertion = (restaurant.id, restaurant.name, restaurant.rating,
                     restaurant.avg_rating, restaurant.num_reviews, restaurant.address, restaurant.city, restaurant.state, restaurant.latitude, restaurant.longitude, restaurant.price, ','+','.join(restaurant.categories)+',')
        statement = 'INSERT INTO "Google" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()

    conn.close()



# Average Rating per Category
def find_average_rating_cat(top_yelp_cats):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    return_list = []

    for key, value in dict(top_yelp_cats).items():
        statement = 'SELECT AVG(Y.Rating), AVG(Y.AverageRating), AVG(G.Rating) '
        statement += 'FROM Yelp as Y JOIN Google as G ON Y.Id = G.Id '
        statement += 'WHERE Y.Categories LIKE "%,{},%"'.format(key)

        cur.execute(statement)
        for row in cur:
            return_list.append((key, value, row[0], row[1], row[2]))

    conn.close()
    return return_list

def print_average_rating_cat_scat(data):
    x = []
    y1 = []
    y2 = []
    y3 = []

    for row in data:
        x.append(row[0])
        y1.append(row[2])
        y2.append(round(row[3],2))
        y3.append(row[4])


    trace1 = go.Scatter(name = 'Yelp', x = x, y = y1, mode = 'lines+markers')

    trace2 = go.Scatter(name = 'Yelp + Google', x = x, y = y2, mode = 'lines+markers')

    trace3 = go.Scatter(name = 'Google', x = x, y = y3, mode = 'lines+markers')

    layout = go.Layout(title = "Average Ratings for Top 10 Categories",
                       xaxis = dict(title = 'Category'),
                       yaxis = dict(title = 'Average Category Rating'),
                       height=700, width=1000)

    data = [trace1, trace2, trace3]
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig)

def print_average_rating_cat_pie(data):
    labels = []
    values = []

    for row in data:
        labels.append(row[0])
        values.append(round(row[3],2))

    colors = ['#4891F3', '#4D76BF', '#D4DD58', '#FFC031', '#FF983B', '#E14548', '#BF3E4B', '#E04D78', '#BC53A4', '#9E5CBB']

    trace = go.Pie(labels=labels, values=values,
                   hoverinfo='label+percent', textinfo='value',
                   marker=dict(colors=colors), textfont=dict(color = '#FFFFFF'))

    layout = go.Layout(title = "Top 10 Categories' Average Ratings",
                       height=700, width=1000)

    data = [trace]
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig)


# Ratings for Restaurants in a Particular Category
def find_average_rating_res(category):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    return_list = []

    statement = 'SELECT Y.Name, Y.Rating, Y.AverageRating, G.Rating '
    statement += 'FROM Yelp as Y JOIN Google as G ON Y.Id = G.Id '
    statement += 'WHERE Y.Categories LIKE "%,{},%"'.format(category)

    cur.execute(statement)
    for row in cur:
        return_list.append((row[0], row[1], row[2], row[3]))

    conn.close()
    return return_list

def print_average_rating_res(data, category):
    x = []
    y1 = []
    y2 = []
    y3 = []

    for row in data:
        x.append(row[0])
        y1.append(row[1])
        y2.append(row[2])
        y3.append(row[3])


    trace1 = go.Scatter(name = 'Yelp', x = x, y = y1, mode = 'markers')

    trace2 = go.Scatter(name = 'Yelp + Google', x = x, y = y2, mode = 'markers')

    trace3 = go.Scatter(name = 'Google', x = x, y = y3, mode = 'markers')

    layout = go.Layout(title = "Ratings for Restaurants in " + category,
                       xaxis = dict(title = 'Restaurant'),
                       yaxis = dict(title = 'Rating'),
                       height=700, width=1000)

    data = [trace1, trace2, trace3]
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig)


# Ratings for Restaurants in a Particular Category
def find_cat_proportions(top_yelp_cats):
    return top_yelp_cats

def print_cat_proportions(data):
    labels = []
    values = []

    for key, value in dict(data).items():
        labels.append(key)
        values.append(value)

    colors = ['#4891F3', '#4D76BF', '#D4DD58', '#FFC031', '#FF983B', '#E14548', '#BF3E4B', '#E04D78', '#BC53A4', '#9E5CBB']

    trace = go.Pie(labels=labels, values=values,
                   hoverinfo='label+percent', textinfo='value',
                   marker=dict(colors=colors), textfont=dict(color = '#FFFFFF'))

    layout = go.Layout(title = "Top 10 Categories' Sizes",
                       height=700, width=1000)

    data = [trace]
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig)

# Command Processor
def process_command(command, city_found, top_yelp_cats, top_google_cats):
    # Exit command
    if command == "exit":
        print("Bye!")
        sys.exit()

    # Read and interpret commands
    commands = command.split()
    main_cmd = commands.pop(0)


    if main_cmd == 'city':
        city = ' '.join(commands)
        restaurants = get_data(city)
        if not restaurants:
            print("No data was found for this city. Please try again.")
            return

        city_found[0] = True
        make_database(restaurants)

        top_yelp_cats[:] = restaurants[2].most_common(10)
        top_google_cats[:] = restaurants[3].most_common(10)
        print("City data generated.")


    elif main_cmd == 'display':
        if not city_found:
            print("Error: You must generate data for a city before calling the display commands.")
            return


        if 'ratings' in commands and 'categories' in commands and 'scatter' in commands:
            data = find_average_rating_cat(top_yelp_cats)
            print_average_rating_cat_scat(data)

        elif 'ratings' in commands and 'categories' in commands and 'pie' in commands:
            data = find_average_rating_cat(top_yelp_cats)
            print_average_rating_cat_pie(data)

        elif 'ratings' in commands and 'restaurants' in commands and 'scatter' in commands:
            i = 1
            for key, val in top_yelp_cats:
                print (i, key)
                i += 1

            response = input("Enter a category's number: ")

            data = find_average_rating_res(top_yelp_cats[int(response) - 1][0])
            print_average_rating_res(data, top_yelp_cats[int(response) - 1][0])

        elif 'proportions' in commands and 'categories' in commands and 'pie' in commands:
            data = find_cat_proportions(top_yelp_cats)
            print_cat_proportions(data)

        else:
            print("Command not recognized:", ','.join(commands))
            return


    else:
            print("Command not recognized.")
            return



# Interactive Prompt
def interactive_prompt():
    city_found = [False]
    top_yelp_cats = []
    top_google_cats = []

    print("Your first command must be a city name. Once data has been generated for a particular city,\nyou can call the 'display' commands or update the city data at any time.")

    response = ''
    while response != 'exit':
        response = input('Enter a command: ')

        if response == 'help':
            print("Enter 'city' followed by the name of a city or, once you've generated a city's data,\nenter 'display' followed by one of the following commands (the words after display\ncan be in any order):")
            print("- ratings categories scatter")
            print("- ratings categories pie")
            print("- scatter restaurants ratings")
            print("- proportions categories pie")
            print()
            continue

        if not response:
            print()
            continue

        process_command(response, city_found, top_yelp_cats, top_google_cats)
        print()


# Main Code
if __name__ == "__main__":
    interactive_prompt()
