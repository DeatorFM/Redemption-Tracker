import tkinter, json, os, time, datetime, threading
from tkinter.constants import *
from tkinter import filedialog, font
from selenium import webdriver

class MainApp(tkinter.Frame):
    def __init__(self, master=None):
        # Initialisiert GUI des Programms
        super().__init__(master)
        self.pack(expand=False)

        self.rewards = None
        self.channelname = None
        self.thread_running = True
        self.driver = None

        self.lastredeemed = tkinter.Label(self, text="Zuletzt eingelöst: unbekannt")
        self.lastredeemed.grid(
            row=0, column=0, columnspan=2, padx=12, pady=5, sticky="w"
        )

        monofont = font.Font(family="Consolas", size=10)
        self.redeemedbox = tkinter.Listbox(self, width=55, font= monofont, relief= SUNKEN)
        self.redeemedbox.grid(row=1, column=0, columnspan=2)

        self.minusbutton = tkinter.Button(
            self,
            text="-1",
            width=7,
            state=DISABLED,
            command=lambda: self.deleter("-"),
        )
        self.minusbutton.grid(row=2, column=0, pady=5, padx=60)

        self.plusbutton = tkinter.Button(
            self,
            text="+1",
            width=7,
            state=DISABLED,
            command=lambda: self.deleter("+"),
        )
        self.plusbutton.grid(row=2, column=1, pady=5)

        self.statusframe = tkinter.LabelFrame(self, text="Trackinginformationen")
        self.statusframe.grid(row=3, column=0, columnspan=2, pady=10, padx=5)

        self.channel = tkinter.Label(self.statusframe, text="Keine Eingabe")
        self.channel.grid(row=0, column=0, sticky="w", padx=2)

        self.rewardbox = tkinter.Entry(self.statusframe, width=50, state=DISABLED)
        self.rewardbox.grid(row=1, column=0, padx=5)

        self.newbutton = tkinter.Button(
            self.statusframe, text="Neu", width=10, command=self.create_window
        )
        self.newbutton.grid(row=0, column=1, padx=5)

        self.openbutton = tkinter.Button(
            self.statusframe, text="Öffnen", width=10, command=self.Open_File
        )
        self.openbutton.grid(row=1, column=1, padx=5, pady=5)

        self.startbutton = tkinter.Button(
            self, text="Start", width=10, state=DISABLED, command=self.initialize
        )
        self.startbutton.grid(row=4, column=0, pady=5, padx=30)

        self.saveendbutton = tkinter.Button(
            self, text="Speichern & Beenden", command=self.save_json
        )
        self.saveendbutton.grid(row=4, column=1, pady=5, padx=30)

    def create_window(self):
        # Ruft Fenster für die Eingabe der Funktion von "Create_New"
        global createwin

        createwin = tkinter.Toplevel()
        createwin.title("Neues Trackingziel eingeben")
        createwin.resizable(False, False)

        label1 = tkinter.Label(createwin, text="Kanalname")
        label1.grid(row=0, columnspan=2, padx=6, sticky="w")

        channelentry = tkinter.Entry(createwin, width=60, borderwidth=2)
        channelentry.grid(row=1, columnspan=2, padx=5)

        borderlabel = tkinter.Label(createwin, text=" ")
        borderlabel.grid(row=2)

        label2 = tkinter.Label(createwin, text="Belohnungen")
        label2.grid(row=3, columnspan=2, padx=6, sticky="w")

        rewardsentry = tkinter.Entry(createwin, width=60, borderwidth=2)
        rewardsentry.grid(row=4, columnspan=2, padx=10)

        okbutton = tkinter.Button(
            createwin,
            text="Erstellen",
            width=10,
            command=lambda: self.Create_New(channelentry.get(), rewardsentry.get()),
        )
        okbutton.grid(row=5, column=0, pady=5)

        cancelbutton = tkinter.Button(
            createwin, text="Abbrechen", width=10, command=lambda: createwin.destroy()
        )
        cancelbutton.grid(row=5, column=1, pady=5)

    def Open_File(self):
        # Öffnet Datei und prüft ob es sich dabei je um eine txt- oder json-Datei handelt
        self.filename = filedialog.askopenfilename(
            initialdir=__file__,
            title="Datei auswählen",
            filetypes=(
                ("Liste der Belohnungen", ".txt"),
                ("Gespeicherte Zähler", ".json"),
            ),
        )
        if self.filename.endswith("txt"):
            with open(self.filename, "r", encoding="utf-8") as f:
                rewards_raw = f.read()
            self.rewardbox["state"] = NORMAL
            self.rewardbox.delete(0, END)
            self.rewardbox.insert(0, rewards_raw)
            self.channelname = os.path.basename(self.filename)[:-4]
            self.channel["text"] = "Kanal: {}".format(self.channelname)
            self.startbutton["state"] = NORMAL
            self.rewards = {str(word): 0 for word in rewards_raw.split(", ")}

        if self.filename.endswith("json"):
            with open(self.filename, "r", encoding="utf-8") as f:
                rewards = json.load(f)
            rewards_raw = ", ".join(list(rewards.keys()))
            self.rewardbox["state"] = NORMAL
            self.rewardbox.delete(0, END)
            self.rewardbox.insert(0, rewards_raw)
            self.channelname = os.path.basename(self.filename)[:-10]
            self.channel["text"] = "Kanal: {}".format(self.channelname)
            self.startbutton["state"] = NORMAL
            self.rewards = rewards
            self.list_update()

    def Create_New(self, channel_name, rewardlist):
        # Kreiert eine neue txt-Datei mit dem Namen des Kanals, die alle Belohnungen enthält
        self.channelname = channel_name
        self.channel["text"] = "Kanal: {}".format(channel_name)
        self.rewardbox["state"] = NORMAL
        self.rewardbox.insert(0, rewardlist)
        with open("{}.txt".format(channel_name), "w", encoding="utf-8") as f:
            f.write(rewardlist)
        self.startbutton["state"] = NORMAL
        createwin.destroy()
        self.rewards = {str(word): 0 for word in rewardlist.split(", ")}

    def save_json(self):
        # Speichert Zählerstand als json-Datei
        self.thread_running = False
        with open("{}_save.json".format(self.channelname), "w", encoding="utf-8") as f:
            json.dump(self.rewards, f, ensure_ascii=False)
        self.driver.quit()
        root.destroy()

    def initialize(self):
        # Initialisiert Browser als Hintergrundprozess
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920x1080")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        self.driver = webdriver.Chrome(
            executable_path="chromedriver.exe", options=chrome_options
        )
        self.driver.get(
            "https://www.twitch.tv/popout/{}/chat?popout=&ab_channel={}".format(
                self.channelname, self.channelname
            )
        )
        time.sleep(1)

        self.newbutton["state"] = DISABLED
        self.openbutton["state"] = DISABLED
        self.minusbutton["state"] = NORMAL
        self.plusbutton["state"] = NORMAL
        self.startbutton["state"] = DISABLED

        # Scaping-Schleife wird in einem Thread gestartet, damit mainloop von tkinter nicht crasht
        thread = threading.Thread(target=self.runtracking)
        thread.daemon = True
        thread.start()

    def runtracking(self):  # Hauptfunktion: Tracking-Loop
        prevlen = 0
        username = ""

        while self.thread_running == True:
            # Scrapt nach neuen Objekten der div-Klasse, die erscheint, wenn jemand jemand etwas einlöst
            rawobjects = self.driver.find_elements_by_xpath(
                "//div[@class='sc-AxjAm dSWgRY']"
            )
            # print(rawobjects)

            if len(rawobjects) > prevlen:
                # Prüft, ob eine neue Belohnung eingelöst wurde
                Text = rawobjects[-1].text
                # print(Text)

                # Prüft nach Username
                if len(Text.split()) >= 2:
                    if Text.split()[1] == "hat":
                        username = Text.split()[0]

                # Prüft ob eine der Keys im extrahierten Text ist
                for key in self.rewards.keys():
                    if key in Text:
                        self.rewards[key] += 1
                        if username:
                            self.lastredeemed[
                                "text"
                            ] = 'Zuletzt eingelöst: "{}" um {} von {}'.format(
                                key, datetime.datetime.now().strftime("%H:%M"), username
                            )
                            username = ""
                        else:
                            self.lastredeemed[
                                "text"
                            ] = 'Zuletzt eingelöst: "{}" um {}'.format(
                                key, datetime.datetime.now().strftime("%H:%M")
                            )
                        break

                prevlen = len(rawobjects)
                self.list_update()

            prevlen = len(rawobjects)
            time.sleep(0.5)

    def list_update(self):
        # Aktualisiert die Liste, in der alle eingelösten Belohnungen angezeigt werden
        self.redeemedbox.delete(0, END)
        for key, value in self.rewards.items():
            if value != 0:
                self.redeemedbox.insert(END, "{:<50} {:2}".format(key, value))

    def deleter(self, operator):
        # Zieht bzw. addiert je nach Klick auf "-1" oder "+1" vom Zähler des ausgewählten Elements
        try:
            pos = self.redeemedbox.curselection()[0]
            key = self.redeemedbox.get(pos)
            key = key.split()
            del key[-1]
            strkey = " ".join(key)
            for k in self.rewards.keys():
                if k in strkey:
                    if operator == "-":
                        self.rewards[k] -= 1 #if self.rewards[k] != 0 else 0
                        break
                    elif operator == "+":
                        self.rewards[k] += 1
                        break
            self.list_update()
        except IndexError:
            pass


os.path.abspath(__file__)

if __name__ == "__main__":

    root = tkinter.Tk()
    root.title("Redempttracker by Deator")
    root.iconbitmap("Redempttracker_Logo.ico")
    root.resizable(False, False)
    app = MainApp(root)
    app.mainloop()