import pandas as pd

s = pd.read_hdf('data.store', 'address')

oldest_time_stamp = s.index[-1]

print s

store = pd.HDFStore('data.store')
c = store.select_column('address','index')
print c[-5:]
where = c[-5:].index
print store.select('address',where=where)