# Lab 0: Review CIS 41A
# Name: Trien Bang Huynh

import csv
import os

FILE_NAME = "cities.csv"
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILE_NAME)

class Cities :
    """
    A class representing a collection of cities and their population.
    """
    def __init__(self):
        self._cities = {}
        try:
            with open(FILE, 'r') as f:
                reader = csv.reader(f)
                for row in reader: 
                    city_name, *population = row
                    self._cities[city_name] = [*population]
        except IOError:
            raise SystemExit("Error opening cities.csv")

    def printYear(self, year): 
        '''
        Print out the population of each city in a given year
        '''
        print(f"Year {year}")
        try:
            year_index = (int(year) - 2000) // 10
            assert year_index in [0, 1, 2]
            for city, data in self._cities.items():
                print(f"{city:<20}{data[year_index]:>10}")
        except (ValueError, AssertionError):
            print(f"{year} is not a valid census year")
        print() 
        
        
        


    
    
C = Cities()
C.printYear(2020)
C.printYear(2000)
C.printYear(10) 
C.printYear('a')
