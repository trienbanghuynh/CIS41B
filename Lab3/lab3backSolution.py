import requests
import json
import sqlite3
from bs4 import BeautifulSoup

# PART A - Web Scrapping

root = 'https://guide.michelin.com'
#link = https://guide.michelin.com/us/en/california/san-jose/restaurants
link = 'https://guide.michelin.com/us/en/california/cupertino/restaurants'
restList = [] # This is a list of dict where each dict represents a resto
                # [{'name': xxx, 'url':xxx, 'loc': xxx, 'addr': xxx,'cost': xxx, 'cuisine':xxx}]

while True:
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'lxml')

    for elem in soup.select('.card__menu-content.js-match-height-content'): # This class is contained in the div tag of all restoraunt boxes

        data = {}
        data['url'] = root + elem.select_one('a')['href'] # There is only one a tag within this div tag
        data['name'] = elem.select_one('.card__menu-content--title.pl-text.pl-big').text.encode('utf-8', 'ignore').decode('utf-8').strip() # When you call .text on a BeautifulSoup tag object, 
                                                                                                                                           # it returns the text within that tag, 
                                                                                                                                           # including the text within all its descendant tags.
                                                                                                                                           # This prints the text of the a tag within the h tag

        data['loc'] = elem.select_one('.card__menu-footer--location.flex-fill.pl-text').text.strip().split(',')[0] # City like Los Gatos, San Jose
        
        last = elem.select_one('.card__menu-footer--price.pl-text').text.strip().split()
        
        data['cost'] = last[0]      # $$$ for example
        data['cuisine'] = last[-1]  # Chinese for example

        page = requests.get(data['url']) # page is now linked to the restaurant's home page
        inner = BeautifulSoup(page.content, 'lxml')

        addr = inner.select_one('.restaurant-details__heading--address').text.strip().split(',')[:-2] # list [street address, city]
        data['addr'] = ','.join(addr) # street name, city
        restList.append(data)

    nextPage = soup.select_one('.btn-carousel.hide-not-dekstop.js-restaurant__pagination.pl-text.pl-big')

    nextlink = nextPage.select_one('a')['href'] # e.g. /us/en/california/cupertino/restaurants
                                                # Notice it is relative, not absolute
                                                # If you just do inspect, you won't know this. You have to view page source

    if not '/page' in nextlink: # if this is true, we have reached the last page after scraping the page
        break              

    link = root + nextlink # must append base to relative url

with open('rest.json', 'w') as f:
    json.dump(restList, f, indent = 3)
print(len(restList))
print('done')


# Part B - Database creation

conn = sqlite3.connect('rest.db')
cur = conn.cursor()

# create Loc table with id (filled in by databse)
# and locations as text strings that are unique
# These will be the unique city names e.g Los Gatos, San Jose, Cupertino
cur.execute('DROP TABLE IF EXISTS Loc')
cur.execute('''CREATE TABLE Loc (
            id INTEGER NOT NULL PRIMARY KEY UNIQUE, 
            loc TEXT UNIQUE ON CONFLICT IGNORE)''')

# create Cost table with id (filled in by database)
# and cost as text strings that are unique
# stores $, $$, $$$, $$$$
cur.execute('''DROP TABLE IF EXISTS Cost''')
cur.execute('''
            CREATE TABLE Cost (
            id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            cost TEXT UNIQUE ON CONFLICT IGNORE)''')

# create Cuisine table with id (filled in by database)
# and cusine as text strings that are unique
cur.execute('''DROP TABLE IF EXISTS Cuisine''')
cur.execute('''
            CREATE TABLE Cuisine (
            id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            cuisine TEXT UNIQUE ON CONFLICT IGNORE)''')

# create Rest table with name, url, loc, cost, cuisine, addr
# loc, cost, cuisine are int because each is forign key into their table
cur.execute('DROP TABLE IF EXISTS Rest')
cur.execute('''CREATE Table Rest (
            name TEXT NOT NULL UNIQUE,
            url TEXT,
            loc INT,
            cost INT,
            cuisine INT,
            addr TEXT)''')

# loc, cost, kind are int because each is foreign key into their table

for rest in restList:
    # insert loc into Loc table, then fetch if to serve as foreign key
    cur.execute('INSERT INTO Loc (loc) VALUES (?)', (rest['loc'],))
    cur.execute('SELECT id FROM Loc WHERE loc = ?', (rest['loc'],))
    locID = cur.fetchone()[0]

    # insert cost into Cost table, then fetch id to serve as foreign key
    cur.execute('INSERT INTO cost (cost) VALUES (?)', (rest['cost'],))
    cur.execute('SELECT id FROM Cost WHERE cost = ?', (rest['cost'],))
    costID = cur.fetchone()[0]

    # insert cuisine into Cuisine table, then fetch id to serve as foreign key
    cur.execute('INSERT INTO Cuisine (cuisine) VALUES (?)', (rest['cuisine'],))
    cur.execute('SELECT id FROM Cuisine WHERE Cuisine = ?', (rest['cuisine'],))
    kindID = cur.fetchone()[0]

    # prepare data (a list) to be inserted into Rest table
    data = [rest['name'], rest['url'], locID, costID, kindID, rest['addr']]
    # create list of 6 ? for 
    cur.execute('INSERT INTO Rest VALUES (?, ?, ?, ?, ?, ?)', data)

conn.commit()
conn.close()
print("done")

