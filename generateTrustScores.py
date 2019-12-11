
# coding: utf-8

# In[2]:


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
import networkx as nx

def generateDiGraph(node_ids, edge_data):
    # Generate network graph
    MG = nx.MultiDiGraph()

    for n in node_ids:
        MG.add_node(n)

    for d in edge_data:
        MG.add_edge(d['source'], d['dest'], key=d['post_id'])

    G = nx.DiGraph()
    for (u, v) in MG.edges():
        G.add_edge(u, v, weight=len(MG[u][v]))
    return G            

def calculate_authority(G):
    hubs, authorities = nx.hits(G)
    return authorities
      

def generateUserAttributes(year, month):
    
    path = os.path.join("data")
    
    company_list = []
    id_list = []
    with open(os.path.join(path, 'SP500.csv')) as SP500csv:
        reader = csv.DictReader(SP500csv)
        for row in reader:
            company_list.append(row['Symbol'])

    buy_keywords = []
    sell_keywords = []
    with open(os.path.join(path, 'keyword.csv')) as keyword:
        reader = csv.DictReader(keyword)
        for row in reader:
            buy_keywords.append(row['Buy'])
            if row['Sell']:
                sell_keywords.append(row['Sell'])
    
    attribute_list = ['n_tweet', 'n_stock_tweet', 'n_sentiment_tweet', 'statuses_count', 'followers_count', 'friends_count',
                 'authority_score', 'reputation_score']
    n_attributes = len(attribute_list)
    
    with open(os.path.join(path, "id_list.txt" )) as id_list:
        reader = id_list.readlines()
        idList = [x.strip() for x in reader]
        n_authors = len(idList)
        user_attributes = [0] * n_authors
        for i in range(n_authors):
            user_attributes[i] = [0] * n_attributes

    tweetpath = os.path.join(path, "StockRelatedTweets", year, month)
    node_ids = []
    edge_data = []

    for dirPath, dirNames, fileNames in os.walk(tweetpath):
            for file in fileNames:
                if file.endswith(".json"):    
                        #print(file)
                        filepath = os.path.join(dirPath, file)
                        with open(filepath) as json_data:
                            data=[]
                            for line in json_data:
                                try:
                                    data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    continue
                            for tweet in data:
                                if 'text' in tweet:
                                    if 'user' in tweet:
                                        if tweet['user']['id'] in idList:
                                            idIndex = idList.index(str(tweet['user']['id']))
                                        else:
                                            continue
                                    else:
                                        continue

                                    # Update statuses_count
                                    if tweet['user']['statuses_count'] > user_attributes[idIndex][attribute_list.index('statuses_count')]:
                                        user_attributes[idIndex][attribute_list.index('statuses_count')] = tweet['user']['statuses_count']
                                    # Update followers_count
                                    if tweet['user']['followers_count'] > user_attributes[idIndex][attribute_list.index('followers_count')]:
                                        user_attributes[idIndex][attribute_list.index('followers_count')] = tweet['user']['followers_count']
                                    # Update friends_count
                                    if tweet['user']['friends_count'] > user_attributes[idIndex][attribute_list.index('friends_count')]:
                                        user_attributes[idIndex][attribute_list.index('friends_count')] = tweet['user']['friends_count']

                                    if 'quoted_status' in tweet:
                                        if not tweet['user']['id'] in node_ids:
                                            node_ids.append(tweet['user']['id'])
                                        if not tweet['quoted_status']['user']['id'] in node_ids:
                                            node_ids.append(tweet['quoted_status']['user']['id'])
                                        edge_data.append({'source':tweet['user']['id'], 'dest': tweet['quoted_status']['user']['id'], 'post_id': tweet['id']})
                                    if 'retweeted_status' in tweet:
                                        if not tweet['user']['id'] in node_ids:
                                            node_ids.append(tweet['user']['id'])
                                        if not tweet['retweeted_status']['user']['id'] in node_ids:
                                            node_ids.append(tweet['retweeted_status']['user']['id'])
                                        edge_data.append({'source':tweet['user']['id'], 'dest': tweet['retweeted_status']['user']['id'], 'post_id': tweet['id']})

                                    user_attributes[idIndex][attribute_list.index('n_tweet')]+=1     #Number of all tweets plus 1
                                    tweet_lower = tweet['text'].lower()
                                    company_index = -1
                                    for company in company_list:
                                        company_index+=1
                                        company_tag = ' $' + company + ' '
                                        if company_tag.lower() in tweet_lower:

                                            user_attributes[idIndex][attribute_list.index('n_stock_tweet')]+=1     #Number of stock-related tweets plus 1
                                            sentiment = False
                                            for buy_keyword in buy_keywords:
                                                if buy_keyword in tweet_lower:
                                                    sentiment = True
                                                    break
                                            for sell_keyword in sell_keywords:
                                                if sell_keyword in tweet_lower:
                                                    sentiment = True
                                                    break
                                            if sentiment:
                                                user_attributes[idIndex][attribute_list.index('n_sentiment_tweet')]+=1    #Number of sentiment-related tweets plus 1
                                            break

    G = generateDiGraph(node_ids, edge_data)

    hubs, authority_scores = nx.hits(G, max_iter=2000, tol=1.0e-6 )
    for node, value in authority_scores.items():
        if str(node) in idList:
            idIndex = idList.index(str(node))
            user_attributes[idIndex][attribute_list.index('authority_score')] = value

    reputation_scores = nx.pagerank(G)
    for node, value in reputation_scores.items():
        if str(node) in idList:
            idIndex = idList.index(str(node))
            user_attributes[idIndex][attribute_list.index('reputation_score')] = value

    arr = np.array(user_attributes)
    
    outputpath = os.path.join(path, "results", year, month)
    savepath = os.path.join(outputpath,'user_attributes_' + year + '_' + month + '.csv' )
    attributes = ','.join(attribute_list)
    np.savetxt(savepath, arr, header=attributes, delimiter=',')


# In[3]:


#Preprocess and generate weighting for sentiments by users
from sklearn import linear_model

def preprocessing(year, month):
    path = os.path.join("data")
    outputpath = os.path.join(path, "results", year, month)

    preprocessedATT = []
    with open(os.path.join(outputpath, "user_attributes_"+ year + "_" + month + ".csv" )) as tweet_attributes:
        reader = csv.DictReader(tweet_attributes)
        for row in reader:
            tempATT = []
            if(float(row['# n_tweet'])!=0):
                tempATT.append(float(row['n_stock_tweet'])/float(row['# n_tweet'])) #expertise
            else:
                tempATT.append(0)

            if(float(row['authority_score'])==0):
                tempATT.append(0)
            else:
                tempATT.append(float(row['authority_score']))
            if(float(row['reputation_score'])==0):
                tempATT.append(0)
            else:
                tempATT.append(float(row['reputation_score']))
            preprocessedATT.append(tempATT)
        
        avg_expertise = np.array(preprocessedATT).mean(axis=0)[0]
        for item in preprocessedATT:
            item.append(1-abs(avg_expertise - item[0])) #experience
        #for item in preprocessedATT:
        #    item[6] = item[6] + temp[6]
        #    item[7] = item[7] + temp[7]
        
    arr = np.array(preprocessedATT)
    savepath = os.path.join(outputpath,'trust_scores_'+ year + '_' + month + '.csv' )
    filter_names = 'expertise_score, authority_score, reputation_score, experience_score'
    np.savetxt(savepath, arr, header=filter_names, delimiter=',', comments='')
    #return arr

def generateTrustScores(year, month):
    generateUserAttributes(year, month)
    preprocessing(year, month)
    print("Trust Scores Generated.")
    #1 min

