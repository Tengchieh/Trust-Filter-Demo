
# coding: utf-8

# In[11]:


import sys
import os
import json
import string
import pprint
import csv
import re
from datetime import datetime
import math
import numpy as np
from calendar import monthrange


def sentiment(year, month):
    #Scan through stock related tweets and derive sentiments by each user.

    path = os.path.join("data")
    outputpath_year = os.path.join(path, "results", year)
    outputpath = os.path.join(outputpath_year, month)
    sentimentpath = os.path.join(outputpath, "User_Sentiment")
    
    try:
        os.mkdir(outputpath_year)    
    except:
        print("%s has been created." %outputpath_year)
    try:
        os.mkdir(outputpath)        
    except:
        print("%s has been created." %outputpath)
    try:
        os.mkdir(sentimentpath)
    except:
        print("%s has been established." %sentimentpath)

    company_list = []
    with open(os.path.join(path,"SP500.csv")) as SP500csv:
        reader = csv.DictReader(SP500csv)
        for row in reader:
            company_list.append(row['Symbol'])

    buy_keywords = []
    sell_keywords = []
    with open(os.path.join(path,"keyword.csv")) as keyword:
        reader = csv.DictReader(keyword)
        for row in reader:
            buy_keywords.append(row['Buy'])
            if row['Sell']:
                sell_keywords.append(row['Sell'])
        
    #Create sentiment accumulation for different dates
    day = monthrange(int(year), int(month))[1]
    n_company = len(company_list)
    acc_sentiment = [0] * n_company
    for i in range(n_company):
        acc_sentiment[i] = [0] * day
    
    arr = np.array(acc_sentiment)

    #Initialize acc_sentiment files.
    with open(os.path.join(path, "id_list.txt" )) as id_list:
        reader = id_list.readlines()
        idList = [x.strip() for x in reader]
        n_authors = len(idList)
        for user in idList:
            np.savetxt(os.path.join(sentimentpath, 'acc_sentiment_' + year + '_' + month + '_' + user + '.csv'), arr, fmt='%i', delimiter=',')

    #Scan through all tweets and apply sentiment analysis. 
    #Accumulate all users' sentiment toward a company in a single day. Generate ACC_Sentiment of each users.
    tweetpath = os.path.join(path, "StockRelatedTweets", year, month)
    for dirPath, dirNames, fileNames in os.walk(tweetpath):
        for file in fileNames:
            if file.endswith("json"):
                filepath = os.path.join(dirPath, file)
                with open(filepath) as json_data:
                    data=[]
                    for line in json_data:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                    for tweet in data:
                        if tweet['user']['id'] not in idList:
                            continue

                        if 'text' in tweet:
                            tweet_lower = tweet['text'].lower()
                            company_index = -1
                            for company in company_list:
                                company_index+=1
                                company_tag = ' $' + company + ' '
                                if company_tag.lower() in tweet_lower:
                                    sentiment = 0
                                    for buy_keyword in buy_keywords:
                                        if buy_keyword in tweet_lower:
                                            sentiment+=1
                                    for sell_keyword in sell_keywords:
                                        if sell_keyword in tweet_lower:
                                            sentiment-=1
                                    if sentiment==0:
                                        break
                                    else:
                                        if 'created_at' in tweet:
                                            second = (datetime.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +%f %Y')- datetime(int(year), int(month), 1)).total_seconds()
                                            date = math.ceil(second/86400) - 1            
                                        else:
                                            break
                                            
                                        user_sentiment_file = os.path.join(sentimentpath, "acc_sentiment_" + year + "_" + month + "_" + str(tweet['user']['id']) + ".csv")
                                        user_sentiment = np.genfromtxt(user_sentiment_file, delimiter=',')
                                        if date ==  user_sentiment.shape[1]:
                                            date -= 1
                                        if sentiment > 0:
                                            user_sentiment[company_index][date]+=1
                                        else:
                                            user_sentiment[company_index][date]-=1
                                        
                                        arr = np.array(user_sentiment)
                                        
                                        np.savetxt(user_sentiment_file, arr, fmt='%i', delimiter=',')                                    

    #Generate dates
    dates = []
    for thedate in range(1, day+1):
        dates.append(month + '/'+ str(thedate) + '/' + year)
    
    for dirPath, dirNames, fileNames in os.walk(sentimentpath):
        for file in fileNames:
            filepath = os.path.join(dirPath, file)
            with open(filepath) as outcsv:
                r = csv.reader(outcsv)
                data = [line for line in r]
            with open(filepath, 'w', newline='') as outcsv:
                writer = csv.writer(outcsv)
                writer.writerow(dates)
                writer.writerows(data)
                
def initialize():
    path = os.path.join("data", "results")
    try:
        os.mkdir(path)
    except:
        print("%s has been established." %path)

        
def generateSentiment(year, month):
    initialize()
    sentiment(year, month) 
    print("User Sentiment Generated.")
    #2minutes

