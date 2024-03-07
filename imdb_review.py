print("importing dependencies...", end="")
from bs4 import BeautifulSoup as bs
import random
import pandas as pd
from requests_html import HTMLSession
import requests as req
import regex as re
import asyncio
print("done.")
user_agents = [
  "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
  "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
  "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
  ]

random_user_agent = random.choice(user_agents)
headers = {
    'User-Agent': random_user_agent
}

df = pd.DataFrame(columns=["username","date","content"])
key=""
soup=""
total_reviews=0
session = HTMLSession()
def get_reviews(imdb_id):
    url="https://www.imdb.com/title/"+str(imdb_id)+"/reviews"
    print("Requesting...", end="")
    while True:
        global headers
        r = session.get(url, headers=headers)
        if r.status_code==200:
            break
        print(f"\n({r.status_code})Requesting again...",end="")
    print("done.")
    soup = bs(r.html.html, "html.parser")
    lister_list = soup.find("div", class_="lister-list")
    total_reviews_div = soup.find("div", class_="header")
    global total_reviews
    total_reviews = int(total_reviews_div.div.text.split()[0].replace(",",""))
    
    print(get_df(lister_list, df, soup))
    print(f"Total number of reviews are: {total_reviews}")
    if total_reviews<25:
        r.close()
        print("Connection Closed.")
        # save_df(df)
        # clean_df(df)
        return df
    while True:
        recieved_command = input("More reviews: ")
        if recieved_command=="y" or recieved_command=="Y":
            url = f"https://www.imdb.com/title/{imdb_id}/reviews/_ajax?ref_=undefined&paginationKey={key}"
            print("Requesting...", end="")
            while True:
                random_user_agent = random.choice(user_agents)
                headers = {
                    'User-Agent': random_user_agent
                }
                r = session.get(url, headers=headers)
                if r.status_code==200:
                    break
                print("\nRequesting again...",end="")
            print("done.")
            soup = bs(r.html.html, "html.parser")
            lister_list = soup.find("div", class_="lister-list")
            print(get_df(lister_list, df, soup))
            print(f"Total number of reviews are: {total_reviews}")
        else:
            # save_df(df)
            break
    r.close()
    print("Connection Closed.")
    # clean_df(df)
    return df
def get_df(lister_list,df, soup):
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
                if len(df)<total_reviews:
                    df.loc[len(df)+1]=row
                else:
                    return df
            try:
                more = soup.find("div", class_="load-more-data")
                pat = r'data-key="(.[^"]+)'
                global key
                key =  re.findall(pat, str(more))[0]
            except IndexError:
                pass
            return df
        else:
            print("No reviews found !!!")
def save_df(df):
    if len(df)!=0:
        df.to_csv("test1.csv", index=False)
        print("document saved.")
    else:
        print("There is no data to save !!!")
def clean_df(df):
    if len(df)!=0:
        df.drop(df.index, inplace=True)
        print("document cleaned.")
    else:
        print("There is no data to delete !!!")
if __name__=="__main__":
    get_reviews("tt0499549") # 3800
    # get_reviews("tt0388698") # 0
    # get_reviews("tt8907844") #5
    # print(get_reviews("tt11234994")) # 12
    # get_reviews("tt15837600") # 158
    # get_reviews("tt1093370")