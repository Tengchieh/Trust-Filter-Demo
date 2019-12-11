
# coding: utf-8


import generateSentiment
import generateTrustScores
import runPrediction


def dateProcessing(start_year, start_month, end_year, end_month, filter_name):
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
            
            generateSentiment(cur_year, month)
            generateTrustScores(cur_year, month)
    
    runPrediction(start_year, start_month, end_year, end_month, filter_name)

if __name__ == "__main__":
    #trust filter selection: expertise, experience, authority, reputation or simple_accumulation
    trust_filter = "expertise"
    dateProcessing("2015","11","2015","12", trust_filter)
    

