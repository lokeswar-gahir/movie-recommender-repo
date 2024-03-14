import random
import regex as re
import pandas as pd
# from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup as bs
def clean_df(df):
    if len(df)!=0:
        df.drop(df.index, inplace=True)
        print("document cleaned.")
    else:
        print("There is no data to delete !!!")

class Reviews:
    def __init__(self):
        self.df = pd.DataFrame(columns=["username","date","content"])
        self.key=None
        self.soup=None
        self.title=None
        self.total_reviews=None
        self.session = requests
    def get_headers(self):
        user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
        ]

        random_user_agent = random.choice(user_agents)
        headers = {
            'User-Agent': random_user_agent
        }
        return headers
    def get_reviews(self, imdb_id: str):
        if len(self.df)>0:
            clean_df(self.df)
        url="https://www.imdb.com/title/"+str(imdb_id)+"/reviews"
        print("Requesting...", end="")
        count=0
        while True:
            r = self.session.get(url, headers=self.get_headers())
            if r.status_code==200:
                break
            print(f"\n({r.status_code})Requesting again...",end="")
            if count>=10:
                return "requsted more then 10 times and still got nothing !!!"
            count+=1

        print("done.")
        self.soup = bs(r.content, "html.parser")
        lister_list = self.soup.find("div", class_="lister-list")
        total_reviews_div = self.soup.find("div", class_="header")
        self.title = self.soup.find("title").text.split(" - ")[0]
        self.total_reviews = int(total_reviews_div.div.text.split()[0].replace(",",""))
        print(self.get_df(lister_list))
        print(f"Total number of reviews are: {self.total_reviews}")
        if self.total_reviews<25:
            return self.df
        return self.df
    def add_more(self,imdb_id):
        url = f"https://www.imdb.com/title/{imdb_id}/reviews/_ajax?ref_=undefined&paginationKey={self.key}"
        # print(url)
        # return "done"
        print("Requesting...", end="")
        count=0
        while True:
            r =self.session.get(url, headers=self.get_headers())
            if r.status_code==200:
                break
            print("\nRequesting again...",end="")
            if count>=20:
                return "requested more than 20 times and still got nothing !!!"
            count+=1
        print("done.")
        self.soup = bs(r.content, "html.parser")
        lister_list = self.soup.find("div", class_="lister-list")
        print(self.get_df(lister_list))
        print(f"Total number of reviews are: {self.total_reviews}")
        return self.df
    def get_df(self, lister_list):
        rev_list = lister_list.find_all("div", class_= "imdb-user-review")
        if len(rev_list):
            for item in rev_list:
                row=list()
                name_date = item.div.div.find("div", class_="display-name-date")
                spans = name_date.find_all("span")
                content = item.div.div.find("div", class_="content")
                row.append(spans[0].text.replace("\n",""))
                row.append(spans[1].text.replace("\n",""))
                row.append(str(content.div.text.replace("\n","")))
                if len(self.df)<self.total_reviews:
                    self.df.loc[len(self.df)+1]=row
                else:
                    return self.df
            try:
                more = self.soup.find("div", class_="load-more-data")
                pat = r'data-key="(.[^"]+)'
                global key
                self.key = re.findall(pat, str(more))[0]
                # print(f"New key is set: ({self.key})")
            except IndexError:
                print(f"New key not found or is not set !!!")
            return self.df
        else:
            print("No reviews found !!!")
    def close_conn(self):
        self.session.close()
        print("Session Closed.")
if __name__ == "__main__":
    r = Reviews()
    r.get_reviews("tt26612950")
