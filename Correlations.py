import bs4 as bs
import datetime as dt
import os
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import pickle
import requests

style.use("ggplot")

def save_sp500_tickers():
	resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies") 
	soup = bs.BeautifulSoup(resp.text, "lxml")
	table = soup.find('table', {'id': 'constituents'})
	tickers = []
	for row in table.findAll("tr")[1:]:
		ticker = row.findAll('td')[0].text.strip().replace(".","-")
		tickers.append(ticker)

	with open("sp500tickers.pickle","wb") as f:
		pickle.dump(tickers, f)

	print(tickers)

# save_sp500_tickers()

def get_data_from_yahoo(reload_sp500 = False):
	if reload_sp500:
		tickers = save_sp500_tickers()
	else:
		with open("sp500tickers.pickle","rb") as f:
			tickers = pickle.load(f)

	if not os.path.exists("stock_dfs"):
		os.makedirs("stock_dfs")

	start = dt.datetime(2020,1,1)
	end = dt.datetime.today()

	for ticker in tickers:
		print(ticker)
		if not os.path.exists(f"stock_dfs/{ticker}.csv"):
			df = web.DataReader(ticker, "yahoo", start, end)
			df.to_csv(f"stock_dfs/{ticker}.csv")
		else:
			print(f"Already have {ticker}")

# get_data_from_yahoo()

def compile_data():
	with open("sp500tickers.pickle","rb") as f:
		tickers = pickle.load(f)

	main_df = pd.DataFrame()

	for count,ticker in enumerate(tickers):
		df = pd.read_csv(f"stock_dfs/{ticker}.csv")
		df.set_index("Date", inplace=True)

		df.rename(columns = {"Adj Close":ticker}, inplace=True)
		df.drop(["Open", "High", "Low", "Close", "Volume"], 1, inplace=True)

		if main_df.empty:
			main_df = df
		else:
			main_df = main_df.join(df, how="outer")
		if count % 10 == 0:
			print(count)

	
	main_df.to_csv("sp500_joined_closes.csv")

# compile_data()

def visualise_data():
	df = pd.read_csv("sp500_joined_closes.csv")	
	
	df_corr = df.corr()

	data = df_corr.values
	fig = plt.figure()
	ax = fig.add_subplot(1,1,1)

	heatmap = ax.pcolor(data, cmap=plt.cm.RdYlGn)
	fig.colorbar(heatmap)
	ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False)
	ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False)
	ax.invert_yaxis()
	ax.xaxis.tick_top()

	column_labels = df_corr.columns
	row_labels = df_corr.index

	ax.set_xticklabels(column_labels, fontsize=0.5)
	ax.set_yticklabels(row_labels, fontsize=0.25)
	plt.xticks(rotation=90)
	heatmap.set_clim(-1,1)
	plt.tight_layout()
	plt.show()

visualise_data()