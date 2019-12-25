
# coding: utf-8



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
import logging
from sklearn import linear_model

__logger = logging.getLogger(__name__)

node_data = {}
def GetNodeData():
    return node_data

edge_data = {}
def GetEdgeData():
    return edge_data    

def generateDiGraph(node_ids, edge_data):
    # Generate network graph
    MG = nx.MultiDiGraph()

    for n in node_ids:
        MG.add_node(n)

    for edge in edge_data:
        MG.add_edge(edge_data[edge]['source'], edge_data[edge]['dest'], key=edge_data[edge]['id'])

    G = nx.DiGraph()
    for (u, v) in MG.edges():
        G.add_edge(u, v, weight=len(MG[u][v]))
    return G            

def calculate_authority(G):
    hubs, authorities = nx.hits(G)
    return authorities
      

def generateUserAttributes(year, month):
    global node_data
    global edge_data
    
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
    
    #attribute_list = ['n_tweet', 'n_stock_tweet', 'n_sentiment_tweet', 'statuses_count', 'followers_count', 'friends_count',
    #             'authority_score', 'reputation_score']
    
    with open(os.path.join(path, "id_list.txt" )) as id_list:
        reader = id_list.readlines()
        user_attributes = {int(node_id.strip()):{ 'n_tweet':0, 'n_stock_tweet':0, 'n_sentiment_tweet':0, 
					'statuses_count':0, 'followers_count':0, 'friends_count':0,
                 			'authority':0, 'reputation':0} 
					for node_id in reader}

    tweetpath = os.path.join(path, "StockRelatedTweets", year, month)
    #node_ids = []
    #edge_data = []

    for dirPath, dirNames, fileNames in os.walk(tweetpath):
            for file in fileNames:
                if file.endswith(".json"):    
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
                                        if tweet['user']['id'] in user_attributes:
                                            idIndex = tweet['user']['id']
                                        else:
                                            continue
                                    else:
                                        continue

                                    if not tweet['user']['id'] in node_data:
                                        node_data[tweet['user']['id']] = {'info':tweet['user']}



                                    # Update statuses_count
                                    if tweet['user']['statuses_count'] > user_attributes[idIndex]['statuses_count']:
                                        user_attributes[idIndex]['statuses_count'] = tweet['user']['statuses_count']
                                    # Update followers_count
                                    if tweet['user']['followers_count'] > user_attributes[idIndex]['followers_count']:
                                        user_attributes[idIndex]['followers_count'] = tweet['user']['followers_count']
                                    # Update friends_count
                                    if tweet['user']['friends_count'] > user_attributes[idIndex]['friends_count']:
                                        user_attributes[idIndex]['friends_count'] = tweet['user']['friends_count']

                                    if 'quoted_status' in tweet:
                                        #if not tweet['user']['id'] in node_ids:
                                        #    node_ids.append(tweet['user']['id'])
                                        if not tweet['quoted_status']['user']['id'] in node_data:
                                            node_data[tweet['quoted_status']['user']['id']] = {'info':tweet['quoted_status']['user']}
                                        
                                        edge_data[len(edge_data)] = {'source':tweet['user']['id'], 'dest': tweet['quoted_status']['user']['id'], 'edge_type': 'quote' , 'id': tweet['id']}

                                    if 'retweeted_status' in tweet:
                                        #if not tweet['user']['id'] in node_ids:
                                        #    node_ids.append(tweet['user']['id'])
                                        if not tweet['retweeted_status']['user']['id'] in node_data:
                                            node_data[tweet['retweeted_status']['user']['id']] = {'info':tweet['retweeted_status']['user']}
                    
                                        edge_data[len(edge_data)] = {'source':tweet['user']['id'], 'dest': tweet['retweeted_status']['user']['id'], 'edge_type': 'retweet' , 'id': tweet['id']}

                                    user_attributes[idIndex]['n_tweet']+=1     #Number of all tweets plus 1
                                    tweet_lower = tweet['text'].lower()
                                    company_index = -1
                                    for company in company_list:
                                        company_index+=1
                                        company_tag = ' $' + company + ' '
                                        if company_tag.lower() in tweet_lower:
                                            user_attributes[idIndex]['n_stock_tweet']+=1     #Number of stock-related tweets plus 1
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
                                                user_attributes[idIndex]['n_sentiment_tweet']+=1    #Number of sentiment-related tweets plus 1
                                            break

    G = generateDiGraph(node_data.keys(), edge_data)

    hubs, authority_scores = nx.hits(G, max_iter=2000, tol=1.0e-6 )
    for node_id, value in authority_scores.items():
        if node_id in user_attributes:            
            user_attributes[node_id]['authority'] = value*10**18

    reputation_scores = nx.pagerank(G)
    for node_id, value in reputation_scores.items():
        if node_id in user_attributes:
            user_attributes[node_id]['reputation'] = value

    #arr = np.array(user_attributes)
    #outputpath = os.path.join(path, "results", year, month)
    #savepath = os.path.join(outputpath,'user_attributes_' + year + '_' + month + '.csv' )
    #attributes = ','.join(attribute_list)
    #np.savetxt(savepath, arr, header=attributes, delimiter=',', comments='')
    return user_attributes


#Preprocess and generate weighting for sentiments by users

def preprocessing(user_attributes, year, month):
    path = os.path.join("data")
    #outputpath = os.path.join(path, "results", year, month)
    with open(os.path.join(path, "id_list.txt" )) as id_list:
        reader = id_list.readlines()
        scores =  {int(node_id.strip()):{ 'expertise':0, 'authority':0, 'reputation':0, 'experience':0} 
					for node_id in reader}

    #preprocessedATT = []
    
    for node_id, row in user_attributes.items():
        tempATT = { 'expertise':0, 'authority':0, 'reputation':0, 'experience':0}
        if(row['n_tweet']!=0):
            tempATT['expertise'] = float(row['n_stock_tweet'])/float(row['n_tweet']) #expertise

        tempATT['authority'] = row['authority']

        tempATT['reputation'] = row['reputation']

        scores[node_id] = tempATT
        
    avg_expertise = np.mean([scores[node_id]['expertise'] for node_id in scores.keys()])

    for node_id in scores.keys():
        scores[node_id]['experience'] = 1 - abs(avg_expertise - scores[node_id]['expertise']) #experience
        
    #arr = np.array(scores)
    #savepath = os.path.join(outputpath,'trust_scores_'+ year + '_' + month + '.csv' )
    #filter_names = 'expertise, authority, reputation, experience'
    #np.savetxt(savepath, arr, header=filter_names, delimiter=',', comments='')
    return scores

def generateTrustScores(year, month):
    attributes = generateUserAttributes(year, month)
    scores = preprocessing(attributes, year, month)
    __logger.info("Trust Scores Generated.")
    #1 min
    return scores

if __name__ == "__main__":
    scores = generateTrustScores(sys.argv[1],sys.argv[2])
    print json.dumps(scores, indent = 4)
    #print json.dumps(GetEdgeData(), indent = 4)
    #print json.dumps(GetNodeData(), indent = 4)

