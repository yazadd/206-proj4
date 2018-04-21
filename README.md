# Project 4 Overview

### Data Sources
For my final project, I built a program that accepts a city name as input from the user and then returns ratings for different restaurant categories, e.g. bar, coffee shop, Chinese, Mexican. These ratings come from Google and Yelp, specifically through the Google Places API and the Yelp Fusion API. Instructions to get Google's API Key can be found [here]( https://developers.google.com/places/web-service/get-api-key), and instructions to get Yelp's API Key can be found [here]( https://www.yelp.com/developers/documentation/v3/authentication). The format of my secrets.py file is as follows:

```
google_places_key = <API KEY>
yelp_fusion_key= <API KEY>
```
My program also uses Plotly to display graphs and charts based on user input. You can get started with Plotly [here](https://plot.ly/python/getting-started/).

### Code Structure
My code is separated into a few key functions:
- **get_data()** takes a city name as a parameter and uses this to search Yelp for food and drink businesses in that city. This data is then parsed and each business is added into a *yelp_restaurants* list as a new *'Business'* class instance. My program then loops through this list and, for each Yelp business, it uses Google's Nearby Places search to find a matching business in Google Places. It gets the *place_id* from the matching business and uses Google's Place Details search to get additional info about that business. This is then added into a *google_reatuarants* list with an id number that matches the Yelp business it was derived from.
- **make_database()** takes in the restaurant lists from *get_data()* and uses them to build and populate two tables ('Yelp' and 'Google') in the food.db database.
- **interactive_prompt()** uses a loop to gather input from the user and make the program interactive. After some preliminary if-statement checks, it passes the user's input to *process_command()*.
- **process_command()** parses and interprets the user's input and uses it to generate data for a city, as well as call the functions which query the database and produce Plotly graphs.

### User Guide
To run the program, open up a terminal window and navigate to the directory which contains proj4.py. Run `python3 proj4.py` or `python proj4.py`, depending on your python installation setup. The program will prompt you for an input. The first input must be a city name, in the format `city <city name>`, for example `city ann arbor`. Once some city data has been generated, you can select a display option by typing `display` followed by one of the following commands (these commands are not order-sensitive, e.g. `display pie categories ratings` is a valid command):
- `ratings categories scatter` shows a scatter graph of the average ratings (Yelp, Google, and Yelp + Google) of the restaurants in each of the top 10 categories in a city.
- `ratings categories pie` shows a pie chart of the average ratings (Yelp + Google only) of the restaurants in each of the top 10 categories in a city.
- `scatter restaurants ratings` shows a scatter graph of the average ratings (Yelp, Google, and Yelp + Google) of all of the restuarants in a category of your choice in a city.
- `proportions categories pie` shows a pie chart of the number of restaurants in each of the top 10 categories in a city.
