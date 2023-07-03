import tkinter as tk
import sqlite3
import webbrowser
import tkinter.messagebox as tkmb
'''
What the database looks like

Database: rest.db

Table: Loc
+----+---------+
| id |   loc   |
+----+---------+
|  1 | City A  |
|  2 | City B  |
| .. |   ...   |
+----+---------+

Table: Cost
+----+------+
| id | cost |
+----+------+
|  1 |  $   |
|  2 | $$   |
| .. | ...  |
+----+------+

Table: Cuisine
+----+---------+
| id | cuisine |
+----+---------+
|  1 | French  |
|  2 | Italian |
| .. |  ...    |
+----+---------+

Table: Rest
+----------------+--------------------------------------+-----+------+--------+------------------+
|      name      |                 url                  | loc | cost | cuisine|      addr        |
+----------------+--------------------------------------+-----+------+--------+------------------+
| Restaurant A   | https://guide.michelin.com/.../A     |  1  |  1   |   1    | 123 Main St, ... |
| Restaurant B   | https://guide.michelin.com/.../B     |  2  |  2   |   2    | 456 Market St,...|
|     ...        |                  ...                 | ... | ...  |  ...   |        ...       |
+----------------+--------------------------------------+-----+------+--------+------------------+
'''

class MainWin(tk.Tk):
    '''Main application window for the restaurant lookup application.
    
    This class is the primary interface for the restaurant lookup application.
    It allows users to search for restaurants by city or cuisine.

    Attributes:
        DB: Name of the SQLite database file.
    '''

    DB = 'rest.db'

    def __init__(self):
        super().__init__()
        self.title('Restaurants')
        self._conn = sqlite3.connect(self.DB) # This will never raise an error 
                                              # If rest.db does not exist, sql will make a new db
        self._cur = self._conn.cursor()
        self.protocol("WM_DELETE_WINDOW", self._close) # self._close does one additional step before closing MainWin which is closing the database


        #  --- Set up main window ---
        tk.Label(self, text='Local Michelin Guide Restaurants',
                 font=('Helvetica', 11), fg='blue').grid(padx=10, pady=10)
        tk.Label(self, text='Searchy by:', font=('Helvetica', 11)).grid(padx=10, pady=10)
        frame = tk.Frame(self)
        frame.grid()
        tk.Button(frame, text='City', fg='blue', font=('Helvetica', 11),
                  command=self._getCity).grid(padx=10, pady=10) 
        tk.Button(frame, text='Cuisine', fg='blue', font=('Helvetica', 11),
                  command=self._getCuisine).grid(row=0, column=3, padx=10, pady=10)
        # ------
    
    def _getCity(self):
        '''Fetches all restaurant cities from the database and prompts the user to select one.

        This method will result in a selection window being shown, populated with cities from the database.
        The user's choice is then used to display available restaurants in the chosen city.

        '''

        # get all restaurant cities
        try:
            self._cur.execute('SELECT loc From Loc') # SELECT operation on a table that doesn't exist will raise error
        except sqlite3.OperationalError:
            tkmb.showerror('Error', "Can't access " + self.DB, parent = self)
            raise SystemExit

        cities = list(zip(*self._cur.fetchall()))[0] # [(Los Gatos, Cupertino,...)][0] which is              
        ### Resulting Data Structure: cities = ('City A', 'City B', ...) ###

        choices = self._getChoice('a city', cities) # tuple containing the selected index in the city selection page e.g. (2,) or (4,)
        if len(choices) == 0:  # If no option was made in the city selection window,
                               # user stays in main window without the choice being processed
            return  
        else:
            choice = choices[0]  # selected index in the city selection page e.g. 2 or 4

        # get restaurant names in city 
        self._cur.execute('''SELECT Rest.name FROM Rest JOIN Loc
                             On Rest.Loc = Loc.id
                             WHERE Loc.loc=?''', (cities[choice],)) # cities[choice] is the selected city in dialog win 
        
        restoNames = list(zip(*self._cur.fetchall()))[0] # restaurants in the selected city
                                                         # e.g. restoNames = ('Le You', 'Pestiscos', ...) 
        choices = self._getChoice('a restaurant', restoNames, multiple = True)  # tuple containing the selected indicie(s) in restaurant selection page
                                                                                # e.g. choices = (1, 5) or (3, 4, 5)

        if len(choices) == 0 : # If no option was made in the restaurant selection window,
                               # user stays in main window without the choice being processed
            return 
        # Show restaurant names in city 
        self._launchChoices(restoNames, choices) # process choice by showing display wins
                                                 # restoNames = ('Le You', 'Pestiscos', ...) 
                                                 # choices = (1, 5)

    def _getCuisine(self):
        '''Fetches all cuisines from the database and prompts the user to select one.

        This method will result in a selection window being shown, populated with cuisines from the database.
        The user's choice is then used to display available restaurants offering the chosen cuisine.
        '''

        # get cuisine of food
        try:
            self._cur.execute('''SELECT cuisine from Cuisine''') # SELECT operation on a table that doesn't exist will raise error
        except sqlite3.OperationalError:
            tkmb.showerror('Error', "can't access " + self.DB, parent = self)
            raise SystemExit
        
        cuisines = list(zip(*self._cur.fetchall()))[0] # [('Chinese', 'Japanese', ...)] which is
                                                       # ('Chinese', 'Japanese', ...)

        choices = self._getChoice('a cuisine', cuisines)  # tuple containing the selected index in the cuisine selection page e.g. (2,) or (4,)
        if len(choices) == 0:
            return
        else:
            choice = choices[0] # selected index in the cuisine selection page e.g. 2 or 4
        
        # get restaurant names selected cuisine 
        self._cur.execute('''Select Rest.name FROM Rest JOIN Cuisine
                             ON Rest.cuisine  = Cuisine.id
                             WHERE Cuisine.cuisine = ?''', (cuisines[choice], )) # cuisines[choice] is the selected cuisine in dialog win 

        restoNames = list(zip(*self._cur.fetchall()))[0] # restaurants with the selected cuisine
                                                         # e.g. restoNames = ('Beijing Duck House', 'General Tso's', ...) 

        choices = self._getChoice('a restaurant', restoNames, multiple = True) # tuple containing the selected indicie(s) in restaurant selection page
                                                                                # e.g. choices = (1, 5) or (3, 4, 5)
        if len(choices) == 0: 
            return
        # Show restaurant names with selected cuisine
        self._launchChoices(restoNames, choices) # process choice by showing display wins
                                                 # restoNames = ('Beijing Duck House', 'General Tso's', ...) 
                                                 # choices = (1, 5)

    def _getChoice(self, option, data, multiple=False):
        '''Displays a dialog window with restaurants for the user to choose from and returns the user's choices.

        Parameters:
            option (str): The type of options the user is choosing from (e.g either 'a city', 'a cuisine', 'a restaurant').
            data (list): List of options for the user to choose from. (e.g. ('Cupertino', 'Los Gatos', ...), ('Chinese', 'Japanese', ...), ('Le You', 'Pestiscos', ...) )
            multiple (bool): Whether the user can select multiple options. Defaults to False. (only true when displaying restaurants selection window)


        Returns:
            list: A list of the user's chosen options. Each item in the list is an index
                  into the 'data' list parameter.
        '''

        dwin = DialogWin(self, option, data, multiple)
        self.wait_window(dwin) # Main Win waits for dialog win
        choices = dwin.getChoice() # tuple of selected indicie(s) in either city selection page or restaurant selection page

        # Resulting Data Structure: choices = (3,) or (0, 2, 3) #

        return choices
    
    def _launchChoices(self, restoNames, choices): 
        '''Fetches and displays restaurant information based on the user's choices.
        
        Parameters:
            restoNames (list): restaurants in the selected city or cuisine. E.g (Le You, Pestico)
            choices (list): List of user-selected indices from the restoNames list. Each index
                            corresponds to a restaurant in the 'restoNames' list.
        
        This method fetches the details of the chosen restaurants and displays them in a new window.
        '''
        

        for choice in choices: # choice is a selected index which corresponds to a selected restaurant in either city or cuisine selection window
            restoName = restoNames[choice] # A single selected restaurant in either city or cuisine selection window
            self._cur.execute('''SELECT Rest.name, Rest.url, Cost.cost, Cuisine.cuisine, Rest.addr
                                FROM Rest JOIN Cuisine JOIN Cost
                                ON Cuisine.id = Rest.cuisine
                                AND Cost.id = Rest.cost
                                AND Rest.name = ?''', (restoName, ))
            
            name, url, dollar, cuisine, addr = self._cur.fetchall()[0]
            DisplayWin(self, name, url, dollar, cuisine, addr)

    def _close(self):
        self._conn.close()
        self.quit()


class DialogWin(tk.Toplevel):
    '''Dialog window for the restaurant lookup application.

    This class represents a dialog window that displays a listbox of choices
    and gets the user's choice(s).

    Attributes:
        master (tkinter.Tk): The parent window.
        instr (str): Instructions for the user (e.g. 'a city', 'a cuisine', 'a restaurant').
        data (list): List of options for the user to choose from (e.g. ('Cupertino' or 'Los Gatos', ...), ('Chinese' or'Japanese', ...), (Le You, Pasticos))
        multiple (bool): Whether the user can select multiple options. Defaults to False.
    '''
    
    def __init__(self, master, instr, data, multiple = False):
        '''Initializes a new instance of the DialogWin class.

        Parameters:
            master (tkinter.Tk): The parent window. 
            instr (str): Instructions for the user. (e.g. 'city', 'cuisine')
            data (list): List of options for the user to choose from. (e.g. ('Cupertino', 'Los Gatos', ...), ('Chinese', 'Japanese', ...),)
            multiple (bool): Whether the user can select multiple options. Defaults to False.
        '''

        super().__init__(master)
                                        
        tk.Label(self, text = 'Click on ' + instr + ' to select').grid() # instr is either city or cuisine
        self._S = tk.Scrollbar(self)
        if multiple: # if Multiple = False, you are in the city/cuisine selection window 
                     # if Multiple = True,  you are on the restaurant selection window
            self._LB = tk.Listbox(self, height=6, width=30, selectmode='multiple', yscrollcommand=self._S.set) 
        else:
            self._LB = tk.Listbox(self, height=6, width=30, yscrollcommand=self._S.set)
        self._S.config(command=self._LB.yview)
        self._LB.grid()
        self._S.grid(row=1, column=1, sticky='ns')
        self._LB.insert(tk.END, *data) # Populate dialog window with ('Cupertino', 'Los Gatos', ...), ('Chinese', 'Japanese', ...)
        tk.Button(self, text='Click to select', command=self._setChoice).grid(pady=20) # set self._choice (defined below) to selected list box indicies

        self._choice = -1 # initialize self._choice with something random
        self.protocol('WM_DELETE_WINDOW', self._close)
        self.focus_set()
        self.grab_set()
        self.transient(master)
    
    def _setChoice(self):
        '''Fetches the user's choices from the listbox and stores them before destroying the window.

        This method is bound to the "Click to select" button and is called when the button is pressed.
        The choices are stored as indices into the 'data' list provided during initialization.

        '''
        self._choice = self._LB.curselection() # e.g. self._chocies = (3,) or self._choice = (0, 2, 4) 

        # A single index means one item was selected, which happens when choosing a city or cuisine. 
        # Multiple indices imply multiple selections, which happens when selecting restaurants.
        
        self.destroy()
    
    def getChoice(self):
        '''Returns the user's choices from the listbox.
        
        Returns:
            list: A list of the user's chosen options. Each item in the list is an index
                  into the 'data' list provided during initialization.
        '''
        return self._choice # e.g. self._chocies = (3,) or self._choice = (0, 2, 4) or self._choice = ()
    
    def _close(self): 
        self._choice = () # No selection made because user closed dialog window without making selection
        self.destroy()  

class DisplayWin(tk.Toplevel):
    '''Display window for the restaurant lookup application.

    This class represents a display window that shows the details of a selected restaurant.

    Attributes:
        master (tkinter.Tk): The parent window.
        data (tuple): Tuple containing the name, url, cost, cuisine, and address of the restaurant.
    '''

    def __init__(self, master, *data):
        '''Initializes a new instance of the DisplayWin class.

        Parameters:
            master (tkinter.Tk): The parent window.
            data (tuple): Tuple containing the name, url, cost, cuisine, and address of the restaurant.
        '''

        super().__init__(master)
        self._data = data
        
        F = tk.Frame(self)
        F.grid(padx = 10, pady = 20)
        tk.Label(F, text=self._data[0], font=('Helvetica', 11), fg='blue').grid()
        tk.Label(F, text=self._data[4], font=('Helvetica', 11)).grid()
        tk.Label(F, text='Cost: ' + self._data[2], font=('Helvetica, 11')).grid()
        tk.Label(F, text = 'Cuisine: ' + self._data[3], font = ('Helvetica', 11), fg ='blue').grid()
        tk.Button(F, text = "Visit Webpage", fg = 'blue', font = ('Helvetica', 11),
                 command = lambda : webbrowser.open(self._data[1])).grid(padx=10, pady=10)
app = MainWin()
app.mainloop()
