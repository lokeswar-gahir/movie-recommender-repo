import pickle
import regex as re
import pandas as pd
from nltk.stem.porter import PorterStemmer

ps = PorterStemmer()
with open("resources/count_vectorizer_3000_new_again.pkl", "rb") as f1:
    cv = pickle.load(f1)
with open("resources/Bernoulli_naive_bayes_again.pkl","rb") as f2:
    clf = pickle.load(f2)

def remove_html(x):
    pattern="<.*?>"
    return re.sub(pattern,"",x)
def remove_special_ch(x):
    out=""
    for ch in x:
        if ch.isalnum():
            out+=ch
        else:
            out+=" "
    return out
def apply_stem(x):
    out = []
    for i in x.split():
        out.append(ps.stem(i))
    return " ".join(out)
def preprocessing(review):
    review = remove_html(review)
    review = review.lower()
    review = remove_special_ch(review)
    review = apply_stem(review)
    return review
def analyze(review):
    review=preprocessing(review)
    vector = cv.transform(pd.Series(review)).toarray()
    pred = clf.predict(vector)
    return pred[0]

def to_apply(row):
    return analyze(row["content"])
class Analyzer:
    def __init__(self):
        pass
    def perform(self, data):
        data["sentiment"]=data.apply(to_apply, axis=1)
        return data
if __name__=="__main__":
    pass