import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import pandas as pd
import pandas_datareader.data as web
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates

style.use("ggplot")

#Start date for series
start = dt.datetime(2000,1,1) 
#End date for series, can be changed to a specific date
end = dt.datetime.today() 

#The tikcer name, can be found on yahoo
ticker = "AZN" 
df = web.DataReader(ticker, "yahoo", start, end)

#"Adj Close" can be edited, and so can resampling size
df_ohlc = df["Adj Close"].resample("5D").ohlc()
#"Volume" can be edited, but is a useful insight, resampling resolution can be changed
df_volume = df["Volume"].resample("5D").sum()

df_ohlc.reset_index(inplace=True)
df_ohlc["Date"] = df_ohlc["Date"].map(mdates.date2num)

ax1 = plt.subplot2grid((6,1), (0,0),rowspan=5, colspan=1)
plt.title(f"{ticker} Candlestick and Volume")
ax2 = plt.subplot2grid((6,1), (5,0),rowspan=1, colspan=1, sharex=ax1)
ax1.xaxis_date()
candlestick_ohlc(ax1, df_ohlc.values, width=2, colorup="g")
ax2.fill_between(df_volume.index.map(mdates.date2num), df_volume.values, 0)

plt.show()