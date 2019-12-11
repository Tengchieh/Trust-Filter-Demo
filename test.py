
# coding: utf-8

# In[1]:


from flask import Flask, render_template
from werkzeug.wrappers import Request, Response
import pandas as pd
import os
import csv
 
app = Flask (__name__)

path = os.path.join("data")

df_scores = pd.read_csv(os.path.join('data', 'results', '2015', '11', 'trust_scores_2015_11.csv'))

company_list = []
with open(os.path.join(path,"SP500.csv")) as SP500csv:
    reader = csv.DictReader(SP500csv)
    for row in reader:
        company_list.append(row['Symbol'])
        
target_company = company_list.index('SPY')
target_date = '11/3/2015'

with open(os.path.join(path, "id_list.txt" )) as id_list:
    reader = id_list.readlines()
    idList = [x.strip() for x in reader]
    #n_authors = len(idList)
            
sentiment = []
sentimentpath = os.path.join(path, 'results', '2015', '11', 'User_Sentiment')
for user in idList:
    with open(os.path.join(sentimentpath,"acc_sentiment_2015_11_" + user + ".csv")) as sentimentfile:
        reader = csv.DictReader(sentimentfile)
        cnt = 0
        for row in reader:
            if cnt == target_company:
                sentiment.append(row[target_date])            
                break
            else:
                cnt+=1
                
df_scores['sentiment'] = sentiment

@app.route("/")
def index():
    return df_scores.to_html()    
 
if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple('localhost', 9000, app)

