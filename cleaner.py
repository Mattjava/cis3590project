import pandas, mongomock

db = mongomock.Database()

raw = pandas.read_csv('biscayne_bay_dataset_oct_2022.csv')

print(raw)

print("Number of rows originally: " + str(len(raw)) + "\n")

lat_data = raw['latitude']
lon_data = raw['longitude']
column_data = raw['Total Water Column (m)']
temp_data = raw['Temperature (C)']
ph_data = raw['pH']
odo_data = raw['ODO (mg/L)']

lat_mean = lat_data.mean()
lat_sd = lat_data.std()

lon_mean = lon_data.mean()
lon_sd = lon_data.std()

column_mean = lon_data.mean()
column_sd = column_data.std()

temp_mean = temp_data.mean()
temp_sd = temp_data.std()

ph_mean = ph_data.mean()
ph_sd = ph_data.std()

odo_mean = odo_data.mean()
odo_sd = odo_data.std()

clean = raw

dropped_rows = 0

def zfactor(x, mean, std):
    return abs((x - mean) / std)

for i in range(0, len(raw)):
    try:
        row = clean.iloc[i]
    except Exception:
        break
    
    lat = row['latitude']
    lon = row['longitude']
    column = row['Total Water Column (m)']
    temp = row['Temperature (C)']
    odo = row['ODO (mg/L)'] 
    ph = row['pH']

    lat_z = zfactor(lat, lat_mean, lat_sd)
    lon_z = zfactor(lon, lon_mean, lon_sd)
    column_z = zfactor(column, column_mean, column_sd)
    temp_z = zfactor(temp, temp_mean, temp_sd)
    odo_z = zfactor(odo, odo_mean, odo_sd)
    ph_z = zfactor(ph, ph_mean, ph_sd)


    if lat_z > 3 or lon_z > 3 or column_z > 3 or temp_z > 3 or odo_z > 3 or ph_z > 3:
        clean = clean.drop(i)
        i -= 1

print("Number of rows dropped: " + str(len(clean)))
