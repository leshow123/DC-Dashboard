""" import plotly.express as px

fig = px.bar(x=["a", "b", "c", "d"], y=[1, 3, 2, 5])
#print(fig)
#fig.write_html('index.html', auto_open=True)

####### lower-level API ##########

import plotly.graph_objects as go
import numpy as np

N = 1000
t = np.linspace(0, 10, 100)
y = np.sin(t)
y_amp = y + 0.15
fig = go.Figure(data=[go.Scatter(x=t, y=y, mode='markers'), go.Scatter(x=t, y=y_amp, mode='markers')])
#fig.write_html('index2.html', auto_open=True)

####### lower-leverl API: Multiple Subplots with Titles #########

from plotly.subplots import make_subplots
#import plotly.graph_objects as go

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Plot 1", "Plot 2", "Plot 3", "Plot 4"))

fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]),
              row=1, col=1)

fig.add_trace(go.Scatter(x=[20, 30, 40], y=[50, 60, 70]),
              row=1, col=2)

fig.add_trace(go.Scatter(x=[300, 400, 500], y=[600, 700, 800]),
              row=2, col=1)

fig.add_trace(go.Scatter(x=t, y=y_amp, mode='markers'),
              row=2, col=2)

fig.update_layout(height=500, width=700,
                  title_text="Multiple Subplots with Titles")
fig.write_html('index.html', auto_open=True) """

import plotly.express as px
import plotly.io as pio
pio.templates
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
import pandas as pd
import datetime
from datetime import date, timedelta
import re

def cut(x):
    return x[:-3]

def format_date1(x):
    return datetime.datetime.strptime(x, "%Y-%m-%d %X").strftime("%Y-%m-%d")

#TODO Why not purchased_at inplace of subscriber_since?

# *** NEW SUBSCRIBERS OVER TIME *** 

# format new subscriptions data (using only subscriber_since data and grouping by date)
all_data_df = pd.read_csv("subscriptions.csv")
all_data_df = all_data_df.rename(columns={'subscriber_since': 'Date Purchased'})
new_subs_df = pd.DataFrame(all_data_df['Date Purchased'])
new_subs_df = new_subs_df.dropna(how = 'all')
new_subs_df["Date Purchased"] = new_subs_df["Date Purchased"].apply(cut)
new_subs_df["Date Purchased"] = new_subs_df["Date Purchased"].apply(format_date1)
num_new_subs = new_subs_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers').reset_index()
# Add a new column, 'Number of Subscribers (Trialers)'. Initialize entire column to 0 
num_new_subs['Number of Subscribers (Trialers)'] = 0
#print(num_new_subs.head(), "\n")

# **** NEW TRIALERS OVER TIME ***

# format new subscriptions from trialers data (using only subscriber since_data and was_trialer and grouping by date)
new_subs_from_trial_df = all_data_df[['Date Purchased', 'was_trial']].copy()
new_subs_from_trial_df = new_subs_from_trial_df.dropna()
#print(new_subs_from_trial_df.head(), "\n\n", "Trials over time", "\n")
new_subs_from_trial_df = new_subs_from_trial_df[new_subs_from_trial_df.was_trial != "f"]
#print(new_subs_from_trial_df.head(), "\n\n", "Frequency Table: Trialers Over Time", "\n")
# Delete the 'was_trial' column, currently holding trues-only, and build a "trues-only" frequency
# table. 
del new_subs_from_trial_df["was_trial"]
new_subs_from_trial_df["Date Purchased"] = new_subs_from_trial_df["Date Purchased"].apply(cut)
new_subs_from_trial_df["Date Purchased"] = new_subs_from_trial_df["Date Purchased"].apply(format_date1)
num_new_subs_from_trial = new_subs_from_trial_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers (Trialers)').reset_index()
#print(num_new_subs_from_trial.head(), "\n", "Total Subscriptions and Trials Component Over Time", "\n")

# *** COMBINED: NEW SUBSCRIBERS AND TRIALERS OVER TIME ***

# combine two dfs
all_subs = pd.merge(num_new_subs, num_new_subs_from_trial, on="Date Purchased", how="outer")
# There'll two columns with the lede, "Number of Subscribers (Trialers)..."
del all_subs["Number of Subscribers (Trialers)_x"]
all_subs = all_subs.rename(columns={'Number of Subscribers (Trialers)_y': 'Number of Subscribers (Trialers)'})
all_subs['Number of Subscribers (Trialers)'].fillna(0, inplace=True)

#######################################################################################################################

# **** DNRs OVER TIME ***
del num_new_subs['Number of Subscribers (Trialers)']
num_new_subs['Number of Subscribers (DNR-ed)'] = 0

new_subs_dnr_df = all_data_df[['Date Purchased', 'do_not_renew']].copy()
new_subs_dnr_df = new_subs_dnr_df.dropna()
print(new_subs_dnr_df.head(), "\n\n", "DNRs over time", "\n")
new_subs_dnr_df = new_subs_dnr_df[new_subs_dnr_df.do_not_renew != "f"]
print(new_subs_dnr_df.head(), "\n\n", "Frequency Table: DNRs Over Time", "\n")
# Delete the 'do_not_renew' column, currently holding trues-only, and build a "trues-only" frequency
# table. 
del new_subs_dnr_df["do_not_renew"]
new_subs_dnr_df["Date Purchased"] = new_subs_dnr_df["Date Purchased"].apply(cut)
new_subs_dnr_df["Date Purchased"] = new_subs_dnr_df["Date Purchased"].apply(format_date1)
num_new_subs_dnr = new_subs_dnr_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers (DNR-ed)').reset_index()
print(num_new_subs_dnr.head(), "\n", "Total Subscriptions and DNR-ed Component Over Time", "\n")

# combine two dfs
all_subs_2 = pd.merge(num_new_subs, num_new_subs_dnr, on="Date Purchased", how="outer")
# There'll two columns with the lede, "Number of Subscribers (DNR-ed)..."
del all_subs_2["Number of Subscribers (DNR-ed)_x"]
all_subs_2 = all_subs_2.rename(columns={'Number of Subscribers (DNR-ed)_y': 'Number of Subscribers (DNR-ed)'})
all_subs_2['Number of Subscribers (DNR-ed)'].fillna(0, inplace=True)
print(all_subs_2.head())

#######################################################################################################################


#  Plot data

fig = make_subplots(rows=2, cols=1, subplot_titles=("Subscriptions Over Time | Trial Subscriptions Overlayed", 
                                                    "Subscriptions Over Time | DNR-ed Subscriptions Overlayed"))

############## A. all_subs ###############

fig.add_trace(go.Scatter(x=all_subs["Date Purchased"], y=all_subs["Number of Subscribers"], name="Number of Subscribers"),
                         row=1, col=1)
fig.add_trace(go.Scatter(x=all_subs["Date Purchased"], y=all_subs["Number of Subscribers (Trialers)"], name="Number of Trialers"), 
                         row=1, col=1)
fig.update_xaxes(title_text="Date Purchased", row=1, col=1)
fig.update_yaxes(title_text="Number", row=1, col=1)

############## B. all_subs_2 ###############

fig.add_trace(go.Scatter(x=all_subs_2["Date Purchased"], y=all_subs_2["Number of Subscribers"], name="Number of Subscribers"),
                         row=2, col=1)
fig.add_trace(go.Scatter(x=all_subs_2["Date Purchased"], y=all_subs_2["Number of Subscribers (DNR-ed)"], name="Number of DNRs"), 
                         row=2, col=1)
fig.update_xaxes(title_text="Date Purchased", row=2, col=1)
fig.update_yaxes(title_text="Number", row=2, col=1)

#fig.update_layout(title_text="XXXXXXXXXXXXX")

fig.show()
fig.write_html('index.html', auto_open=True)
