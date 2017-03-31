import pandas as pd

h5_file = "h5_store_.h5"
h5_key = 'address'

df = pd.read_hdf(h5_file, h5_key)

# set index to timestamps
df = df.set_index("timestamp")

print df.tail()

end_time_window = df.index.max()
start_time_window = end_time_window - pd.DateOffset(milliseconds=1000)

df_slice = df.ix[start_time_window:]

print df_slice

