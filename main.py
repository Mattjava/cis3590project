import pandas

raw = pandas.read_csv('biscayne_bay_dataset_oct_2022.csv')

len = len(raw)

print("Number of rows originally: " + str(len))

temp_data = raw['Temperature (C)']
ph_data = raw['pH']
odo_data = raw['ODO (mg/L)']

temp_mean = temp_data.mean()
temp_sd = temp_data.std()

ph_mean = ph_data.mean()
ph_sd = ph_data.std()

odo_mean = odo_data.mean()
odo_sd = odo_data.std()

dropped_rows = 0

for i in range(0, len):
    row = raw.iloc[i]

    temp = row['Temperature (C)']
    odo = row['ODO (mg/L)'] 
    ph = row['pH']

    temp_z = abs((temp - temp_mean) / temp_sd)
    odo_z = abs((odo - odo_mean) / odo_sd)
    ph_z = abs((ph - ph_mean) / ph_sd)

    if temp_z > 3 or odo_z > 3 or ph_z > 3:
        print(f"DROP {i}TH ROW!")
        dropped_rows += 1

print("Number of rows dropped: " + str(dropped_rows))






