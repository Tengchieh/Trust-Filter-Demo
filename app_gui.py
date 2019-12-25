import Tkinter as tk
import ttk
import os
import csv
import pandas as pd
#import pandastable as pdtable
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from stockPrediction import ROIProcessing, dateProcessing

path = os.path.join("data")

### Generate Company list for selection.
company_list = []
with open(os.path.join(path,"SP500.csv")) as SP500csv:
    reader = csv.DictReader(SP500csv)
    for row in reader:
        company_list.append(row['Symbol'])
### Generate user_id list
user_ids = []        
with open(os.path.join(path, "id_list.txt" )) as id_list:
        reader = id_list.readlines()
        for row in reader:
            user_ids.append(row)
        
window = tk.Tk()

window.title("Stock Prediction")
window.geometry('1024x960')
window.configure(background='white')

label1 = tk.Label(window, text = "Select Interval of Tracking (Begin Month)/(Begin Year) to (End Month)/(End Year).").grid(row=0,columnspan=4)

### Add Scrollbar
#scrollbar = tk.Scrollbar(window)
#scrollbar.grid(row= 10, column=15, sticky="ns")

### Set begin year/month
start_year = tk.StringVar()
start_month = tk.StringVar()
label_begin_year = tk.Label(window, text = "Begin year:").grid(row=1,sticky=tk.W)
combo_begin_year = ttk.Combobox(window, values = ["2015"], textvariable=start_year)
combo_begin_year.grid(column=1, row=1,sticky=tk.W)
combo_begin_year.current(0)
#combo_begin_year.bind(("<<ComboboxSelected>>", bindBeginYear)
label_begin_month = tk.Label(window, text = "Begin month:").grid(row=1, column=2)
combo_begin_month = ttk.Combobox(window, values = ["11", "12"], textvariable=start_month)
combo_begin_month.grid(column=3, row=1,sticky=tk.W)
combo_begin_month.current(0)

### Set end year/month
end_year = tk.StringVar()
end_month = tk.StringVar()
label_end_year = tk.Label(window, text = "End year:").grid(row=2,sticky=tk.W)
combo_end_year = ttk.Combobox(window, values = ["2015"], textvariable=end_year)
combo_end_year.grid(column=1, row=2,sticky=tk.W)
combo_end_year.current(0)
#combo_begin_year.bind(("<<ComboboxSelected>>", bindBeginYear)
label_end_month = tk.Label(window, text = "End month:").grid(row=2, column=2)
combo_end_month = ttk.Combobox(window, values = ["11", "12"], textvariable=end_month)
combo_end_month.grid(column=3, row=2,sticky=tk.W)
combo_end_month.current(0)

### Set Applied Filter
trust_filter = tk.StringVar()
label_filter = tk.Label(window, text = "Applied Filter:").grid(row=3,sticky=tk.W)
combo_filter = ttk.Combobox(window, values = 
                ["expertise", "experience", "authority", "reputation"], 
                textvariable=trust_filter)
combo_filter.grid(column=1, row=3,sticky=tk.W)
combo_filter.current(0)

### Calculate Button
def calculate():
    roi = ROIProcessing(start_year.get(), start_month.get(), 
                        end_year.get(), end_month.get(), trust_filter.get())
    row_draw = 5
    col_draw = 0
    draw_stock_prediction(row_draw, col_draw, roi)

    
button1 = tk.Button(window, text='Calculate', command=calculate)
button1.grid(row=4, column=2)

def draw_stock_prediction(row0, col0, roi):
    roi_total = roi.T
    roi_total['day'] = [str(d) for d in range(1,len(roi_total.index)+1)]

    # Add a FigureCanvasTkAgg in that frame
    figure = Figure(figsize=(5,5), dpi=100)
    ax = figure.add_subplot(111)
    roi_total.plot.line(x='day', y='Total')
    plt.ylabel(' ROI (Dollars)')
    plt.title("Return on Investment from %s-%s to %s-%s usgin %s filter" 
    %(start_year.get() ,start_month.get() ,end_year.get() ,end_month.get() ,trust_filter.get()))
    plt.show()
    
    return

### Second Stage - for showing table
#abelspace = tk.Label(window, text = "").grid(row=5)
label2 = tk.Label(window, text = "Select Target Date to Show the Sentiments.").grid(row=6,columnspan=4)
### Set year/month/day
year = tk.StringVar()
month = tk.StringVar()
day = tk.StringVar()
company = tk.StringVar()

label_year = tk.Label(window, text = "Targeted year:").grid(row=7,sticky=tk.W)
combo_year = ttk.Combobox(window, values = ["2015"], textvariable=year)
combo_year.grid(column=1, row=7,sticky=tk.W)
combo_year.current(0)
label_month = tk.Label(window, text = "Targeted month:").grid(row=7, column=2)
combo_month = ttk.Combobox(window, values = ["11", "12"], textvariable=month)
combo_month.grid(column=3, row=7,sticky=tk.W)
combo_month.current(0)
label_day = tk.Label(window, text = "Targeted day:").grid(row=8,sticky=tk.W)
combo_day = ttk.Combobox(window, values = [str(x) for x in range(1,32)], textvariable=day)
combo_day.grid(column=1, row=8,sticky=tk.W)
combo_day.current(0)
label_com = tk.Label(window, text = "Targeted company:").grid(row=8, column=2)
combo_com = ttk.Combobox(window, values = company_list, textvariable=company)
combo_com.grid(column=3, row=8,sticky=tk.W)
combo_com.current(0)
### Calculate Button
def Select():
    scores = dateProcessing(year.get(), month.get(), 
                        day.get(), company.get(), trust_filter.get())
    #print scores                        
    col_table = 0
    row_table = 10
    
    show_table_with_scrollbar(scores, row_table, col_table)
    return

button2 = tk.Button(window, text='Select', command=Select)
button2.grid(row=9, column=2)

def show_table_with_scrollbar(scores, row0, col0):
    # Create a frame for the canvas with non-zero row&column weights
    frame_canvas = tk.Frame(window)
    frame_canvas.grid(row=row0, column=col0, columnspan=4, pady=(5, 0), sticky='nw')
    frame_canvas.grid_rowconfigure(0, weight=1)
    frame_canvas.grid_columnconfigure(0, weight=1)
    # Set grid_propagate to False to allow 5-by-5 buttons resizing later
    frame_canvas.grid_propagate(False)

    # Add a canvas in that frame
    canvas = tk.Canvas(frame_canvas, bg="white")
    canvas.grid(row=0, column=0, sticky="news")

    # Link a scrollbar to the canvas
    vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
    vsb.grid(row=0, column=1, sticky='ns')
    canvas.configure(yscrollcommand=vsb.set)

    # Create a frame to contain the table
    frame_table = tk.Frame(canvas, bg="blue")
    canvas.create_window((0, 0), window=frame_table, anchor='nw')

    # Add scores table to the frame
    row = 0
    col = 0    
    for user_id in scores.keys():
        row += 1        
        label_id = tk.Label(frame_table, text = user_id, borderwidth=0, width=10)
        label_id.grid(row = row, column = col, sticky="nsew", padx=1, pady=1)
        
    row = 0
    filter_list = ['expertise', 'experience', 'reputation', 'authority', 'Sentiments', 'Weighted Sentiments']
    label_id = tk.Label(frame_table, text = 'user_id', borderwidth=0, width=13)
    label_id.grid(row = row, column = col, sticky="nsew", padx=1, pady=1)
    
    for filter_name in filter_list:
        col += 1
        label_filter = tk.Label(frame_table, text = filter_name, borderwidth=0, width=13)
        label_filter.grid(row = row, column = col, sticky="nsew", padx=1, pady=1)
    
    for user_id in scores.keys():
        col = 0
        row += 1
        for filter_name in filter_list:
            col += 1
            label_score = tk.Label(frame_table, text = round(scores[user_id][filter_name],4), borderwidth=0, width=13)
            label_score.grid(row = row, column = col, sticky="nsew", padx=1, pady=1)       
    # Update table frames idle tasks to let tkinter calculate buttons sizes
    frame_table.update_idletasks()

    # Resize the canvas frame to show exactly table size and the scrollbar
    columns_width = 750
    rows_height = 500
    frame_canvas.config(width=columns_width + vsb.winfo_width(),
                    height=rows_height)

    # Set the canvas scrolling region
    canvas.config(scrollregion=canvas.bbox("all"))
    return

window.mainloop()
