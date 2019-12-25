
# coding: utf-8


from generateSentiment import generateSentiment
from generateTrustScores import generateTrustScores, GetNodeData, GetEdgeData
from runPrediction import runPrediction


scores = {}
acc_sentiments = {}

def ROIProcessing(start_year, start_month, end_year, end_month, filter_name):
    global scores
    global acc_sentiments
    
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
        
        for month_int in range(first_month, last_month+1):
            if(month_int<10):
                month = '0'+ str(month_int)
            else:
                month = str(month_int)
                
            acc_sentiments_onemonth = generateSentiment(cur_year, month)

            if not acc_sentiments:
                acc_sentiments.update(acc_sentiments_onemonth)
            elif cur_year not in acc_sentiments.itervalues().next().itervalues().next():
                for user_node in acc_sentiments:
                    for company in acc_sentiments[user_node]:
                        acc_sentiments[user_node][company][cur_year] = acc_sentiments_onemonth[user_node][company][cur_year]
            else:
                for user_node in acc_sentiments:
                    for company in acc_sentiments[user_node]:
                        acc_sentiments[user_node][company][cur_year][month] = acc_sentiments_onemonth[user_node][company][cur_year][month]
                
            scores_onemonth = generateTrustScores(cur_year, month)
            
            if not scores:
                scores = {cur_year: {month: scores_onemonth} }
            elif cur_year not in scores:
                scores[cur_year] = {month: scores_onemonth}
            else:
                scores[cur_year][month] = scores_onemonth
    
    roi = runPrediction(start_year, start_month, end_year, end_month, filter_name, acc_sentiments, scores)
    
    return roi

def dateProcessing(target_year, target_month, target_day, company, filter_name):
    global scores
    global acc_sentiments
    
    combined = scores[target_year][target_month]
    for user_id in combined:
        combined[user_id]['Sentiments'] = acc_sentiments[user_id][company][target_year][target_month][int(target_day)]
        combined[user_id]['Weighted Sentiments'] = combined[user_id]['Sentiments'] * combined[user_id][filter_name]
    return combined
    
if __name__ == "__main__":
    #trust filter selection: expertise, experience, authority, reputation or simple_accumulation
    trust_filter = "expertise"
    roi = ROIProcessing("2015","11","2015","12", trust_filter)
    company = "SPY"
    combined_scores = dateProcessing("2015", "11", "13", company, trust_filter)
    
    print roi
    print combined_scores
    
    

