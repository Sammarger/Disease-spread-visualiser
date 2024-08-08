from django.shortcuts import render
from django.views.generic import ListView, CreateView
import requests
import math
from .models import usersymptoms, usersymptom_form
from django.contrib.auth.models import User

# PLOTTING GRAPHS
from plotly.offline import plot
import plotly.express as px
import pandas
import json

# WEB SCRAPING
import sqlite3
import csv
from bs4 import BeautifulSoup

#Each function within views.py is associated with a webpage and a URL pattern within urls.py

# Django framework allows table, such as usersymptoms, to be called and rendered on to an HTTP webpage
class SymptomsListView(ListView):
    model = usersymptoms
    template_name = "front/front.html"
    context_object_name = 'symptoms'
    ordering = ['-date_set']

class SymptomsCreateView(CreateView):
    model = usersymptoms
    form_class = usersymptom_form

 #Before form is submitted, that forms author is automatically the currently logged in user
    def form_valid(self, form):
        form.instance.user_id = self.request.user
        #Parent class form author is overriden to be current user before form is created
        return super().form_valid(form)

def map_data(request):
    #Request Model parses a chosen HTML page, and beautiful soup is able to extract data from the HTML template
    url = "https://www.worldometers.info/coronavirus/#countries"
    worldMetersCountries = requests.get(url)
    soup = BeautifulSoup(worldMetersCountries.content, 'html.parser')



    # Function takes called line and strips all HTML code by removing everything within <>, leaving only text
    def stripHtmlBrackets(line):
        stripChar = False
        strippedLine = ""
        line = list(line)
        for i in line:
            if i == '<':
                stripChar = True

            elif i == '>':
                stripChar = False

            if stripChar == False and i != ",":
                strippedLine += str(i)

        strippedLine = strippedLine.strip('>')
        return (strippedLine)

    def AddQuotationMarks(unquoted_data):
        quoted_data = '"' + unquoted_data + '"'
        return (quoted_data)


    # Table is the list of countries that hold the key information I want to extract
    tables = soup.find_all('table')

    #All countries can be found under the tag <tr>, representing a row of data
    countryDataSet = tables[0].find_all('tr', style_="")

    #Table to be created in desease_data.csv
    with open('desease_data.csv', 'w', encoding='utf8', newline='') as f:
        thewriter = csv.writer(f)
        header = ['id', 'country', 'total_cases', 'total_deaths', 'total_recovered', 'active_cases']
        thewriter.writerow(header)
        for country in countryDataSet:
            # Identifies Placement of row within table using find
            placementUnstripped = str(country.find('td', {"style": "font-size:12px;color: grey;text-align:center;vertical-align:middle;"}))
            placement = stripHtmlBrackets(placementUnstripped)
            # If a line with in <td><\td> does not have a placement, it can be classified as not a country, and is therefore skipped
            print(country)
            if placement not in ['0', 'None']:
                row = []
                for line in country:
                    line = str(line)
                    rowItem = stripHtmlBrackets(line)
                    if rowItem == 'N/A':
                        rowItem = '0'
                    #Identifies whether item whithin the row is what we are looking for,
                    #checking whether the data contains any symbols other than digits and commas
                    if rowItem not in ['None', '\n', '']:
                        if rowItem[0] not in ['+', '-']:
                            if rowItem == ' ':
                                rowItem = '0'
                            if len(row) == 1:
                                rowItem = AddQuotationMarks(rowItem)
                            row.append(rowItem)
                            if len(row) == 6:
                                print(row)
                                thewriter.writerow(row)

    connection = sqlite3.connect("sqlite.db")
    #cursor is an object that is used by python to interpret and executing sql queries
    cursor = connection.cursor()
    cursor.execute("DELETE FROM covid_statistics;")
    connection.commit()

    #Loop goes through every row in desease_data.csv and the sqlite query replaces each row in the covid_statistics table with new data
    skipHeader = True
    with open("desease_data.csv", "r") as file:
        for row in file:
            if skipHeader == False:
                print(row)
                cursor.execute("INSERT OR REPLACE INTO covid_statistics(id, country, total_cases, total_deaths, total_recovered, active_cases) VALUES (" + row + ");")
                connection.commit()
            skipHeader = False
    #world_map_geo is an open source json file that will produce a detailed vector world map, in which each country is associated with its name.
    countries = json.load(open('world_map_geo.json', 'r'))

    #Pandas is able to read SQL, CSV and JSON files and compile the data into a dictionary understandable to python
    df = pandas.read_sql_query("SELECT * from covid_statistics", connection)
    df = df[['country', 'total_cases', 'total_deaths', 'total_recovered', 'active_cases']]
    df['country'] = df['country'].str.strip('"')

    df = df.groupby('country').sum()
    df = df.reset_index(drop=False)
    df_temp = df.set_index('country')

    missing_countries = []
    mappable_countries = []

    #For every country in the JSON file, program will attempt to find data for it within the covid_statistics table
    #If country is found, mappable_countries is appended with the given countries name and geometry
    for country in countries['features']:
        mappable = False

        country_name_json = country['properties']['name']
        abrev_name_json = country['properties']['abbrev']
        geounit_name_json = country['properties']['geounit']

        if country_name_json in df_temp.index:
            mappable = True

        elif abrev_name_json in df_temp.index:
            mappable = True
            country_name_json = abrev_name_json

        elif geounit_name_json in df_temp.index:
            mappable = True
            country_name_json = geounit_name_json
        else:
            missing_countries.append(country_name_json)

        if mappable == True:
        #Each item in mappable_countries dictionary contains type, the data used to produce a vector image
        #of the country and a unique id, which is country name.
            geo = country['geometry']
            mappable_countries.append({
                'type': 'feature',
                'geometry': geo,
                'id': country_name_json
            })
    #Dictionary representing all the countries that the covid_statistics table has data on
    geo_world = {'type': 'FeatureCollection', 'features': mappable_countries}

    #As the values being handled are very large, in order to produce a clear range of values for measuring and
    #comparing data on the graph, log10 is applied to each value.
    df['choropleth_colour'] = df['total_cases'].apply(math.log10)
    maximum = df['choropleth_colour'].max()
    maxcolour = int(maximum) + 1

    #Calculates the scale to be shown on the sidebar
    values = [i for i in range(maxcolour)]
    ticks = [10 ** i for i in values]

    #Using plotly to create a choropleth map, using each country and assigning it its colour, with hover data being all
    #the other data extracted from the website
    fig = px.choropleth(df, geojson=geo_world, locations='country', color=df['choropleth_colour'],
                        range_color=(0, maximum), labels={'TotalCases': 'Total Cases'},
                        hover_data=["total_cases", "total_deaths", "total_recovered", "active_cases"])
    fig.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        #Colour bar indicates what colour represents what number
        coloraxis_colorbar={
            'title': 'Total Cases',
            'tickvals': values,
            'ticktext': ticks
        })

    #Adjusting size and layout of graph
    fig.update_layout(height=300, margin={"r": 0, "t": 0, "l": 0, "b": 0})

    fig.update_geos(visible=False, resolution=110, showcountries=True, countrycolor="Black")

    #Assigning graph to a variable so it can be passed as context, and inserted into HTML template
    #Allows the graph to be update every time the page is refreshed and values are changed
    plot_div = plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')

    #
    return render(request, "front/about.html", context={ "plot_div": plot_div})

def view_table(request):
    #Returns data values as a simple table
    d = []
    csv_file = pandas.read_csv("desease_data.csv")
    print(csv_file)
    csv_file.columns = ['placement', 'country', 'total_cases', 'total_deaths', 'total_recovered', 'active_cases']
    csv_file['country'] = csv_file['country'].str.strip('"')
    for i in range(len(csv_file)):
        line = csv_file.iloc[i]
        d.append(dict(line))
    context = {
        'table': d
    }
    return render(request, 'front/rawData.html', context)

def local_map(request):
    #Local map will be using data from the usersymptoms table in the database in order to display
    #another choropleth map

    connection = sqlite3.connect("sqlite.db")
    cursor = connection.cursor()
    df = pandas.read_sql_query("SELECT * from front_usersymptoms", connection)
    df = df.reset_index()
    recorded_users = []
    cursor.execute("DELETE FROM front_user_covid_record;")
    connection.commit()
    #Iterrows allows each pandas dataframe row to be iterated over and row is all items in the current row
    #Checks every symptom in usersymptoms to see if it matches the criteria for user likely to have been infected
    for index, row in df.iterrows():
        chance_of_infection = 0
        if float(row['temperature']) > 37.8:
            chance_of_infection += 1
        if row['continuous_cough'] == True:
            chance_of_infection += 1
        if row['loss_of_senses'] == True:
            chance_of_infection += 1
        #If symptoms show signs of covid, symptom is added to user_covid_record using cursor
        if row['infected_contact'] == True or chance_of_infection >= 2:
            user_id = row['user_id_id']
            if user_id not in recorded_users:
                user_id = "'"+str(user_id)+"'"
                date = "'"+str(row["date_set"])+"'"
                postcode = "'"+row["postcode"]+"'"
                recorded_users.append(user_id)
                record = str(user_id), str(date), str(postcode)
                #cursor.execute("INSERT INTO front_user_covid_record(user_id, covid_record_date_id, covid_record_postcode_id) SELECT user_id_id, date_set, postcode  FROM front_usersymptoms WHERE user_id_id=('" + str(user_id) +"');")
                cursor.execute("INSERT INTO front_user_covid_record(user_id, covid_record_date_id, covid_record_postcode_id) VALUES ({}, {},{});".format(str(user_id), str(date), str(postcode)))
                connection.commit()
    cases_per_county = []
    dff = pandas.read_sql_query("SELECT * FROM front_user_covid_record;", connection)
    print(dff)
    mappable_counties = []
    counties = json.load(open('london_postcode_geo.json', 'r'))
    county_index = 0

    #Using the same design for the world choropleth map, the program will iterate over every county
    #In the london_postcode json file and recognises which postcodes have values, and the rest are assigned 0
    for county in counties['features']:
        county_index += 1
        county_name = county['properties']['Name']
        num_of_cases = 0
        infected_county = False
        geo = county['geometry']

        mappable_counties.append({
            'type': 'feature',
            'geometry': geo,
            'id': county_index
        })

        #For each record of covid with a matching county name to london_postcode_geo.json, a count is created
        #Which will be used to produce a choropleth colour scale
        for index, row in dff.iterrows():
            if county_name == row['covid_record_postcode_id']:
                infected_county = True
                num_of_cases +=1
        #cases_per_county dictionary is appended with county name, the number of cases and its index
        if infected_county == True:
            cases_per_county.append({
                'county': county_name,
                'cases': num_of_cases,
                'id': county_index
            })

        else:
            cases_per_county.append({
                'county': county_name,
                'cases': 0,
                'id': county_index
            })
    geo_london = {'type': 'FeatureCollection', 'features': mappable_counties}

    print(cases_per_county)

    #Data is not scaled down as my program does not expect millions of user at the current time
    df = pandas.DataFrame(cases_per_county)
    maximum = df['cases'].max()
    maxcolour = int(maximum) + 1

    values = [i for i in range(maxcolour)]
    ticks = [i for i in values]

    fig = px.choropleth(df, geojson=geo_london, locations='id', color=df['cases'],scope='europe',
                        range_color=(0, maximum), labels={'cases': 'Total Cases'}, hover_data=['county'])

    #Places the scope of the default view of the map to view only where there is data collected
    fig.update_geos(fitbounds="locations")

    fig.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        coloraxis_colorbar={
            'title': 'Total Cases',
            'tickvals': values,
            'ticktext': ticks
        })

    fig.update_layout(height=300, margin={"r": 0, "t": 0, "l": 0, "b": 0})

    plot_div = plot(fig, output_type='div', include_plotlyjs=False, show_link=False, link_text='')

    return render(request, 'front/local_map.html', context={ "plot_div": plot_div})









