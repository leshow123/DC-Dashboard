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

def cut19(x):
    return x[:19]

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

def format_date3(x):
    date_format = "%Y-%m-%d %H:%M:%S" #"%b %d %Y %H:%M:%S"
    if x == 'nan':
        pass # option 1. Use 'pass' so pd.Timestamp coerces return value to NaT

        # option 2. choose a date close to pd.Timstamp min as placeholder for 
        # nan in paid_until or dat_joined. The nan might be due to couponed 
        # subscriptions, since they have > 0 days_in_subscriptions. See
        # Active Trialers %ages.

        #return datetime.datetime.strptime("1759-12-31 00:00:00", date_format)
        
    else:
        return datetime.datetime.strptime(x, date_format)

def date_converter(y):
    if y == 'nan':
        return date.fromisoformat("9999-12-31")
    else:    
        return date.fromisoformat(y)

def date_subtract(y,n):
    return y - timedelta(days=n)

def timedelta_convert(n):
    return timedelta(days=n)

# *** LOAD DATA ***

#track_interest_df = pd.read_csv("track_interest.csv")
subscriptions_df = pd.read_csv("subscriptions.csv")

#print("Rows in TRACK_INTEREST_DF: ", len(track_interest_df.index), "\n")
#print("Rows in SUBSCRIPTIONS_DF: ", len(subscriptions_df.index), "\n")

subscriptions_sub_df = pd.DataFrame(subscriptions_df[['id', 'stripe_id', 'paid_until', 'was_trial', 'subscriber_since', 'do_not_renew', 'status', 'days_in_subscription']])
subscriptions_sub_df = subscriptions_sub_df.rename(columns={'id': 'subscription_id'})

#print("Rows in SUBSCRIPTIONS_SUB_DF: ", len(subscriptions_sub_df.index), "\n")

all_data_df = subscriptions_sub_df


#
# *** NEW SUBSCRIBERS, DAILY, OVER THE PERIOD *** 
#

new_subs_df = pd.DataFrame(all_data_df['subscriber_since'])
new_subs_df = new_subs_df.rename(columns={'subscriber_since': 'Date Purchased'})
new_subs_df["Date Purchased"] = new_subs_df["Date Purchased"].astype(str)
new_subs_df["Date Purchased"] = new_subs_df["Date Purchased"].apply(cut7)
new_subs_df["Date Purchased"] = new_subs_df["Date Purchased"].apply(format_date2)
new_subs_df.fillna("9999-12-31 00:00:00-00", inplace=True)
num_new_subs = new_subs_df.groupby(['Date Purchased']).size().to_frame(name = 'Number of Subscribers').reset_index()
num_new_subs = num_new_subs[:-1]

print("\n ******************** num_new_subs ********************** \n")
print(num_new_subs, "\n")


#
# **** SUBSCRIPTIONS COMMENCING AS TRIALING OVER THE PERIOD ***** 
#      
#      At this point, we dont care whether the user's gonna
#      make the jump to fully paid or not. When we do care,
#      we graph ACTIVE TRIALERS later on.
#

"""
1. days_in_subscription is needed to compute the subscriber_since (a.k.a Date Purchased),
   i.e., paid_until - days_in_subscription, in cases whereby 
   {was_trial == t; paid_until != NULL; subscriber_since == NULL}.

2. But there are also cases where {paid_until == NULL; subscriber_since == NULL;
   days_in_subscription == 0}. Coupons, I guess? Or "visitors" (BUT HOW'D THEY GET
   ON THE SUBSCRIPTION TABLE). These are dropped, since we can't fit them to a 
   particular date in the timeline.

"""
"""
new_subs_commenced_as_trial_df = all_data_df[['subscriber_since','paid_until','days_in_subscription','was_trial']].copy()
new_subs_commenced_as_trial_df["subscriber_since"].fillna('', inplace=True) 
new_subs_commenced_as_trial_df["subscriber_since"] = new_subs_commenced_as_trial_df["subscriber_since"].astype(str)
new_subs_commenced_as_trial_df["subscriber_since"] = new_subs_commenced_as_trial_df["subscriber_since"].apply(cut19)
new_subs_commenced_as_trial_df["paid_until"] = new_subs_commenced_as_trial_df["paid_until"].astype(str)
new_subs_commenced_as_trial_df["paid_until"] = new_subs_commenced_as_trial_df["paid_until"].apply(cut19)
new_subs_commenced_as_trial_df["paid_until"] = new_subs_commenced_as_trial_df["paid_until"].apply(format_date3)
new_subs_commenced_as_trial_df["days_in_subscription"] = new_subs_commenced_as_trial_df["days_in_subscription"].apply(timedelta_convert)

#print(new_subs_commenced_as_trial_df, "\n ******************************************")

# Take out those described in 2. above                          TODO How many are there?
new_subs_commenced_as_trial_df = new_subs_commenced_as_trial_df[new_subs_commenced_as_trial_df.days_in_subscription != timedelta_convert(0)]
#print(new_subs_commenced_as_trial_df, "\n ******************************************")

new_subs_commenced_as_trial_df = \
    new_subs_commenced_as_trial_df.assign(date_purchased = lambda x: x['paid_until'] - x['days_in_subscription'])
#print(new_subs_commenced_as_trial_df, "\n ******************************************")
"""

"""
There's a 2hr slack added to the expiration (i.e., paid_until). Why is that @MarkJones?
Anyway, TODO: Compensate for this in via timedelta's HH:MM:SS for (alias) 'date_purchased'.
Otherwise, we'd have to take 'date_purchased' as a close approx. of subscriber_since.

"""

"""
# Now that EVERY subscription has been fitted to a timeline, from the previous steps,
# we can then focus attention. 

new_subs_commenced_as_trial_df = new_subs_commenced_as_trial_df[new_subs_commenced_as_trial_df.was_trial == "t"]

#print(len(new_subs_commenced_as_trial_df.index), "\n ******************************************")
#print(new_subs_commenced_as_trial_df)

new_subs_commenced_as_trial_df_ACTUAL = new_subs_commenced_as_trial_df[['date_purchased','was_trial']].copy()
new_subs_commenced_as_trial_df_ACTUAL = new_subs_commenced_as_trial_df_ACTUAL.reset_index()
# Delete the old index
del new_subs_commenced_as_trial_df_ACTUAL['index']
new_subs_commenced_as_trial_df_ACTUAL['date_purchased'] = new_subs_commenced_as_trial_df_ACTUAL['date_purchased'].astype(str)
new_subs_commenced_as_trial_df_ACTUAL['date_purchased'] = new_subs_commenced_as_trial_df_ACTUAL['date_purchased'].apply(cut7)

#print(len(new_subs_commenced_as_trial_df_ACTUAL.index), "\n ******************************************")
#print(new_subs_commenced_as_trial_df_ACTUAL)

# Delete the 'was_trial' column, currently holding trues-only, and build a "trues-only" frequency
# table.
  
del new_subs_commenced_as_trial_df_ACTUAL["was_trial"]
new_subs_commenced_as_trial_df_ACTUAL = new_subs_commenced_as_trial_df_ACTUAL.rename(columns={'date_purchased': 'Date Purchased'})
new_subs_commenced_as_trial_df_ACTUAL = \
    new_subs_commenced_as_trial_df_ACTUAL.groupby(['Date Purchased']).size().to_frame(name = 'NoS Commenced as Trialers').reset_index()

print("\n ******************** new_subs_commenced_as_trial_df_ACTUAL ********************** \n")
print(new_subs_commenced_as_trial_df_ACTUAL, "\n")
"""

########################################### ACTIVE SUBSCRIPTIONS ########################################################################################

all_paid = all_data_df

# We need two separate tables (one for indexing) to achieve the aim. This is one.
all_paid['subscriber_since'] = all_paid['subscriber_since'].astype(str)
all_paid['subscriber_since'] = all_paid['subscriber_since'].apply(cut7)
all_paid['subscriber_since'] = all_paid['subscriber_since'].apply(date_converter)
all_paid_grped_sub_df = all_paid.groupby(['subscriber_since']).size().to_frame(name="No. of Subscriptions").reset_index()

#print(len(all_paid_grped_sub_df.index), "\n ******************************************")
#print(all_paid_grped_sub_df)

all_paid_grped_sub_df["Paid Subscriptions"] = 0
all_paid_grped_sub_df["Active Paid Subscriptions (APS)"] = 0
all_paid_grped_sub_df["APS, Converted from Trialing"] = 0
all_paid_grped_sub_df["APS, Commenced with DNR=True"] = 0

all_paid_grped_by_purchased_at = all_paid.groupby(['subscriber_since'])       #TODO Chnage to all_paid_grped_by_subscriber_since

#Convert SeriesGroupBy to DataFrame and reformat date columns
all_paid_grped_by_purchased_at = all_paid_grped_by_purchased_at.apply(pd.DataFrame)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].astype(str)
all_paid_grped_by_purchased_at["paid_until"] = all_paid_grped_by_purchased_at["paid_until"].apply(cut7)
all_paid_grped_by_purchased_at['paid_until'] = all_paid_grped_by_purchased_at['paid_until'].apply(date_converter)

#print(len(all_paid_grped_by_purchased_at.index), "\n ******************************************")
#print(all_paid_grped_by_purchased_at)

limit = len(all_paid_grped_sub_df.index)

# Need it back as str()
all_paid_grped_sub_df['subscriber_since'] = all_paid_grped_sub_df['subscriber_since'].astype(str)

for i in range(limit):
    # We need to iterate through the dates
    this_date = all_paid_grped_sub_df['subscriber_since'][i]

    # The idea is to look-back, obtain qualifying transactions up until 'this_date', and extract necessary views.

    # Get "PAID SUBSCRIPTIONS" (i.e., those that have 'subscriber_since' set) on each day
    paid_subs_b4_this_date = all_paid_grped_by_purchased_at[all_paid_grped_by_purchased_at.subscriber_since < date.fromisoformat(this_date)]

    # Get "ACTIVE PAID SUBSCRIPTIONS" as of this_date
    active_paid_subs_b4_this_date = paid_subs_b4_this_date[paid_subs_b4_this_date.paid_until > date.fromisoformat(this_date)]

    # ACTIVE PAID SUBS - CONVERTED FROM TRIALING
    active_paid_subs_b4_this_date_CONVERTED_FROM_TRIALING = active_paid_subs_b4_this_date[active_paid_subs_b4_this_date.was_trial == "t"]

    # ACTIVE PAID SUBS - COMMENCED AS DNR=t
    #
    # Caveat: Transitions from DNR=t to DNR=f (i.e., yes, renew) and vice versa are not taken into
    #         account.
    #
    active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs = active_paid_subs_b4_this_date[active_paid_subs_b4_this_date.do_not_renew == "t"]
    
    all_paid_grped_sub_df["Paid Subscriptions"][i] = paid_subs_b4_this_date.count()["paid_until"]
    all_paid_grped_sub_df["Active Paid Subscriptions (APS)"][i] = active_paid_subs_b4_this_date.count()["paid_until"]
    all_paid_grped_sub_df["APS, Converted from Trialing"][i] = active_paid_subs_b4_this_date_CONVERTED_FROM_TRIALING.count()["paid_until"]
    all_paid_grped_sub_df["APS, Commenced with DNR=True"][i] = active_paid_subs_b4_this_purchased_at_date_ACTIVE_DNRs.count()['paid_until']

# Note: Delete last row because of placeholder date "9999-12-13"
all_paid_grped_sub_df = all_paid_grped_sub_df[:-1]

all_paid_grped_sub_df = all_paid_grped_sub_df.rename(columns={'subscriber_since': 'Date Purchased'})

print("\n ***************** all_paid_grped_sub_df *************************\n")
print(all_paid_grped_sub_df, "\n")


########################################### PER DAY NO. OF SUBS WITH STATUS 'CANCELLED' ######################################################################
"""
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

"""

###########################################              ACTIVE TRIALERS              #########################################################################

all_data_sub_df = all_data_df
all_data_sub_df = all_data_sub_df.groupby(['subscriber_since'])
all_data_sub_df = all_data_sub_df.apply(pd.DataFrame)

#print(len(all_data_sub_df.index), "\n **************** HERE 1 *************************")
#print(all_data_sub_df)

# Make a copy. We need it for computing a breakdown of Active Trialers
# for each day (i.e., paid_until - days_in_subscription).

all_data_sub_df['paid_until_format1'] = all_data_sub_df['paid_until']
all_data_sub_df["paid_until_format1"] = all_data_sub_df["paid_until_format1"].astype(str)
all_data_sub_df["paid_until_format1"] = all_data_sub_df["paid_until_format1"].apply(cut19)
all_data_sub_df["paid_until_format1"] = all_data_sub_df["paid_until_format1"].apply(format_date3)
all_data_sub_df["days_in_subscription"] = all_data_sub_df["days_in_subscription"].apply(timedelta_convert)

# Make a copy for re-use when computing Active Trialers %ages.
all_data_sub_df_COPY = all_data_sub_df

all_data_sub_df['paid_until'] = all_data_sub_df['paid_until'].astype(str)
all_data_sub_df["paid_until"] = all_data_sub_df["paid_until"].apply(cut7)
all_data_sub_df['subscriber_since'] = all_data_sub_df['subscriber_since'].astype(str)

#print(len(all_data_sub_df.index), "\n **************** HERE 2 **************************")
#print(all_data_sub_df)


# NOTE:
#  
# ACTIVE TRIAL(ER)S, to mean, those about to or may not make the 
# transition to paid subscription.
# 
# AT = {subscriber_since = NULL, was_trial = TRUE, [paid_until != NULL]}
#   
all_data_sub_df_S_SINCE_IS_NULL = all_data_sub_df[all_data_sub_df.subscriber_since == "9999-12-31"]

#print(len(all_data_sub_df_S_SINCE_IS_NULL.index), "\n")
#print(all_data_sub_df_S_SINCE_IS_NULL)

all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE = all_data_sub_df_S_SINCE_IS_NULL[all_data_sub_df_S_SINCE_IS_NULL.was_trial == "t"]
all_data_sub_df_ACTIVE_TRIALERS = \
    all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE[all_data_sub_df_S_SINCE_IS_NULL_and_WAS_TRIAL_IS_TRUE.paid_until != "nan"]

# Per day breakdown based on paid_until and days_in_subscription. 
# Recall, paid_until - days_in_subscription ~= purchase date.

all_data_sub_df_ACTIVE_TRIALERS = \
    all_data_sub_df_ACTIVE_TRIALERS.assign(date_purchased = lambda x: x['paid_until_format1'] - x['days_in_subscription'])

#print(len(all_data_sub_df_ACTIVE_TRIALERS.index), "\n")   # 2,278
#print(all_data_sub_df_ACTIVE_TRIALERS)

all_data_sub_df_ACTIVE_TRIALERS["date_purchased"] = all_data_sub_df_ACTIVE_TRIALERS["date_purchased"].astype(str)
all_data_sub_df_ACTIVE_TRIALERS["date_purchased"] = all_data_sub_df_ACTIVE_TRIALERS["date_purchased"].apply(cut7)
num_of_active_trialers = all_data_sub_df_ACTIVE_TRIALERS.groupby(['date_purchased']).size().to_frame(name="Active Trialers").reset_index()
num_of_active_trialers = num_of_active_trialers.rename(columns={'date_purchased': 'Date Purchased'})

print("\n *********************  num_of_active_trialers  *******************************")
print(num_of_active_trialers, "\n")
#print(all_paid_grped_sub_df, "\n *****************************************************")


############### ACTIVE TRIALER PERCENTAGE OF ... #######################

"""
Active Trialers (AT) %ages are computed from the ratio of AT to
EVERY kind of subscription, less those described in 2.
above, that have days_in_subscription = 0 (Coupons maybe?).

But as previously alluded, active trialers have to be fit
to a timeline, since they don't have subscriber_since set 
(yet or maybe never). So, we just compute: 
paid_until - days_in_subscription ~= purchase date / date_joined 
(as alias/approx. for subscriber_since).

"""

# Firstly, take out those described in 2. above
   
all_data_sub_df_COPY = all_data_sub_df_COPY[all_data_sub_df_COPY.days_in_subscription != timedelta_convert(0)]
all_data_sub_df_COPY = \
    all_data_sub_df_COPY.assign(date_joined = lambda x: x['paid_until_format1'] - x['days_in_subscription'])

#all_data_sub_df_COPY.to_csv('all_data_sub_df_COPY.csv')
#print("\n ************************************ \n", all_data_sub_df_COPY)

all_data_sub_df_COPY["date_joined"] = all_data_sub_df_COPY["date_joined"].astype(str)
all_data_sub_df_COPY["date_joined"] = all_data_sub_df_COPY["date_joined"].apply(cut7)

#print("\n ************************************ \n", all_data_sub_df_COPY)

subcriptions_date_joined = all_data_sub_df_COPY[["date_joined"]].copy()
subcriptions_date_joined = subcriptions_date_joined.reset_index()
del subcriptions_date_joined['index']
#print("\n ************************************ \n", subcriptions_date_joined)
#subcriptions_date_joined.to_csv('joined_fqt.csv')

# Build the frequency table
subcriptions_date_joined = subcriptions_date_joined.groupby(['date_joined']).size().to_frame(name="NoS").reset_index()

# Remove that NaT (for the test dataset, 69 in total. These are subscriptions 
# with non-zero days_in_subscription but with paid_until == null. 
# Meaning, we can't compute dat_joined for them. COUPONS?
#  
subcriptions_date_joined = subcriptions_date_joined[:-1]

"""
At this point, we now have two tables, one holding no. of ALL OTHER
subscriptions as at each day, and the second one, Active Trialers as
at each day. Hence, we can compute %ages.

Ideally, the tables should be same length (row-wise), but rather than
relay on pd.merge (akin to SQL joins), we had proceed as follows.

"""

AS = subcriptions_date_joined
AS = AS.rename(columns = {'date_joined':'Date Purchased'})
num_of_active_trialers = num_of_active_trialers.rename(columns={'date_purchased': 'Date Purchased'})
num_of_active_trialers['Date Purchased'] = num_of_active_trialers['Date Purchased'].astype(str)

#print("\n ************************************ \n", AS, "\n")

#print("\n ************************************ \n", num_of_active_trialers)

# Convert Dataframe to Dictionary With one of the columns as key
AT_dict_keyed_by_Date_Purchased = num_of_active_trialers.set_index('Date Purchased').T.to_dict('list')
AS_dict_keyed_by_Date_Purchased = AS.set_index('Date Purchased').T.to_dict('list')

#print(AT_dict_keyed_by_Date_Purchased, "\n\n")
#print(AS_dict_keyed_by_Date_Purchased, "\n\n")

# NOTE:
# 
# The idea is to lookup the corresponding values in APS for each date existing in AT.
# 
# CAVEAT However, pd.merge(...,how="outer"), which is equiv. to a "outer join" will yield 
# impaired results if the tables are of variable length.
# 
# It's more convenient (or safe), to implement the idea as follows, and make graphing 
# easy.
#

for key in AS_dict_keyed_by_Date_Purchased:
    AS_value = AT_dict_keyed_by_Date_Purchased.get(key,None)
    if AS_value != None:
        AS_value = AS_value.pop()
        AS_dict_keyed_by_Date_Purchased[key].append(AS_value)

#print(AS_dict_keyed_by_Date_Purchased, "\n\n")

# Use the keys (i.e., dates) as the index (i.e., ...orient='index'...), where 'AT_percentages_view'
# facilitates graphing ACTIVE TRIALERS %ages
 
AT_percentages_view = pd.DataFrame.from_dict(AS_dict_keyed_by_Date_Purchased, orient='index', columns=['All Other Subscriptions', 'Active Trialers'])
AT_percentages_view = AT_percentages_view.reset_index()
AT_percentages_view = AT_percentages_view.rename(columns = {'index':'Date'})
AT_percentages_view['Active Trialers'].fillna(0, inplace=True) # You never know.

print("\n********************** AT_percentages_view  *******************************\n")
print(AT_percentages_view, "\n")



#  PLOT DATA

fig = make_subplots(rows=3, cols=2, subplot_titles=("Per Day New Subscriptions", 
                                                    "Paid Subscriptions | Active Paid Subscriptions (APS)",
                                                    "DNRs - Daily Percentages of APS",
                                                    "Active Trialers, PiT",
                                                    "Active Trialers - Daily Percentage of APS",
                                                    "" #"Per Day New Subscriptions - Status \'Cancelled\'",
                                                    ))

############## A. ###############

"""
df = new_subs_commenced_as_trial_df_ACTUAL
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["NoS Commenced as Trialers"], name="Daily Subscriptions Commenced as Trials"), 
                         row=1, col=1)

fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Number", row=1, col=1)

"""

df = num_new_subs
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscribers"], name="Daily New Subscriptions"), 
                         row=1, col=1)

fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Number", row=1, col=1)

############## B. ###############

df = all_paid_grped_sub_df
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Paid Subscriptions"], name="Paid Subscriptions"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Active Paid Subscriptions (APS)"], name="Active Paid Subscriptions (APS)"), 
                         row=1, col=2)
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["APS, Converted from Trialing"], name="APS - Converted from Trialing"), row=1, col=2)

# DNRs - Daily Percentages
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=100.0 * (df["APS, Commenced with DNR=True"]/df["Active Paid Subscriptions (APS)"]), name="Active DNRs Percentages"), row=2, col=1)

# Active Trialers, PiT
fig.add_trace(go.Scatter(x=num_of_active_trialers["Date Purchased"], y=num_of_active_trialers["Active Trialers"], name="Active Trialers, PiT"), row=2, col=2)

# Active Trialers, %ages
fig.add_trace(go.Scatter(x=AT_percentages_view["Date"], y=100.0 * (AT_percentages_view["Active Trialers"]/AT_percentages_view["All Other Subscriptions"])
, name="Active Trialers, Daily Percentages"), row=3, col=1)

fig.update_xaxes(title_text="Date", row=1, col=2)
fig.update_yaxes(title_text="Number", row=1, col=2)

fig.update_xaxes(title_text="Date", row=2, col=1)
fig.update_yaxes(title_text="Percentage", row=2, col=1)

fig.update_xaxes(title_text="Date", row=2, col=2)
fig.update_yaxes(title_text="Number", row=2, col=2)

fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Percentage", row=3, col=1)

############## C. ###############
"""
df = subscribers_over_time_cancelled_overlayed
fig.add_trace(go.Scatter(x=df["Date Purchased"], y=df["Number of Subscriptions (Cancelled)"], name="Per Day NOS With Status \"Cancelled\""), 
                         row=3, col=1)
fig.update_xaxes(title_text="Date", row=3, col=1)
fig.update_yaxes(title_text="Number", row=3, col=1)
"""

#fig.show()
fig.update_layout(showlegend=True)
fig.write_html('index.html', auto_open=True)
