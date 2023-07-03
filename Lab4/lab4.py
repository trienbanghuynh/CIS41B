import urllib.request
import json
import os
import tkinter as tk
import tkinter.messagebox as tkmb
import sys
from collections import defaultdict
import time
import tkinter.filedialog
import threading
import queue
from dotenv import load_dotenv


# You can ignore two lines of below code if you don't store your API in .env file. Instead you will replace myAPIkey and hardcode with your API key.

load_dotenv()
myAPIkey = os.getenv("API_KEY")

# API key is a secret, you will need to replace with your API key here to fetch data
HEADERS = {"X-Api-Key": f"{myAPIkey}"}


class MainWin(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("US NPS")
        self._stateSelection = []
        self._dataAPI = []

        with open("states_hash.json", 'r') as fh:
            self._states_dic = json.load(fh)

        tk.Label(self, text="National Park Finder", fg="green", font=(
            'Times', 17)).grid(row=0, column=0, columnspan=3, pady=10, padx=10)

        self.L1 = tk.Label(self, text="Select up to 5 states",
                           fg="black", font=('Times', 15))
        self.L1.grid(row=1, column=0, columnspan=3, pady=10)

        # Listbox and Scrollbar
        self.listbox = tk.Listbox(
            self, width=50, height=10, selectmode="multiple")
        self.scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)

        # populate the listbox with US's states
        for state in self._states_dic.values():
            self.listbox.insert(tk.END, state)

        self.listbox.grid(row=2, column=0, ipadx=5,
                          padx=20, pady=20, sticky="nsew")
        self.scrollbar.grid(row=2, column=1, sticky="ns")

        # make selection limit up to 5
        def limit_selection(event):
            if len(self.listbox.curselection()) > 5:
                self.listbox.selection_clear(self.listbox.curselection()[0])

        self.listbox.bind("<<ListboxSelect>>", limit_selection)

        # Select button
        self.B = tk.Button(self, text="Submit choice", font=(
            'Times', 15), command=self.onClicked)
        self.B.grid(row=3, column=0, columnspan=2, padx=20, pady=20)

        # status label
        self.L2 = tk.Label(self, text="", font=('Times', 15))
        self.L2 .grid(row=4, column=0, columnspan=3, pady=10, padx=10)

    def onClicked(self):

        if len(self.listbox.curselection()) == 0:
            tkmb.showerror("Error", "Please select at least 1 state")
            return
        else:
            for index in self.listbox.curselection():
                code, name = list(self._states_dic.items())[index]
                self._stateSelection.append((code, name))
            self.parksFinder()

    def parksFinder(self):

        self.L1['text'] = "Select parks to save parks info to file"
        self.B['text'], self.B['command'] = "Save", self.saveFile
        self.L2['text'] = f"Fetching data for {len(self._stateSelection)} state(s)"
        self.listbox.unbind("<<ListboxSelect>>")
        self.listbox.delete(0, tk.END)

        timeRecord = 0

        for choice in self._stateSelection:
            # an ex of choice = "AL": "Alabama"
            code, name = choice

            # Configure API request
            endpoint = f'https://developer.nps.gov/api/v1/parks?stateCode={code}'

            # start recording fetching time
            start = time.time()

            # Make API request and get response
            req = urllib.request.Request(endpoint, headers=HEADERS)
            response = urllib.request.urlopen(req)

            timeRecord += time.time() - start

            # Parse JSON data from response
            data = json.loads(response.read().decode())

            # append to dataAPI list
            self._dataAPI.append(data)

            for park in data['data']:
                tempStr = name + ": " + park['name']
                self.listbox.insert(tk.END, tempStr)

        print(f"Time of fetching data from API in serial: {timeRecord:.2f}s")

    def saveFile(self):

        if len(self.listbox.curselection()) == 0:
            tkmb.showerror("Error", "Please select at least 1 park")
            return

        # each key (statename) will have list of selected parks
        selectedParksWithStates = defaultdict(list)

        for i in self.listbox.curselection():
            stateAndPark = self.listbox.get(i)
            stateName = stateAndPark.split(":")[0].strip()
            parkName = stateAndPark.split(":")[1].strip()
            selectedParksWithStates[stateName].append(parkName)

        # print(selectedParksWithStates)

        # open current directory

        directory = tk.filedialog.askdirectory(initialdir='.')

        filesSave = []
        index = 0
        # if user choose a directory
        if directory:
            for stateName, listOfParks in selectedParksWithStates.items():
                listToSave = []
                for park in listOfParks:
                    parkDictForFile = {}
                    tempDict = {}
                    # loop through each parks in selected states to find the parks chosen from the listbox
                    for parkDict in self._dataAPI[index]['data']:
                        if parkDict['name'] == park:
                            tempDict['full name'] = parkDict['fullName']
                            tempDict['description'] = parkDict['description']
                            tempAcList = []
                            for act in parkDict['activities']:
                                tempAcList.append(act['name'])
                            tempDict['activities'] = ", ".join(tempAcList)
                            tempDict['url'] = parkDict['url']

                            break

                    parkDictForFile[park] = tempDict
                    listToSave.append(parkDictForFile)

                # saving file in selected directory
                filename = stateName + ".json"
                pathToSaveFile = directory + "/" + filename
                filesSave.append(filename)

                with open(pathToSaveFile, 'w') as fh:
                    json.dump(listToSave, fh, indent=3)

                index += 1

            # create a confirm messagebox
            filesSaveStr = ", ".join(filesSave)

            confirmed = tkmb.askyesno(
                "Confirmation", f"Save files: {filesSaveStr}")
            if confirmed:
                self.closeWin()

        else:
            self.listbox.selection_clear(0, tk.END)

    def closeWin(self):
        self.destroy()
        self.quit()


app = MainWin()
app.mainloop()
