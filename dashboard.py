import plotly.express as px

fig = px.bar(x=["a", "b", "c", "d"], y=[1, 3, 2, 5])
fig.write_html('index.html', auto_open=True)