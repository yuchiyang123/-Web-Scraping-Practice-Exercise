import requests
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
from bs4 import BeautifulSoup
from io import BytesIO
import webbrowser

API_KEY = "YOUR_STEAM_KEY"

class SteamScraper:

    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Steam遊戲爬蟲')
        self.window.geometry('800x500')

        self.scrollable_frame = tk.Frame(self.window)
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True)

        self.search_frame = tk.Frame(self.scrollable_frame)
        self.search_frame.pack(pady=20)

        self.search_entry = tk.Entry(self.search_frame, width=30, font=('標楷體', 12))
        self.search_entry.pack(side=tk.LEFT, padx=10)

        self.search_button = tk.Button(self.search_frame, text='搜尋', command=self.crawl_steam_data, font=('標楷體', 12))
        self.search_button.pack(pady=10)

        self.results_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.results_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.results_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_canvas = tk.Canvas(self.results_frame, yscrollcommand=self.scrollbar.set, bg='white')
        self.results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.results_canvas.yview)

        self.results_inner_frame = tk.Frame(self.results_canvas, bg='white')
        self.results_inner_frame.pack(pady=20)

        self.results_inner_frame.bind("<Configure>", self.on_frame_configure)
        self.results_canvas.bind("<Configure>", self.on_canvas_configure)
        self.results_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        self.results_canvas.create_window((0, 0), window=self.results_inner_frame, anchor=tk.NW)

    def on_frame_configure(self, event):
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.results_canvas.itemconfigure(self.results_inner_frame, width=event.width)

    def on_mousewheel(self, event):
        self.results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def fetch_steam_game_info(self, app_id, language):
        url = f'https://store.steampowered.com/api/appdetails?appids={app_id}&key={API_KEY}&l={language}'
        response = requests.get(url)
        data = response.json()

        if data.get(str(app_id)) and data[str(app_id)].get('success'):
            game_data = data[str(app_id)]['data']
            if game_data.get('name') and game_data.get('price_overview'):
                name = game_data['name']
                price_overview = game_data['price_overview']
                if price_overview['final_formatted'].strip() == '':
                    price = '免費'
                else:
                    price = f'特惠價格：{price_overview["final_formatted"]}\n原價格：{price_overview["initial_formatted"]}'
                return name, price, game_data.get('steam_appid')

        return None, None, None

    def clear_results(self):
        for widget in self.results_inner_frame.winfo_children():
            widget.destroy()

    def crawl_steam_data(self):
        self.clear_results()  # 清除上一次的搜索结果

        search_term = self.search_entry.get()

        url = f'https://store.steampowered.com/search/?sort_by=_ASC&supportedlang=tchinese&os=win&filter=globaltopsellers&term={search_term}'

        all_games = []

        page = 1
        while True:
            response = requests.get(f'{url}&page={page}')
            response.encoding = 'utf-8'
            html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            search_results = soup.find_all('a', class_='search_result_row')

            if not search_results:
                break

            for result in search_results:
                game_id = result.get('data-ds-appid')
                game_name = result.find('span', class_='title').text.strip()
                all_games.append({'id': game_id, 'name': game_name})

            page += 1

        if not all_games:
            messagebox.showinfo('搜尋結果', '找不到相關遊戲。')
        else:
            self.show_game_info(all_games)

    def show_game_info(self, games):
        max_width = 0
        max_height = 0
        max_frame = None
        for game in games:
            app_id = game['id']
            name, price, steam_appid = self.fetch_steam_game_info(app_id, 'tchinese')

            if name and price:
                game_frame = tk.Frame(self.results_inner_frame, bg='white', padx=10, pady=10)
                game_frame.pack(fill=tk.X, pady=10)

                # 設置連結標題
                title_label = tk.Label(game_frame, text=f'遊戲名稱：{name}', font=('標楷體', 12), fg='blue', cursor='hand2', bg='white')
                title_label.pack(pady=5)
                title_label.bind("<Button-1>", lambda event, appid=steam_appid: self.open_steam_link(appid))

                thumbnail_url = f'https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/capsule_184x69.jpg'
                response = requests.get(thumbnail_url)
                image_data = response.content

                img = Image.open(BytesIO(image_data))
                img_resized = img.resize((200, 80))
                img_tk = ImageTk.PhotoImage(img_resized)

                img_label = tk.Label(game_frame, image=img_tk, bg='white')
                img_label.pack(pady=5)
                img_label.image = img_tk

                price_label = tk.Label(game_frame, text=price, font=('標楷體', 12), bg='white')
                price_label.pack(pady=5)

                frame_width = game_frame.winfo_width()
                frame_height = game_frame.winfo_height()

                if frame_width > max_width:
                    max_width = frame_width
                if frame_height > max_height:
                    max_height = frame_height
                    max_frame = game_frame

        self.results_inner_frame.update_idletasks()
        self.results_inner_frame.config(width=max_width, height=max_height)

        for child_frame in self.results_inner_frame.winfo_children():
            child_frame.config(width=max_width)

        if max_frame:
            self.results_canvas.yview_moveto(max_frame.winfo_y() / self.results_inner_frame.winfo_height())

    def open_steam_link(self, appid):
        steam_link = f'https://store.steampowered.com/app/{appid}'
        webbrowser.open(steam_link)

    def run(self):
        self.window.mainloop()

scraper = SteamScraper()
scraper.run()
