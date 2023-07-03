import requests
import json
import tkinter as tk
import threading
import time
import tkinter.messagebox as tkmb
import os
import queue
import collections

class Parks(tk.Tk):
    STATEFILE = 'states_hash.json'
    MAXCHOICE = 5

    def __init__(self):
        super().__init__()
        self.title('US NPS')

        with open(self.STATEFILE) as fh:
            data = json.load(fh) # {State Abbreviation : State}}
        
        self._stateDic = dict(zip(data.values(), data.keys())) # Reverse to {State: State Abbreviation}
        states = tuple(data.values()) # tuple (State name)
        self._D = {} # Dictionary to store the data

        self._start = True # Identify the start wwindow

        tk.Label(self, text = 'National Park Finder', font = ('Calibri', 14, 'bold')).grid(pady = 2)

        self._prompt = tk.StringVar()
        self._prompt.set('Select up to' + str(self.MAXCHOICE) + ' states')
        tk.Label(self, textvariable=self._prompt).grid(pady = 2)

        self._F = tk.Frame(self, width=40)
        self._F.grid(padx=10)
        self._S = tk.Scrollbar(self._F)
        self._LB = tk.Listbox(self._F, height=10, width=50, yscrollcommand=self._S.set, selectmode='multiple')
        self._S.config(command=self._LB.yview)
        self._LB.grid()
        self._S.grid(row=0, column=1, sticky='ns')
        self._LB.insert(tk.END, *states)

        self._buttonText = tk.StringVar()
        self._buttonText.set('Submit Choice')
        tk.Button(self, textvariable=self._buttonText, command = lambda: self._processChoice(self._start)).grid(pady = 5)
        self._result = tk.StringVar()
        self._result.set('')
        tk.Label(self, textvariable=self._result).grid(pady=2)

    def _processChoice(self, start):
        choice = self._LB.curselection()
        if start == True: # If we are on the start window
            self._getData(choice)
        else: # If the screen has been reconfigured
            self.writeFile(choice)

    def _getData(self, choice):
        if not (1 <= len(choice) <= self.MAXCHOICE): # Show error if the user selected to many or to few states
            tkmb.showerror('Error', 'Select 1 to ' + str(self.MAXCHOICE) + ' states', parent = self)
            return
    
        states = self._LB.get(0, tk.END) # returns a tuple of selected states

        q = queue.Queue()
        self._result.set('Results:')
        tList = []

        for i in choice:
            t = threading.Thread(target = self._getStateData, args = (states[i], q)) # pass in the queue to the API retriever
            tList.append(t)
        
        start = time.time()

        for t in tList:
            t.start()
        for t in tList:
            s = q.get()
            self._result.set(self._result.get() + s)  
            self.update()

        """
        start=time.time()  # single thread
        for i in choice:
            self.getStateData(self.states[i], self._q)
        """

        print(f'{time.time() - start:.2f}')
        self._start = False
        self._displayState()

    def _getStateData(self, name, q):
        statecode = self._stateDic[name].lower()
        requestStr = f'https://developer.nps.gov/api/v1/parks?stateCode=api_key= ...'
        page = requests.get(requestStr)
        data = page.json()
        q.put(name + ': ' + str(data['total'] + ' '))
        # print(name + ': ' + str(data['total'])) # single thread print total
        self._D[name] = data

    
    def _displayState(self):
        L = [state + ': ' + park['name'] for state in self._D for park in self._D[state]['data']]
        self._prompt.set('Select parks to save park info to file')
        self._LB.delete(0, tk.END)
        self._LB.insert(tk.END, *L)
        self._buttonText.set('Save')

    def _writeFile(self, choice):
        if len(choice) < 1:
            tkmb.showinfo('Notification', 'No park selected, no file saved', parent = self)
            self._LB.selection_clear(0, tk.END)
            return
        
        path = tk.filedialog.askdirectory(initialdir=os.getcwd(), parent = self)
        if not path:
            self._LB.selection_clear(0, tk.END)
            return

        gen = (record for state in self._D for record in self._D[state]['data'])

        L = self._LB.get(0, tk.END)
        D = collections.defaultdict(list)
        for num in choice:
            stateName, parkName = [name.strip() for name in L[num].split(':')]
            record = next(gen)
            while record['name'] != parkName:
                record = next(gen)
            d = {parkName:{}}
            d[parkName]['full name'] = record['fullName']
            d[parkName]['description'] = record['description']
            d[parkName]['activities'] = ', '.join([elem['name'] for elem in record['activities']])
            d[parkName]['url'] = record['url']
            D[stateName].append(d)

        os.chdir(path)
        states = []
        for state in D:
            states.append(state+'.json')
            with open(state + '.json') as fh:
                json.dump(D[state], fh, indent=3)
        tkmb.showinfo('Saved', 'Saved files: ' + ', '.join(states), parent = self)
        self.destroy()
        self.quit()

if __name__ == "__main__":
    app = Parks().mainloop()