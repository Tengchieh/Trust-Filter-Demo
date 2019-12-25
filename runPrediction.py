
# coding: utf-8

import sys 
import csv
import os
from datetime import datetime
from datetime import timedelta
import numpy as np
import logging
import pandas as pd

__logger = logging.getLogger(__name__)

path = os.path.join("data")

#Retrieve stock price for a particular day
def retrieveStockPrice(company):
    stock_file = os.path.join(path, "SandP500_stock", company + "_data.csv")
    with open(stock_file) as stockfile:
        stockprice = {}
        reader = csv.DictReader(stockfile)
        for row in reader:
            if 'open' in row:
                if row["open"] and row['close']:
                    stockprice[row['date']] = round((float(row["open"]) + float(row['close'])) / 2, 5)
            else:
                if row["Open"] and row['Close']:
                    stockprice[row['Date']] = round((float(row["Open"]) + float(row['Close'])) / 2, 5)
    return stockprice

#Retriev accumulated sentiment and compare with actual stock price
company_list = []
with open(os.path.join(path, 'SP500.csv')) as SP500csv:
    reader = csv.DictReader(SP500csv)
    for row in reader:
        company_list.append(row['Symbol'])

def transformwithSlash(date):
    if date.month < 10:
        date_string_month = str(date.year) + '-0' + str(date.month)                    
    else:
        date_string_month = str(date.year) + '-' + str(date.month)
    
    if date.day < 10:
        date_string = str(date_string_month) +  '-0' + str(date.day)
    else:
        date_string = str(date_string_month) +  '-' + str(date.day)       
    return date_string

def lenofDay(start_year, start_month, end_year, end_month):
    if end_month=='12':
        len_day = (datetime(int(end_year)+1,1,1)-datetime(int(start_year),int(start_month),1)).days
    else:
        len_day = (datetime(int(end_year),int(end_month)+1,1)-datetime(int(start_year),int(start_month),1)).days
    return len_day

def runROI(start_year, start_month, end_year, end_month, filter_name, sentiment_alltime):
    len_day = lenofDay(start_year, start_month, end_year, end_month)
    n_company = len(company_list)
    ROI_history = [0] * n_company
    for i in range(n_company):
        ROI_history[i] = [0] * len_day

    currHoldDict = {company:0  for company in company_list }
    
    total_investment = [0] * len_day  #Record daily # of invested company, to find maximum money required.
    
    for year_int in range(int(start_year), int(end_year)+1):
        if (year_int == int(end_year)):
            last_month = int(end_month)            
        else:
            last_month = 12
        if(year_int == int(start_year)):
            first_month = int(start_month)
        else:
            first_month = 1
            
        start_date = datetime(year_int, first_month, 1)
    
        for single_month in (start_date.replace(month=n) for n in range(first_month, last_month + 1)):
            year = str(single_month.year)
            if single_month.month < 10:
                month = '0' + str(single_month.month)
            else:
                month = str(single_month.month)
                
            #sentimentpath = os.path.join(path, "results", year, month, "User_Sentiment")
            offset = (datetime(single_month.year, single_month.month, 1) - datetime(int(start_year), int(start_month), 1)).days

            #For weekly
            #with open(os.path.join( path, 'acc_weekly_sentiment_' + year + '_' + month + '_ALL_' + filter_name + '.csv')) as accSentiment:
            #with open(os.path.join( sentimentpath, 'acc_sentiment_' + year + '_' + month + '_ALL_' + filter_name + '.csv')) as accSentiment:
            #    reader = csv.DictReader(accSentiment)
            #    company_idx = 0
            acc_Sentiment = sentiment_alltime[year][month]
            #print acc_Sentiment
            
            #for acc_Sentiment in reader:
            for company in company_list:
                currHold = currHoldDict[company]
                company_idx = company_list.index(company)
                #company = company_list[company_idx]

                avg_price = retrieveStockPrice(company) 
                #Find first workday in the month.
                findworkday = single_month
                findwd_string = transformwithSlash(findworkday)
                while findwd_string not in avg_price:
                    findworkday += timedelta(days=1)
                    findwd_string = transformwithSlash(findworkday)
                previousPrice = avg_price[findwd_string]
                #Add for hold 100 dollars for each stock at the begining.
                if offset == 0:
                    currHold = 100 / previousPrice

                sumSentiment = 0

                if offset > 0:   #To add last month's ROI.
                    ROI_history[company_idx][offset] = round(ROI_history[company_idx][offset-1], 5)

                for day in range(1, len(acc_Sentiment.index)+1):
                    next_date = datetime(int(year), int(month), day) + timedelta(days=1)  #Buy stock 1 day after
                    #date =  str(int(month)) + '/' + str(day) + '/' + year
                    sumSentiment += float(acc_Sentiment.loc[day, company])

                    next_date_string = transformwithSlash(next_date)

                    if next_date_string in avg_price:
                        nextdayPrice = avg_price[next_date_string]                
                        if sumSentiment > 0:
                            if currHold == 0:
                                currHold = 100 / nextdayPrice
                                previousPrice = avg_price[next_date_string]
                        elif sumSentiment < 0:
                            if currHold:
                                currHold = 0

                        if currHold > 0:       
                            ROI_history[company_idx][day + offset -1] = round(ROI_history[company_idx][day + offset-2] +
                                                                             (nextdayPrice-previousPrice)*currHold , 5)
                            total_investment[day + offset -1] += 1
                        else:
                            ROI_history[company_idx][day + offset -1] = round(ROI_history[company_idx][day + offset-2], 5)

                        previousPrice = nextdayPrice #Save stock price for next iteration
                        sumSentiment = 0 #Reset sentiment
                    else:
                        ROI_history[company_idx][day + offset - 1] = round(ROI_history[company_idx][day + offset-2], 5)

                currHoldDict[company]=currHold
                #company_idx+=1 #Predict next stock
    #print ('Maximum companies invested in one day: ', max(total_investment))
    
    #arr = np.array(ROI_history)
    #For weekly
    #savepath = os.path.join("Extra_Storage", source_dir, end_year, start_year + start_month + '_to_' + end_year + end_month + '_' + filter_name + '_weekly.csv')
    #For daily
    #BuyZeroatBegin
    #savepath = os.path.join("Extra_Storage", source_dir, end_year, start_year + start_month + '_to_' + end_year + end_month + '_' + filter_name + '_BuyZeroatBegin_Meaningcloud.csv')
    #Buy100atBegin
    #savepath = os.path.join(path, "results", start_year + start_month + '_to_' + end_year + end_month + '_' + filter_name + '_BuyAllatBegin.csv')
    #np.savetxt(savepath, arr, fmt='%1.5f', delimiter=',')
    #addDateTag(savepath, start_year, start_month, end_year, end_month)
   
    pd_ROI_history = pd.DataFrame(ROI_history, index = company_list, columns = [x for x in range(1,len_day+1)])
    pd_ROI_history.loc['Total',:]= pd_ROI_history.sum(axis=0)
        
    return pd_ROI_history

def runSentiment(acc_sentiments, user_id, year, month):
    #sentimentpath = os.path.join(path, "results", year, month, "User_Sentiment")
    #file =os.path.join(sentimentpath, 'acc_sentiment_' + year + '_' + month + '_' + user_id + '.csv' )
    #sentiment = np.genfromtxt(file, delimiter=',', skip_header=1)
    
    #transform multiple-layered dict "acc_sentiments" to two layers
    
    acc_sentiments_twolayer = {company:{date: acc_sentiments[user_id][company][year][month][date] for date in acc_sentiments[user_id][company][year][month]} 
                                                                                    for company in acc_sentiments[user_id]}
    sentiment = pd.DataFrame(acc_sentiments_twolayer)                                                                                
    return sentiment

def runWeeklySentiment(user_id, year, month):
    sentimentpath = os.path.join(path, "results", year, month, "User_Sentiment")
    file =os.path.join(sentimentpath, 'acc_sentiment_' + year + '_' + month + '_' + user_id + '.csv' )
    sentiment = np.genfromtxt(file, delimiter=',', skip_header=1)
    
    weeklysentiment = []
    singlecompany_sentiment = []
    for row in sentiment:
            for i in range(len(row)):
                temp = 0
                if i < 7:
                    for idx in range(i+1):
                        temp += row[idx]
                    singlecompany_sentiment.append(temp)
                else:
                    for idx in range(i-6, i+1):
                        temp += row[idx]
                    singlecompany_sentiment.append(temp)
            
            weeklysentiment.append(singlecompany_sentiment)
            singlecompany_sentiment = []
    ans = np.asarray(weeklysentiment)
    return ans

def addDateTag(roipath, start_year, start_month, end_year, end_month):
    #Generate dates
    dates = []
    date = datetime(int(start_year), int(start_month), 1)
    if end_month == '12':
        end_date = datetime(int(end_year)+1, 1, 1)
    else:
        end_date = datetime(int(end_year), int(end_month)+1, 1)
    for delta in range((end_date-date).days):
        day = date + timedelta(days = delta)
        dates.append( "%s/%s/%s" % ({day.month}, {day.day}, {day.year}) ) 

    with open(roipath) as outcsv:
        r = csv.reader(outcsv)
        data = [line for line in r]
    with open(roipath, 'w', newline='') as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(dates)
        writer.writerows(data)

def accumulateUserSentiments(start_year, start_month, end_year, end_month, filter_name, acc_sentiments, scores):
    sentiment_alltime = {}
    for year_int in range(int(start_year), int(end_year)+1):
        if (year_int == int(end_year)):
            last_month = int(end_month)            
        else:
            last_month = 12
        if(year_int == int(start_year)):
            first_month = int(start_month)
        else:
            first_month = 1
        cur_year = str(year_int)
        
        sentiment_alltime[cur_year] = {}
        
        for month_int in range(first_month, last_month+1):
            if(month_int<10):
                month = '0'+ str(month_int)
            else:
                month = str(month_int)
            
            #outputpath = os.path.join(path, "results", cur_year, month)
            #openfile = None
            #if("predicted_scores" in filter_name):
            #    openfile = os.path.join(outputpath, filter_name + ".csv" )
            #elif not("simple_accumulation" in filter_name):
            #    openfile = os.path.join(outputpath, "trust_scores_"+ cur_year + "_" + month + ".csv" )
            #    
            #try:
            #    trust_scores = open(openfile)
            #    reader = csv.DictReader(trust_scores)
            #    scores = []
            #
            #    for x in reader:
            #        if(filter_name == 'authority'):
            #            scores.append([float(x[filter_name + "_score"])*10**18])
            #        elif("predicted_scores" in filter_name):
            #            scores.append([float(x['combined_score'])])
            #        else:
            #            scores.append([float(x[filter_name + "_score"])])
            #except:
            #    pass                
            #
            with open(os.path.join(path, "id_list.txt" )) as id_list:
                reader = id_list.readlines()
                idList = [int(x.strip()) for x in reader]
                len_day = lenofDay(cur_year, month, cur_year, month)
                sentiment_all = pd.DataFrame(np.zeros((len_day,len(company_list))), columns=company_list, index = [x for x in range(1,len_day+1)])

            #    
            #    if("simple_accumulation" in filter_name):
            #        scores = np.ones((len(idList),1))
            #        
            
       
            
            for user_id in idList:
                cur_score = scores[cur_year][month][int(user_id)][filter_name]
                cur_sentiment = runSentiment(acc_sentiments, int(user_id), cur_year, month)
                #print cur_score
                #print cur_sentiment
                sentiment_all += cur_score*cur_sentiment
                #acc_sentiment += ratio*runWeeklySentiment(user_id, path, cur_year, month) #From daily to weekly sentiment
                
            sentiment_alltime[cur_year][month] = sentiment_all
            #print sentiment_alltime
            
            #For daily
            #savepath = os.path.join(outputpath, 'User_Sentiment', "acc_sentiment_" + cur_year + "_" + month + "_ALL_" + filter_name + ".csv" )
            #For weekly
            #savepath = os.path.join(path, 'User_Sentiment', "acc_weekly_sentiment_" + cur_year + "_" + month + "_ALL_" + filter_name + ".csv" )
            #np.savetxt(savepath, acc_sentiment, fmt='%1.5f', delimiter=',')
            #addDateTag(savepath, cur_year, month, cur_year, month)
    return sentiment_alltime
            
    
def runPrediction(year_start, month_start, year_end, month_end, filter_name, acc_sentiments, scores):
        #accumulateUserSentiments('2015', '11', '2015', '12', "simple_accumulation" )
        acc_sentiment_all = accumulateUserSentiments(year_start, month_start, year_end, month_end, filter_name, acc_sentiments, scores)
        roi = runROI(year_start, month_start, year_end, month_end, filter_name, acc_sentiment_all)
        #runROI('2015', '11', '2015', '12', "simple_accumulation")        
        #runROI('2015', '11', '2016', '04', "buyandhold")
        __logger.info("Prediction using %s is done." %filter_name)
        # 2-3 min for one month & one filter
        return roi
    

