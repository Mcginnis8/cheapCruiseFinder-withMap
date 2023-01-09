import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import customtkinter
from tkintermapview import TkinterMapView
import webbrowser

monthArr = ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06', '2023-07', '2023-08', '2023-09',
            '2023-10', '2023-11', '2023-12', '2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06',
            '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12', '2025-01']
Arr = []
global df


# URL of the website you want to scrape
def scrape_cruise(month, tupleArr):
    tempArrTuples = []
    url = "https://www.cruisewatch.com/find/cruise?sort=price&search_months%5B%5D=" + str(month)

    # Send a GET request to the website and store the response
    response = requests.get(url)

    # Parse the HTML content of the website
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all the elements on the page with the class "price"
    tempPrices = soup.find_all(class_="card-body")

    for i in tempPrices:
        a_tag = i.select_one('a[href]')
        shipLink = a_tag['href']
        rateTemp = i.find(class_="badge badge-primary")
        dateTemp = i.find_all("p")[2].text[0:38].replace("\xa0", "").replace("SAIL DATE: ", "")
        date_regex = r"(\w+) (\d+), (\d+) - (\w+) (\d+)"
        dateTemp = re.sub(date_regex, r"\1 \2-\4 \5, \3", dateTemp)

        if rateTemp:
            rateTemp = rateTemp.text
        else:
            rateTemp = 'None'
        tempTuple = (i.find(class_="cost").text.replace("$", "").replace("/night", ""), i.find(class_="price").text,
                     i.find_all("p")[1].text, dateTemp, rateTemp, shipLink,
                     i.find(class_="search-result tour-name").text)
        tempArrTuples.append(tempTuple)
    tupleArr += tempArrTuples
    # Sort the tuples by the first element
    return tupleArr


def first(myArr):
    for i in range(len(monthArr)):
        myArr = scrape_cruise(monthArr[i], myArr)
    df = pd.DataFrame(myArr, columns=['CPD', 'Price', 'Location', 'Dates', 'Rating', 'shipURL', 'shipName'])
    df = df.drop_duplicates(subset=["Location", "Dates"], keep='first')
    df = df.sort_values(by='CPD')
    return df


customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):
    APP_NAME = "Cruise Price Tracker"
    WIDTH = 1000
    HEIGHT = 780

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)
        self.destNum = 0
        self.marker_list = []
        self.poly_list = []

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_right = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============

        self.frame_left.grid_rowconfigure(3, weight=1)

        self.button_next = customtkinter.CTkButton(master=self.frame_left,
                                                   text="Next Destination",
                                                   command=self.next_marker_event)
        self.button_next.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_prev = customtkinter.CTkButton(master=self.frame_left,
                                                   text="Previous Destination",
                                                   command=self.prev_marker_event)
        self.button_prev.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.cruiseName = customtkinter.CTkLabel(master=self.frame_left, corner_radius=6,
                                                 text="Click Next Destination",
                                                 height=100,
                                                 fg_color=["gray90", "gray13"])
        self.cruiseName.grid(pady=(20, 0), padx=(20, 20), row=2, column=0)

        self.button_prev = customtkinter.CTkButton(master=self.frame_left,
                                                   text="Listing",
                                                   command=self.listing_url_event)
        self.button_prev.grid(pady=(20, 0), padx=(20, 20), row=3, column=0)

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Tile Server:", anchor="w")
        self.map_label.grid(row=4, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal",
                                                                                    "Google satellite"],
                                                           command=self.change_map)
        self.map_option_menu.grid(row=5, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=(20, 20), pady=(10, 20))

        # ============ frame_right ============

        self.frame_right.grid_rowconfigure(1, weight=1)
        self.frame_right.grid_rowconfigure(0, weight=0)
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_columnconfigure(1, weight=0)
        self.frame_right.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_right, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            placeholder_text="type address")

        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_5.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        # Set default values
        self.map_widget.set_zoom(5)
        self.map_widget.set_address("Atlanta")
        self.map_option_menu.set("OpenStreetMap")
        self.appearance_mode_optionemenu.set("Dark")
        customtkinter.set_appearance_mode("Dark")

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

    def next_marker_event(self):
        self.destNum += 1
        for poly in self.poly_list:
            poly.delete()
        for marker in self.marker_list:
            marker.delete()
        aa = df.at[self.destNum, 'shipName']
        b = df.at[self.destNum, 'Rating']
        c = df.at[self.destNum, 'CPD']
        d = df.at[self.destNum, 'Dates']
        e = df.at[self.destNum, 'Price']
        a = df.at[self.destNum, 'Location'].split(';')
        a = [s.strip() for s in a]
        tempStr = 'Price Ranking: ' + str(self.destNum)+ '\nTotal Price: '+ e+'\nCost Per Day: $' + c + '\nDates: ' + d + '\nCruise Ship: ' + aa + '\nRating: ' + b + '\nLocations:'
        for i in a:
            tempStr += '\n' + i
        self.cruiseName.configure(text=tempStr)
        tempBool = False
        x = len(a)
        if a[0] == a[len(a)-1]:
            tempBool = True
            x -= 1
        tempArr = []
        for j in range(x):
            tempMarker = self.map_widget.set_address(a[j], marker=True)
            if tempMarker:
                if tempBool and not j:
                        tempStr = str(j + 1) + '-' + str(len(a)) +'. '+ str(a[j])
                        tempMarker.set_text(tempStr)
                        self.marker_list.append(tempMarker)
                        tempArr.append(tempMarker.position)
                else:
                    tempStr = str(j+1) + '. '+ str(a[j])
                    tempMarker.set_text(tempStr)
                    self.marker_list.append(tempMarker)
                    tempArr.append(tempMarker.position)

        tempPoly = app.map_widget.set_polygon(tempArr, outline_color="red",
                                              border_width=12,
                                              name="switzerland_polygon")
        self.poly_list.append(tempPoly)
        self.map_widget.set_zoom(4)

    def prev_marker_event(self):
        for poly in self.poly_list:
            poly.delete()
        for marker in self.marker_list:
            marker.delete()
        self.destNum -= 1
        a = df.at[self.destNum, 'shipName']
        b = df.at[self.destNum, 'Rating']
        c = df.at[self.destNum, 'CPD']
        d = df.at[self.destNum, 'Dates']
        e = df.at[self.destNum, 'Price']
        tempStr = 'Price Ranking: ' + str(self.destNum + 1) + '\nTotal Price: '+ e+'\nCost Per Day: $' + c + '\nDates: ' + d + '\nCruise Ship: ' + a + '\nRating: ' + b
        self.cruiseName.configure(text=tempStr)
        a = df.at[self.destNum, 'Location'].split(';')
        a = [s.strip() for s in a]
        tempBool = False
        x = len(a)
        if a[0] == a[len(a)-1]:
            tempBool = True
            x -= 1
        tempArr = []
        for j in range(x):
            tempMarker = self.map_widget.set_address(a[j], marker=True)
            if tempMarker:
                if tempBool and not j:
                        tempStr = str(j + 1) + '-' + str(len(a)) +'. '+ str(a[j])
                        tempMarker.set_text(tempStr)
                        self.marker_list.append(tempMarker)
                        tempArr.append(tempMarker.position)
                else:
                    tempStr = str(j+1) + '. '+ str(a[j])
                    tempMarker.set_text(tempStr)
                    self.marker_list.append(tempMarker)
                    tempArr.append(tempMarker.position)
        tempPoly = app.map_widget.set_polygon(tempArr, outline_color="red",
                                              border_width=12,
                                              name="switzerland_polygon")
        self.poly_list.append(tempPoly)
        self.map_widget.set_zoom(4)

    def listing_url_event(self):

        # The URL to open
        url = df.at[self.destNum, 'shipURL']

        # Open the URL in the user's default web browser
        webbrowser.open(url)

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga",
                                            max_zoom=22)
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga",
                                            max_zoom=22)

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    df = first(Arr)
    app = App()
    app.start()
