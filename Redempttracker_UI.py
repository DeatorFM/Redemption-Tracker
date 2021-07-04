import tkinter, json, os, time, datetime, textwrap, threading, win32ui, win32gui, win32con, winsound
from tkinter.constants import *
from tkinter import filedialog, font, messagebox
from selenium import webdriver
from selenium.webdriver.support.relative_locator import By, locate_with, with_tag_name


class MainApp(tkinter.Frame):
    def __init__(self, master=None):
        # Initialisiert GUI des Programms
        super().__init__(master)
        self.pack(expand=False)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=3)

        self.rewards = None
        self.channelname = None
        self.thread_running = False
        self.driver = None
        self.alert = "C:\\Windows\\Media\\Windows Notify System Generic.wav"
        self.eventlist = []
        self.listmode = "counter"

        self.lastredeemed = tkinter.LabelFrame(self, text="Zuletzt eingelöst")
        self.lastredeemed.grid(
            row=0, column=0, columnspan=3, padx=5, pady=5, sticky=W + E
        )
        self.lastredeemed.grid_configure(ipady=3)

        self.lastitem = tkinter.Label(self.lastredeemed, text="Warte auf Ereignis", width=56, anchor=W, justify=LEFT)
        self.lastitem.grid(row=0, column=0, columnspan=3, sticky=W, pady=3, padx=3)

        self.attmessage = tkinter.Label(
            self.lastredeemed, text="", bg="#ffffff", width=56, anchor=W, justify=LEFT
        )
        self.attmessage.grid(row=1, column=0, columnspan=3, padx=3, sticky=W)

        monofont = font.Font(family="Consolas", size=10)
        self.redeemedbox = tkinter.Listbox(self, width=58, font=monofont, relief=SUNKEN)
        self.redeemedbox.grid(row=1, column=0, columnspan=3)

        self.minusbutton = tkinter.Button(
            self,
            text="-1",
            width=7,
            state=DISABLED,
            command=lambda: self.deleter("-"),
        )
        self.minusbutton.grid(row=2, column=0, pady=5)

        self.modebutton = tkinter.Button(
            self,
            text="Ereignisse",
            width=10,
            state=DISABLED,
            command=lambda: self.set_mode("events"),
        )
        self.modebutton.grid(row=2, column=1, padx=10, pady=5)

        self.plusbutton = tkinter.Button(
            self,
            text="+1",
            width=7,
            state=DISABLED,
            command=lambda: self.deleter("+"),
        )
        self.plusbutton.grid(row=2, column=2, pady=5, sticky=E, padx=50)

        self.statusframe = tkinter.LabelFrame(self, text="Trackingeinstellungen")
        self.statusframe.grid(
            row=3, column=0, columnspan=3, pady=10, padx=5, sticky=W + E
        )
        self.statusframe.grid_columnconfigure(0, weight=3)
        self.statusframe.grid_columnconfigure(1, weight=0)
        self.statusframe.grid_columnconfigure(2, weight=0)
        self.statusframe.grid_configure(ipady=3)

        self.channel = tkinter.Label(self.statusframe, text="Keine Eingabe")
        self.channel.grid(row=0, column=0, rowspan=2, sticky=N + W, padx=2, pady=5)

        self.newbutton = tkinter.Button(
            self.statusframe, text="Neu", width=10, command=self.create_window
        )
        self.newbutton.grid(row=0, column=1, padx=5, sticky=E)

        self.openbutton = tkinter.Button(
            self.statusframe, text="Öffnen", width=10, command=self.Open_File
        )
        self.openbutton.grid(row=0, column=2, padx=5, pady=5, sticky=E)

        self.outputmode = tkinter.BooleanVar()
        self.outputmode.set(False)
        self.checkoutputmode = tkinter.Checkbutton(
            self.statusframe,
            text="Immer alle Belohnungen anzeigen",
            variable=self.outputmode,
            command=self.list_update,
        )
        self.checkoutputmode.grid(row=1, column=0, columnspan=3, sticky=W)

        self.alert_on = tkinter.BooleanVar()
        self.alert_on.set(False)
        self.checkalert = tkinter.Checkbutton(
            self.statusframe,
            text="Sound bei neuem Ereignis abspielen",
            variable=self.alert_on,
        )
        self.checkalert.grid(row=2, column=0, columnspan=3, sticky=W)

        self.startbutton = tkinter.Button(
            self, text="Start", width=10, state=DISABLED, command=self.initialize
        )
        self.startbutton.grid(row=4, column=0, pady=10, padx=40)

        self.saveendbutton = tkinter.Button(
            self, text="Speichern & Beenden", command=self.save_json
        )
        self.saveendbutton.grid(
            row=4, column=1, columnspan=2, padx=40, pady=10, sticky=E
        )

        self.statusbar = tkinter.Label(
            self, text="Keine Datei geöffnet", bd=1, relief=SUNKEN, anchor=W
        )
        self.statusbar.grid(row=5, column=0, columnspan=3, sticky=W + E)

    def create_window(self):
        # Ruft Fenster für die Eingabe der Funktion von "Create_New"

        createwin = tkinter.Toplevel(bd=10)
        createwin.title("Neues Trackingprofil erstellen")
        createwin.resizable(False, False)

        label1 = tkinter.Label(createwin, text="Kanalname")
        label1.grid(row=0, columnspan=3, pady=2, sticky=W)

        channelentry = tkinter.Entry(createwin, width=60, borderwidth=2)
        channelentry.grid(row=1, columnspan=3, padx=3, sticky=W)

        borderlabel = tkinter.Label(createwin, text=" ")
        borderlabel.grid(row=2)

        label2 = tkinter.Label(createwin, text="Belohnungen (Keine Emojis verwenden)")
        label2.grid(row=3, columnspan=3, sticky=W)

        rewardsentry = tkinter.Entry(createwin, width=46, borderwidth=2)
        rewardsentry.grid(row=4, column=0, padx=3, columnspan=2)

        gatherbutton = tkinter.Button(
            createwin,
            text="Auto-Eintrag",
            command=lambda: self.gather_rewards(channelentry.get(), rewardsentry),
        )
        gatherbutton.grid(row=4, column=2)

        okbutton = tkinter.Button(
            createwin,
            text="Erstellen",
            width=10,
            command=lambda: self.Create_New(
                channelentry.get(), rewardsentry.get(), createwin
            ),
        )
        okbutton.grid(row=5, column=0, pady=5, sticky=S)

        cancelbutton = tkinter.Button(
            createwin, text="Abbrechen", width=10, command=lambda: createwin.destroy()
        )
        cancelbutton.grid(row=5, column=1, columnspan=3, pady=5, sticky=S)

    def Open_File(self):
        # Öffnet Datei und prüft ob es sich dabei je um eine txt- oder json-Datei handelt
        self.filename = filedialog.askopenfilename(
            initialdir=__file__,
            title="Datei auswählen",
            filetypes=(
                ("Liste der Belohnungen", ".txt"),
                ("Gespeicherte Zähler", ".json"),
                ("Alarm", ".wav"),
            ),
        )
        if self.filename.endswith("txt"):
            with open(self.filename, "r", encoding="utf-8") as f:
                rewards_raw = f.read()
            self.channelname = os.path.basename(self.filename)[:-4]  # Alternativ f.name
            self.channel["text"] = "Kanal: {}".format(self.channelname)
            self.startbutton["state"] = NORMAL
            self.rewards = {str(word): 0 for word in rewards_raw.split(", ")}
            for key in self.rewards.keys():
                self.redeemedbox.insert(
                    END, textwrap.shorten(key, width=55, placeholder=" ...")
                )
            self.statusbar["text"] = "{}.txt importiert".format(self.channelname)

        if self.filename.endswith("json"):
            with open(self.filename, "r", encoding="utf-8") as f:
                rewards = json.load(f)
            rewards_raw = ", ".join(list(rewards.keys()))
            self.channelname = os.path.basename(self.filename)[
                :-10
            ]  # Alternativ f.name
            self.channel["text"] = "Kanal: {}".format(self.channelname)
            self.startbutton["state"] = NORMAL
            self.rewards = rewards
            for key in self.rewards.keys():
                self.redeemedbox.insert(
                    END, textwrap.shorten(key, width=55, placeholder=" ...")
                )
            self.statusbar["text"] = "{}_save.json importiert".format(self.channelname)

        if self.filename.endswith("wav"):
            self.alert = self.filename

    def Create_New(self, channelname, rewardlist, window):
        # Kreiert eine neue txt-Datei mit dem Namen des Kanals, die alle Belohnungen enthält
        if channelname or rewardlist:
            self.channelname = channelname.lower()
            self.channel["text"] = "Kanal: {}".format(channelname)
            with open("{}.txt".format(channelname), "w", encoding="utf-8") as f:
                f.write(rewardlist)
            self.startbutton["state"] = NORMAL
            window.destroy()
            self.rewards = {str(word): 0 for word in rewardlist.split(", ")}
            self.statusbar["text"] = "{}.txt erstellt".format(self.channelname)
            for key in self.rewards.keys():
                self.redeemedbox.insert(
                    END, textwrap.shorten(key, width=55, placeholder=" ...")
                )
        else:
            window.destroy()

    def gather_rewards(self, channelname, window):
        if channelname:
            l = []
            self.boot_driver(channelname)
            self.driver.implicitly_wait(10)
            self.driver.find_element(
                By.XPATH,
                "//div[@class='InjectLayout-sc-588ddc-0 eVRxkm']//button[@class='ScCoreButton-sc-1qn4ixc-0 ScCoreButtonText-sc-1qn4ixc-3 gShCOc']",
            ).click()
            time.sleep(0.2)
            self.driver.find_element(
                By.XPATH,
                "//div[@class='sc-AxjAm jzZXia']//button[@class='ScCoreButton-sc-1qn4ixc-0 ScCoreButtonPrimary-sc-1qn4ixc-1 jbpuQw']",
            ).click()
            raw = self.driver.find_elements(By.XPATH, "//p[@class='sc-AxirZ juurQm']")
            for item in raw:
                l.append(item.text)
            string = ", ".join(l)
            window.delete(0, END)
            window.insert(0, string)
            self.driver.quit()
        else:
            messagebox.showinfo("Auto-Eintrag", "Bitte Kanalnamen vorher eingeben!")
            self.create_window()

    def boot_driver(self, channelname):
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
                channelname, channelname
            )
        )

    def save_json(self):
        # Speichert Zählerstand als json-Datei
        try:
            self.thread_running = False
            if self.rewards != None:
                with open(
                    "{}_save.json".format(self.channelname), "w", encoding="utf-8"
                ) as f:
                    json.dump(self.rewards, f, ensure_ascii=False)
            self.driver.quit()
            root.destroy()

        except AttributeError:
            root.destroy()

    def initialize(self):
        # Initialisiert Browser als Hintergrundprozess
        self.thread_running = True
        self.list_update()
        self.boot_driver(self.channelname)

        self.newbutton["state"] = DISABLED
        self.openbutton["state"] = DISABLED
        self.minusbutton["state"] = NORMAL
        self.plusbutton["state"] = NORMAL
        self.startbutton["state"] = DISABLED
        self.modebutton["state"] = NORMAL

        # Scaping-Schleife wird in einem Thread gestartet, damit mainloop von tkinter nicht crasht
        thread = threading.Thread(target=self.runtracking)
        thread.daemon = True
        thread.start()
        self.statusbar["text"] = "Trackt {}".format(self.channelname)

    def runtracking(self):  # Hauptfunktion: Tracking-Loop und Analyse
        prevlen = 0
        username = ""
        message = "Keine Nachricht"
        hwnd = win32ui.FindWindow(None, r"Redempttracker by Deator").GetSafeHwnd()

        while self.thread_running == True:
            # Scrapt nach neuen Objekten der div-Klasse, die erscheint, wenn jemand jemand etwas einlöst
            rawobjects = self.driver.find_elements(
                By.XPATH, "//div[@class='sc-AxjAm dSWgRY']"
            )

            if len(rawobjects) > prevlen:
                # Prüft, ob eine neue Belohnung eingelöst wurde
                Text = rawobjects[-1].text
                try:
                    Text1 = " ".join(Text.split()[:-2])
                    Text2 = " ".join(Text.split()[2:-2])
                except IndexError:
                    Text1 = Text
                    Text2 = Text

                # Prüft ob eine der Keys im extrahierten Text ist
                for key in self.rewards.keys():
                    if key == Text1 or key == Text2:
                        self.rewards[key] += 1

                        # Prüft nach Username bei Einlösung angehängter Nachricht z.B.: "Grüße ausrichten erhalten"
                        if Text.startswith(tuple(self.rewards.keys())) == False:
                            username = Text.split()[0]
                        else:
                            raw_username = self.driver.find_elements(
                                locate_with(
                                    By.XPATH,
                                    "//div[@class='sc-AxjAm ipUaGy']//span[@class='chat-author__display-name']",
                                ).below(rawobjects[-1])
                            )
                            username = raw_username[-1].text
                            raw_username.clear()
                            raw_message = self.driver.find_elements(
                                locate_with(
                                    By.XPATH,
                                    "//span[@data-test-selector='chat-line-message-body']/",
                                ).below(rawobjects[-1])
                            )
                            message = raw_message[-1].text
                            raw_message.clear()

                        # Zuweisung der Labels für die letzte Einlösung und der Nachricht
                        self.lastitem["text"] = textwrap.fill(
                            '"{}" um {} von {}'.format(
                                key, datetime.datetime.now().strftime("%H:%M"), username
                            ),
                            width=65,
                        )

                        self.attmessage["text"] = textwrap.fill(message, width=65)
                        message = ""

                        self.eventlist.append(
                            '{}: "{}" von {}'.format(
                                datetime.datetime.now().strftime("%H:%M"), key, username
                            )
                        )

                        win32gui.FlashWindowEx(hwnd, win32con.FLASHW_ALL, 5, 0)
                        if self.alert_on.get() == True:
                            winsound.PlaySound(self.alert, winsound.SND_FILENAME)
                        break

                self.list_update()

            prevlen = len(rawobjects)
            time.sleep(0.5)

    def set_mode(self, mode):
        self.listmode = mode
        self.list_update()

        if mode == "counter":
            self.minusbutton["state"] = NORMAL
            self.plusbutton["state"] = NORMAL
            self.modebutton["text"] = "Ereignisse"
            self.modebutton["command"] = lambda: self.set_mode("events")
        else:
            self.minusbutton["state"] = DISABLED
            self.plusbutton["state"] = DISABLED
            self.modebutton["text"] = "Zähler"
            self.modebutton["command"] = lambda: self.set_mode("counter")

    def list_update(self):
        # Aktualisiert die Liste, in der alle eingelösten Belohnungen angezeigt werden
        if self.thread_running == True:
            if self.listmode == "counter":
                self.redeemedbox.delete(0, END)
                for key, value in self.rewards.items():
                    if self.outputmode.get() == False:
                        if value != 0:
                            self.redeemedbox.insert(
                                END,
                                "{:<54} {:2}".format(
                                    textwrap.shorten(key, width=55, placeholder=" ..."),
                                    value,
                                ),
                            )
                    else:
                        self.redeemedbox.insert(
                            END,
                            "{:<54} {:2}".format(
                                textwrap.shorten(key, width=55, placeholder=" ..."),
                                value,
                            ),
                        )
            if self.listmode == "events":
                self.redeemedbox.delete(0, END)
                for event in self.eventlist:
                    self.redeemedbox.insert(0, event)

    def deleter(self, operator):
        # Zieht bzw. addiert je nach Klick auf "-1" oder "+1" vom Zähler des ausgewählten Elements
        try:
            pos = self.redeemedbox.curselection()[0]
            selection = self.redeemedbox.get(pos)
            selection = " ".join(selection.split()[:-1])
            for key in self.rewards.keys():
                if key == selection:
                    if operator == "-":
                        self.rewards[key] -= 1 if self.rewards[key] != 0 else 0
                        break
                    elif operator == "+":
                        self.rewards[key] += 1
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
