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

def cut7(x):
    return x[:10]

def format_date1(x):
    if x == '':
        return datetime.datetime.strptime("9999-12-31 00:00:00", "%Y-%m-%d %X").strftime("%Y-%m-%d")
    else:
        return datetime.datetime.strptime(x, "%Y-%m-%d %X").strftime("%Y-%m-%d")

def format_date2(x):
    if x == '' or x == 'nan':
        return datetime.datetime.strptime("9999-12-31 00:00:00", "%Y-%m-%d %X").strftime("%Y-%m-%d")
    else:
        return datetime.datetime.strptime(x, "%Y-%m-%d").strftime("%Y-%m-%d")

def date_converter(y):
    if y == 'nan':
        return date.fromisoformat("9999-12-31")
    else:    
        return date.fromisoformat(y)


# *** LOAD DATA ***

track_interest_df = pd.read_csv("track_interest.csv")
subscriptions_df = pd.read_csv("subscriptions.csv")

subscriptions_sub_df = pd.DataFrame(subscriptions_df[['id', 'stripe_id', 'paid_until', 'was_trial', 'do_not_renew', 'status']])
subscriptions_sub_df = subscriptions_sub_df.rename(columns={'id': 'subscription_id'})

track_interest_sub_df = track_interest_df[['purchased_at', 'subscription_id']].copy()
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].astype(str)
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].apply(cut7)
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].apply(format_date2)

all_data_df = pd.merge(track_interest_sub_df, subscriptions_sub_df, on="subscription_id", how="outer")
all_data_df['purchased_at'].fillna(0, inplace=True)
all_data_df = all_data_df[all_data_df.purchased_at != 0]

# *** NEW SUBSCRIBERS OVER TIME *** 

new_subs_df = pd.DataFrame(all_data_df['purchased_at'])
new_subs_df = new_subs_df.rename(columns={'purchased_at': 'Date Purchased'})
new_subs_df = new_subs_df.dropna(how = 'all')
num_new_subs = new_subs_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers').reset_index()

# Add a new column, 'Number of Subscribers From Trialers'. Initialize entire column to 0, preparatory to merge.
 
num_new_subs['Number of Subscribers (Trialers)'] = 0

# **** NEW TRIALERS OVER TIME ***

new_subs_from_trial_df = all_data_df[['purchased_at', 'was_trial']].copy()
new_subs_from_trial_df = new_subs_from_trial_df.dropna()
new_subs_from_trial_df = new_subs_from_trial_df[new_subs_from_trial_df.was_trial == "t"]

# Delete the 'was_trial' column, currently holding trues-only, and build a "trues-only" frequency
# table.
  
del new_subs_from_trial_df["was_trial"]
new_subs_from_trial_df = new_subs_from_trial_df.rename(columns={'purchased_at': 'Date Purchased'})
num_new_subs_from_trial = new_subs_from_trial_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers (Trialers)').reset_index()

# *** COMBINED: NEW SUBSCRIPTIONS AND TRIALS OVER TIME ***

subscribers_over_time_trialers_overlayed = pd.merge(num_new_subs, num_new_subs_from_trial, on="Date Purchased", how="outer")

# There'll two columns with the lede, "Number of Subscribers (Trialers)..."

del subscribers_over_time_trialers_overlayed["Number of Subscribers (Trialers)_x"]
subscribers_over_time_trialers_overlayed = subscribers_over_time_trialers_overlayed.rename(columns={'Number of Subscribers (Trialers)_y': 'Number of Subscribers (Trialers)'})
subscribers_over_time_trialers_overlayed['Number of Subscribers (Trialers)'].fillna(0, inplace=True)
subscribers_over_time_trialers_overlayed["Date Purchased"] = subscribers_over_time_trialers_overlayed["Date Purchased"].apply(date_converter)

# Take out the placeholder 9999-12-31

subscribers_over_time_trialers_overlayed = subscribers_over_time_trialers_overlayed[:-1]

########################################### ACTIVE SUBSCRIPTIONS ########################################################################################


all_paid = all_data_df

# We need two separate views/tables to achieve the aim. This is one.
all_paid_grped_sub_df = all_paid.groupby(['purchased_at']).size().to_frame(name="No. of Paid Subscriptions").reset_index()

all_paid_grped_sub_df["Active Paid Subscriptions, Daily"] = 0
all_paid_grped_sub_df["Active Paid Subscriptions, Daily (w/o Trials)"] = 0
all_paid_grped_sub_df["Active Trialers, Daily"] = 0
all_paid_grped_sub_df["Active DNRs"] = 0
all_paid_grped_by_purchased_at = all_paid.groupby(['purchased_at'])

#Convert SeriesGroupBy to DataFrame and reformat date columns
all_paid_grped_by_purchased_at = all_paid_grped_by_purchased_at.apply(pd.DataFrame)
all_paid_grped_by_purchased_at['purchased_at'] = all_paid_grped_by_purchased_at['purchased_at'].astype(str)
all_paid_grped_by_purchased_at['purchased_at'] = all_paid_grped_by_purchased_at['purchased_at'].apply(date_converter)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].astype(str)
all_paid_grped_by_purchased_at["paid_until"] = all_paid_grped_by_purchased_at["paid_until"].apply(cut7)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].apply(date_converter)

#print(all_paid_grped_by_purchased_at, "\n")

limit = len(all_paid_grped_sub_df.index)
for i in range(limit):
    this_purchased_at = all_paid_grped_sub_df['purchased_at'][i]

    # compare each purchased_at with ENTIRE HISTORY of paid_untils up until the purchased_at date

    subs_b4_this_purchased_at_date = all_paid_grped_by_purchased_at[all_paid_grped_by_purchased_at.purchased_at < date.fromisoformat(this_purchased_at)]

    active_paid_subs_b4_this_purchased_at_date = subs_b4_this_purchased_at_date[subs_b4_this_purchased_at_date.paid_until > date.fromisoformat(this_purchased_at)]
    active_paid_subs_b4_this_purchased_at_date_SAN_TRIAL = active_paid_subs_b4_this_purchased_at_date[active_paid_subs_b4_this_purchased_at_date.was_trial == "f"]

    # **** ACTIVE DNRs % ****
    active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs = active_paid_subs_b4_this_purchased_at_date[active_paid_subs_b4_this_purchased_at_date.do_not_renew == "t"]
    
    # **** ACTIVE TRIALERS OVER TIME ****
    active_paid_subs_b4_this_purchased_at_date_TRIAL = active_paid_subs_b4_this_purchased_at_date[active_paid_subs_b4_this_purchased_at_date.was_trial == "t"]
    #print("==> ", this_purchased_at, "\n", active_paid_subs_b4_this_purchased_at_date.count()["paid_until"],"\n")
    
    all_paid_grped_sub_df["Active Paid Subscriptions, Daily"][i] = active_paid_subs_b4_this_purchased_at_date.count()["paid_until"]
    all_paid_grped_sub_df["Active Paid Subscriptions, Daily (w/o Trials)"][i] = active_paid_subs_b4_this_purchased_at_date_SAN_TRIAL.count()["paid_until"]
    all_paid_grped_sub_df["Active Trialers, Daily"][i] = active_paid_subs_b4_this_purchased_at_date_TRIAL.count()["paid_until"]
    all_paid_grped_sub_df["Active DNRs"][i] = active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs.count()['paid_until']

# Note: Delete last row because of placeholder purchased_at  date "9999-12-13"
all_paid_grped_sub_df = all_paid_grped_sub_df[:-1]
all_paid_grped_sub_df = all_paid_grped_sub_df.rename(columns={'purchased_at': 'Date Purchased'})

########################################### PER DAY NO. OF SUBS CANCELLED ###################################################################################

new_subs_status7_df = all_data_df[['purchased_at', 'status']].copy()
new_subs_status7_df = new_subs_status7_df.dropna()
new_subs_status7_df = new_subs_status7_df[new_subs_status7_df.status == 7]

del new_subs_status7_df["status"]
new_subs_status7_df = new_subs_status7_df.rename(columns={'purchased_at': 'Date Purchased'})
new_subs_status7_df = new_subs_status7_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscriptions (Cancelled)').reset_index()

# *** COMBINED: NEW SUBSCRIPTIONS AND CANCELLED OVER TIME ***

subscribers_over_time_cancelled_overlayed = pd.merge(num_new_subs, new_subs_status7_df, on="Date Purchased", how="outer")
subscribers_over_time_cancelled_overlayed['Number of Subscriptions (Cancelled)'].fillna(0, inplace=True)
subscribers_over_time_cancelled_overlayed["Date Purchased"] = subscribers_over_time_cancelled_overlayed["Date Purchased"].apply(date_converter)
subscribers_over_time_cancelled_overlayed = subscribers_over_time_cancelled_overlayed[:-1]







"""
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
#print(new_subs_dnr_df.head(), "\n\n", "DNRs over time", "\n")
new_subs_dnr_df = new_subs_dnr_df[new_subs_dnr_df.do_not_renew != "f"]
#print(new_subs_dnr_df.head(), "\n\n", "Frequency Table: DNRs Over Time", "\n")
# Delete the 'do_not_renew' column, currently holding trues-only, and build a "trues-only" frequency
# table. 
del new_subs_dnr_df["do_not_renew"]
new_subs_dnr_df["Date Purchased"] = new_subs_dnr_df["Date Purchased"].apply(cut)
new_subs_dnr_df["Date Purchased"] = new_subs_dnr_df["Date Purchased"].apply(format_date1)
num_new_subs_dnr = new_subs_dnr_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers (DNR-ed)').reset_index()
#print(num_new_subs_dnr.head(), "\n", "Total Subscriptions and DNR-ed Component Over Time", "\n")

# combine two dfs
all_subs_2 = pd.merge(num_new_subs, num_new_subs_dnr, on="Date Purchased", how="outer")
# There'll two columns with the lede, "Number of Subscribers (DNR-ed)..."
del all_subs_2["Number of Subscribers (DNR-ed)_x"]
all_subs_2 = all_subs_2.rename(columns={'Number of Subscribers (DNR-ed)_y': 'Number of Subscribers (DNR-ed)'})
all_subs_2['Number of Subscribers (DNR-ed)'].fillna(0, inplace=True)
#print(all_subs_2.head())

#######################################################################################################################

# **** STATUS: CANCELLED [7] OVER TIME ***

del num_new_subs['Number of Subscribers (DNR-ed)']
num_new_subs['Number of Subscribers (Cancelled)'] = 0

new_subs_cancelled_df = all_data_df[['Date Purchased', 'status']].copy()
new_subs_cancelled_df = new_subs_cancelled_df.dropna()
print(new_subs_cancelled_df.head(), "\n\n", "Status (Cancelled) over time", "\n")
new_subs_cancelled_df = new_subs_cancelled_df[new_subs_cancelled_df.status == 7]
print(new_subs_cancelled_df.head(), "\n\n", "Frequency Table: Status (Cancelled) Over Time", "\n")
# Delete the 'status' column, currently holding 7s-only, and build a "7s-only, i.e., cancelled" frequency
# table.
del new_subs_cancelled_df["status"]
new_subs_cancelled_df["Date Purchased"] = new_subs_cancelled_df["Date Purchased"].apply(cut)
new_subs_cancelled_df["Date Purchased"] = new_subs_cancelled_df["Date Purchased"].apply(format_date1)
num_new_subs_cancelled = new_subs_cancelled_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers (Cancelled)').reset_index()
print(num_new_subs_cancelled.head(), "\n", "Total Subscriptions and Cancelled Subscriptions Over Time", "\n")

# combine two dfs
all_subs_3 = pd.merge(num_new_subs, num_new_subs_cancelled, on="Date Purchased", how="outer")
# There'll two columns with the lede, "Number of Subscribers (Cancelled)..."
del all_subs_3["Number of Subscribers (Cancelled)_x"]
all_subs_3 = all_subs_3.rename(columns={'Number of Subscribers (Cancelled)_y': 'Number of Subscribers (Cancelled)'})
all_subs_3['Number of Subscribers (Cancelled)'].fillna(0, inplace=True)
print(all_subs_3.head())

#######################################################################################################################

"""











#  Plot data

fig = make_subplots(rows=3, cols=2, subplot_titles=("Per Day New Subscriptions | Trials Overlayed", 
                                                    "Active Subscriptions",
                                                    "Active Subscriptions | DNRs Percentages",
                                                    "Active Subscriptions | Trials Percentages",
                                                    "All Subscriptions | Cancelled Status, Daily"))

############## A. ###############

df = subscribers_over_time_trialers_overlayed
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscribers"], name="Daily New Subscriptions"),
                         row=1, col=1)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscribers (Trialers)"], name="Daily New Subscriptions (Trials)"), 
                         row=1, col=1)

fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Number", row=1, col=1)

############## B. ###############

df = all_paid_grped_sub_df
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Paid Subscriptions, Daily"], name="Active Paid Subscriptions, Daily"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Paid Subscriptions, Daily (w/o Trials)"], name="Active Paid Subscriptions, Daily (w/o Trials)"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Trialers, Daily"], name="Active Trialers, Daily"), row=1, col=2)


fig.add_trace(go.Scatter(x=df["Date Purchased"], y=100.0 * (df["Active DNRs"]/df["Active Paid Subscriptions, Daily"]), name="Active DNRs Percentages"), row=2, col=1)


fig.add_trace(go.Scatter(x=df["Date Purchased"], y=100.0 * (df["Active Trialers, Daily"]/df["Active Paid Subscriptions, Daily"]), name="Active Trialers Percentages"), row=2, col=2)


fig.update_xaxes(title_text="Date", row=1, col=2)
fig.update_yaxes(title_text="Number", row=1, col=2)

fig.update_xaxes(title_text="Date", row=2, col=1)
fig.update_yaxes(title_text="Percentage", row=2, col=1)

fig.update_xaxes(title_text="Date", row=2, col=2)
fig.update_yaxes(title_text="Percentage", row=2, col=2)

############## C. ###############

df = subscribers_over_time_cancelled_overlayed

fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscribers"], name="Daily New Subscriptions"),
                         row=3, col=1)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscriptions (Cancelled)"], name="Per Day NOS With Status \"Cancelled\""), 
                         row=3, col=1)
fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Number", row=3, col=1)


"""
fig.add_trace(go.Scatter(x=all_subs_3["Date Purchased"], y=all_subs_3["Number of Subscribers"], name="Number of Subscribers"),
                         row=1, col=2)
fig.add_trace(go.Scatter(x=all_subs_3["Date Purchased"], y=all_subs_3["Number of Subscribers (Cancelled)"], name="Number of Cancelled Subscriptions"), 
                         row=1, col=2)
fig.update_xaxes(title_text="Date Purchased", row=1, col=2)
fig.update_yaxes(title_text="Number", row=1, col=2)


fig.update_layout(showlegend=False)
"""
#fig.show()
fig.write_html('index.html', auto_open=True)
