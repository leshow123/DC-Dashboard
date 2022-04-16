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

subscriptions_sub_df = pd.DataFrame(subscriptions_df[['id', 'stripe_id', 'paid_until', 'was_trial', 'subscriber_since', 'do_not_renew', 'status']])
subscriptions_sub_df = subscriptions_sub_df.rename(columns={'id': 'subscription_id'})

track_interest_sub_df = track_interest_df[['purchased_at', 'subscription_id']].copy()
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].astype(str)
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].apply(cut7)
track_interest_sub_df["purchased_at"] = track_interest_sub_df["purchased_at"].apply(format_date2)

all_data_df = pd.merge(track_interest_sub_df, subscriptions_sub_df, on="subscription_id", how="outer")
all_data_df['purchased_at'].fillna(0, inplace=True)
all_data_df = all_data_df[all_data_df.purchased_at != 0]
#print(all_data_df.head())


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

# We need two separate tables (one as index) to achieve the aim. This is one.
all_paid_grped_sub_df = all_paid.groupby(['purchased_at']).size().to_frame(name="No. of Paid Subscriptions").reset_index()

all_paid_grped_sub_df["Paid Subscriptions"] = 0
all_paid_grped_sub_df["Active Paid Subscriptions"] = 0
all_paid_grped_sub_df["Active Paid Subscriptions, Converted from Trialing"] = 0
all_paid_grped_sub_df["Active Paid Subscriptions, DNRs=True"] = 0
all_paid_grped_by_purchased_at = all_paid.groupby(['purchased_at'])

#Convert SeriesGroupBy to DataFrame and reformat date columns
all_paid_grped_by_purchased_at = all_paid_grped_by_purchased_at.apply(pd.DataFrame)

all_paid_grped_by_purchased_at['purchased_at'] = all_paid_grped_by_purchased_at['purchased_at'].astype(str)
all_paid_grped_by_purchased_at['purchased_at'] = all_paid_grped_by_purchased_at['purchased_at'].apply(date_converter)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].astype(str)
all_paid_grped_by_purchased_at["paid_until"] = all_paid_grped_by_purchased_at["paid_until"].apply(cut7)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].apply(date_converter)
all_paid_grped_by_purchased_at['subscriber_since'] = all_paid_grped_by_purchased_at['subscriber_since'].astype(str)
all_paid_grped_by_purchased_at["subscriber_since"] = all_paid_grped_by_purchased_at["subscriber_since"].apply(cut7)
all_paid_grped_by_purchased_at['subscriber_since'] = all_paid_grped_by_purchased_at['subscriber_since'].apply(date_converter)

limit = len(all_paid_grped_sub_df.index)
for i in range(limit):
    # We need a date counter/index
    this_date = all_paid_grped_sub_df['purchased_at'][i]

    # The idea is to look-back, obtain qualifying transactions up until 'this_date', and extract necessary views.

    # Get "PAID SUBSCRIPTIONS", i.e., those that have 'subscriber_since' set, for each day
    paid_subs_b4_this_date = all_paid_grped_by_purchased_at[all_paid_grped_by_purchased_at.subscriber_since < date.fromisoformat(this_date)]

    # Get "ACTIVE PAID SUBSCRIPTIONS" as of this_date
    active_paid_subs_as_of_this_date = paid_subs_b4_this_date[paid_subs_b4_this_date.paid_until > date.fromisoformat(this_date)]

    # ACTIVE PAID SUBS - CONVERTED FROM TRIALING
    active_paid_subs_as_of_this_date_CONVERTED_FROM_TRIALING = active_paid_subs_as_of_this_date[active_paid_subs_as_of_this_date.was_trial == "t"]

    # ACTIVE PAID SUBS - DNR SET TO TRUE
    active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs = active_paid_subs_as_of_this_date[active_paid_subs_as_of_this_date.do_not_renew == "t"]
    
    all_paid_grped_sub_df["Paid Subscriptions"][i] = paid_subs_b4_this_date.count()["paid_until"]
    all_paid_grped_sub_df["Active Paid Subscriptions"][i] = active_paid_subs_as_of_this_date.count()["paid_until"]
    all_paid_grped_sub_df["Active Paid Subscriptions, Converted from Trialing"][i] = active_paid_subs_as_of_this_date_CONVERTED_FROM_TRIALING.count()["paid_until"]
    all_paid_grped_sub_df["Active Paid Subscriptions, DNRs=True"][i] = active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs.count()['paid_until']

# Note: Delete last row because of placeholder date "9999-12-13"
all_paid_grped_sub_df = all_paid_grped_sub_df[:-1]
all_paid_grped_sub_df = all_paid_grped_sub_df.rename(columns={'purchased_at': 'Date Purchased'})


########################################### PER DAY NO. OF SUBS WITH STATUS 'CANCELLED' ###################################################################################

new_subs_status7_df = all_data_df[['purchased_at', 'status']].copy()
new_subs_status7_df = new_subs_status7_df.dropna()
new_subs_status7_df = new_subs_status7_df[new_subs_status7_df.status == 7]

del new_subs_status7_df["status"]
new_subs_status7_df = new_subs_status7_df.rename(columns={'purchased_at': 'Date Purchased'})
new_subs_status7_df = new_subs_status7_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscriptions (Cancelled)').reset_index()

subscribers_over_time_cancelled_overlayed = pd.merge(num_new_subs, new_subs_status7_df, on="Date Purchased", how="outer")
subscribers_over_time_cancelled_overlayed['Number of Subscriptions (Cancelled)'].fillna(0, inplace=True)
subscribers_over_time_cancelled_overlayed["Date Purchased"] = subscribers_over_time_cancelled_overlayed["Date Purchased"].apply(date_converter)
subscribers_over_time_cancelled_overlayed = subscribers_over_time_cancelled_overlayed[:-1]


#############################################################################################################################################################

all_data_sub_df = all_data_df
all_data_sub_df = all_data_sub_df.groupby(['purchased_at'])
all_data_sub_df = all_data_sub_df.apply(pd.DataFrame)
#print(all_data_sub_df, "\n ***************************************** \n\n")

all_data_sub_df['purchased_at'] = all_data_sub_df['purchased_at'].astype(str)
all_data_sub_df['purchased_at'] = all_data_sub_df['purchased_at'].apply(date_converter)
all_data_sub_df['paid_until'] = all_data_sub_df['paid_until'].astype(str)
all_data_sub_df["paid_until"] = all_data_sub_df["paid_until"].apply(cut7)
#all_data_sub_df['paid_until'] = all_data_sub_df['paid_until'].apply(date_converter)
all_data_sub_df['subscriber_since'] = all_data_sub_df['subscriber_since'].astype(str)
all_data_sub_df["subscriber_since"] = all_data_sub_df["subscriber_since"].apply(cut7)
#all_data_sub_df['subscriber_since'] = all_data_sub_df['subscriber_since'].apply(date_converter)

#print(all_data_sub_df)
#exit(1)

# Note:
#  
# ACTIVE TRIAL(ER)S - to mean those about to or may not make the transition to paid subscription.
# ACTIVE TRIAL(ER)S = {subscriber_since = NULL, was_trial = TRUE, [paid_until != NULL]}
#   
all_data_sub_df_S_SINCE_IS_NULL = all_data_sub_df[all_data_sub_df.subscriber_since == "nan"]      #date.fromisoformat("9999-12-31")
all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE = all_data_sub_df_S_SINCE_IS_NULL[all_data_sub_df_S_SINCE_IS_NULL.was_trial == "t"]
all_data_sub_df_ACTIVE_TRIALERS = \
    all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE[all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE.paid_until != "nan"]

#all_data_sub_df_ACTIVE_TRIALERS.sort_values(['purchased_at'], ascending=True, inplace=True)

num_of_active_trialers = all_data_sub_df_ACTIVE_TRIALERS.groupby(['purchased_at']).size().to_frame(name="Active Trialers").reset_index()
num_of_active_trialers = num_of_active_trialers.rename(columns={'purchased_at': 'Date Purchased'})
num_of_active_trialers = num_of_active_trialers[:-1]

print(num_of_active_trialers, "\n\n")   
print(all_paid_grped_sub_df[['Date Purchased', 'Active Paid Subscriptions']])

#  PLOT DATA

fig = make_subplots(rows=3, cols=2, subplot_titles=("Per Day New Subscriptions | Trials", 
                                                    "Paid Subscriptions",
                                                    "Active Subscriptions | DNRs Percentages",
                                                    "Active Subscriptions | Trialing",
                                                    "Per Day New Subscriptions | Status \'Cancelled\'"))

############## A. ###############

df = subscribers_over_time_trialers_overlayed
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscribers (Trialers)"], name="Daily New Subscriptions (Trials)"), 
                         row=1, col=1)

fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Number", row=1, col=1)

############## B. ###############

df = all_paid_grped_sub_df
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Paid Subscriptions"], name="Paid Subscriptions"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Paid Subscriptions"], name="Active Paid Subscriptions (APS)"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Paid Subscriptions, Converted from Trialing"], name="APS - Converted from Trialing"), row=1, col=2)


fig.add_trace(go.Scatter(x=df["Date Purchased"], y=100.0 * (df["Active Paid Subscriptions, DNRs=True"]/df["Active Paid Subscriptions"]), name="Active DNRs Percentages"), row=2, col=1)


#fig.add_trace(go.Scatter(x=df["Date Purchased"], y=100.0 * (df["Active Trialers, Daily"]/df["Active Paid Subscriptions, Daily"]), name="Active Trialers Percentages"), row=2, col=2)

fig.add_trace(go.Scatter(x=num_of_active_trialers["Date Purchased"], y=num_of_active_trialers["Active Trialers"], name="Active Trialers, Daily"), row=2, col=2)

fig.update_xaxes(title_text="Date", row=1, col=2)
fig.update_yaxes(title_text="Number", row=1, col=2)

fig.update_xaxes(title_text="Date", row=2, col=1)
fig.update_yaxes(title_text="Percentage", row=2, col=1)

fig.update_xaxes(title_text="Date", row=2, col=2)
fig.update_yaxes(title_text="Percentage", row=2, col=2)

############## C. ###############

df = subscribers_over_time_cancelled_overlayed
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscriptions (Cancelled)"], name="Per Day NOS With Status \"Cancelled\""), 
                         row=3, col=1)
fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Number", row=3, col=1)


#fig.show()
fig.update_layout(showlegend=True)
fig.write_html('index.html', auto_open=True)
