import plotly.express as px

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
fig.write_html('index.html', auto_open=True)