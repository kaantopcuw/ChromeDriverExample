from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.ttk import Combobox
from selenium import webdriver
from bs4 import BeautifulSoup
import os, time, requests, collections, shelve

def normalize(score, maxScore):
    return score/maxScore

def make_soup(link):
    driver = webdriver.Chrome(os.getcwd()+'/chromedriver.exe')   # can be different with OS. Refer to chromedriver file on your machine.
    driver.get(link)
    time.sleep(5)
    elem = driver.find_element_by_xpath("//*")
    html = elem.get_attribute("outerHTML")
    soup = BeautifulSoup(html,'html.parser')
    return soup

def soup_requests(link):
    req = requests.get(link)
    soup = BeautifulSoup(req.content, "html.parser")
    return soup

def freq_find(keys):
    return collections.Counter(keys)

def clear_text(text):
    text = text.strip().lower()
    text = text.replace(",", "")
    text = text.replace(".", "")
    text = text.replace("\n", "")
    text = text.replace("\r\n", "")
    return text

class Person:
    def __init__(self, name, department, link, keywords):
        self.name = name
        self.department = department
        self.link = link
        self.keywords = keywords
    
    def get_tuple(self, score):
        return (self.name, score, self.link)

    def calc_score(self, topScore):
        pass

class GUI:

    def double_click(self, event):
        col = self.table.identify_column(event.x)
        values_row = self.table.item(self.table.focus())
        if col == '#3':
            link = values_row["values"][2]
            driver = webdriver.Chrome(os.getcwd()+'/chromedriver')
            driver.get(link)

    def insert_table(self, persons):
        self.table.delete(*self.table.get_children())
        for i, person in enumerate(persons):
            tableTuple = (person[0], "{:.2f}".format(person[1]), person[2])
            self.table.insert("", "end", text=str(i+1), values=tableTuple)

    def search(self):
        keyword = self.keywords_text.get().lower()
        if keyword != "":
            if keyword in self.mydb:
                allPersons = []
                curPersons = []
                if self.selected_department == "All":
                    for person in self.persons.values():
                        if keyword in person.keywords:
                            curPersons.append(person)
                            allPersons.append(person)
                else:
                    for person in self.persons.values():
                        if keyword in person.keywords:
                            if self.selected_department == person.department:
                                curPersons.append(person)
                            allPersons.append(person)
                scores = [x.keywords[keyword] for x in allPersons]
                maxScore = max(scores)
                tupleList = [p.get_tuple(normalize(p.keywords[keyword], maxScore)) for p in curPersons]
                tupleList = sorted(tupleList, key=lambda tup: tup[1], reverse=True)
                self.insert_table(tupleList)

    def cmb_select(self, event):
        self.selected_department = self.department_Combobox.get()

    def add_keys_in_db(self, keys):
        for key in keys.keys():
            if key in self.mydb:
                curCount = self.mydb[key]
                curCount += keys[key]
                self.mydb[key] = curCount
            else:
                self.mydb[key] = keys[key]

    def progres_head_change_text(self, text):
        self.progress_head_label["text"] = text
        self.progress_frame.update()

    def progres_tail_change_text(self, text):
        self.progress_tail_label["text"] = text
        self.progress_frame.update()

    def fill_table(self, datas):
        self.table.delete(*self.table.get_children())

    def fetch_person(self, link):
        soup = soup_requests(link)
        metaDatas = soup.find("meta", attrs={"name":"keywords"})["content"].split(",")
        name = metaDatas[0].strip()
        department = metaDatas[1].strip()
        keys = soup.find(class_="academic-staff-detail-content sub-page-content").getText().split(" ")
        keys = [clear_text(x) for x in keys]
        keys = filter(None, keys)
        key_freqs = freq_find(keys)
        newPerson = Person(name, department, link, key_freqs)
        self.persons[name] = newPerson

        self.add_keys_in_db(key_freqs)

        if department not in self.department_list:
            self.department_list.append(department)
        

    def fetch_profiles(self):
        if(self.url_text.get() != ""):
            self.mydb = shelve.open("cache", "n")
            self.department_list = ["All"]
            self.persons = {}
            self.progres_head_change_text("Collecting Faculty Members' Profile Links…")
            soup = make_soup(self.url_text.get())
            urls = soup.select("div.academic-staff-category-inside > a") 
            self.progres_head_change_text("Fetching Profiles...")
            progress = 0
            step = 300 / float(len(urls))
            for url in urls:
                progress += step
                self.progress_bar.create_rectangle(0, 0, progress, 25, fill="green")
                self.progres_tail_change_text('{:.0f} Complated'.format(progress/3))
                self.fetch_person("https://www.sehir.edu.tr"+url.get("href"))
        
            self.department_Combobox["values"] = tuple(sorted(self.department_list))
            self.department_Combobox.current(0)
            self.selected_department = self.department_Combobox.get()

    def __init__(self):
        self.main_window = Tk()
        self.main_window.title("Search Engine")
        self.main_window.minsize(1000, 500)

        self.main_frame = Frame(self.main_window)

        self.head_label = Label(self.main_frame, text="Sehir Faculty Member Search Engine", bg="blue", fg="white", padx=2, pady=2, font="Area 20")
        self.head_label.pack(fill="x")
        
        #url
        self.url_frame = Frame(self.main_frame)
        self.url_label = Label(self.url_frame, text="Faculty Profile Url:", font="Area 14")
        self.url_label.grid(row=0, column=0, padx=10)

        self.url_text = Entry(self.url_frame, font="Area 12", width=80)
        self.url_text.grid(row=0, column=1)
        self.url_text.insert(INSERT, "https://www.sehir.edu.tr/en/academics/college-of-engineering-and-natural-sciences/academic-staff")
        self.url_frame.pack()

        #fetch button
        self.fetch_button = Button(self.main_frame, text="Fetch Profiles", command=self.fetch_profiles)
        self.fetch_button.pack(pady=15)

        #progtess bar
        self.progress_frame = Frame(self.main_frame)

        self.progress_head_label = Label(self.progress_frame, text="", font="Area 12")
        self.progress_head_label.grid(row=0, column=0, padx=20)

        self.progress_bar = Canvas(self.progress_frame, bg='grey', width =300, height = 20, borderwidth=2, relief='sunken')
        self.progress_bar.grid(row=0, column=1)

        self.progress_tail_label = Label(self.progress_frame, text="0% Completed", font="Area 12")
        self.progress_tail_label.grid(row=0, column=2, padx=20)

        self.url_frame.grid_columnconfigure(0, weight=1)
        self.url_frame.grid_columnconfigure(1, weight=2)
        self.url_frame.grid_columnconfigure(2, weight=1)
        self.progress_frame.pack(pady=20)

        #keywords and department
        self.key_and_dep_frame = Frame(self.main_frame)

        self.keywords_label = Label(self.key_and_dep_frame, text="Keywords:", font="Area 16")
        self.keywords_label.grid(row=0, column=0,padx=10)

        self.keywords_text = Entry(self.key_and_dep_frame, font="Area 14")
        self.keywords_text.grid(row=0, column=1, padx=10)
        
        self.department_label = Label(self.key_and_dep_frame, text="Department:", font="Area 16")
        self.department_label.grid(row=0, column=2, padx=10)

        self.department_Combobox = Combobox(self.key_and_dep_frame, width=25)
        self.department_Combobox.bind("<<ComboboxSelected>>", self.cmb_select)
        self.department_Combobox.grid(row=0, column=3, padx=10)
                
        self.key_and_dep_frame.pack(pady=20)

        #search button
        self.search_button = Button(self.main_frame, text="Search", width=30, command=self.search)
        self.search_button.pack(pady=20)

        #table
        self.table = ttk.Treeview(self.main_frame)
        self.table["columns"] = ("col1", "col2", "col3")
        self.table.heading("#0", text="Rank",anchor=CENTER)
        self.table.heading("col1", text="Faculty Member",anchor=CENTER)
        self.table.heading("col2", text="Score",anchor=CENTER)
        self.table.heading("col3", text="Link",anchor=CENTER)
        self.table.bind("<Double-1>", self.double_click)
        self.table.pack(pady=20, padx=20, fill="x")

        self.main_frame.pack(fill="both", expand=True)

    def show(self):
        self.main_window.mainloop()

def main():
    gui = GUI()
    gui.show()

if __name__ == '__main__': main()