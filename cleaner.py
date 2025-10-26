import pandas, os
from pandas.api.types import is_numeric_dtype, is_any_real_numeric_dtype

data_files = os.listdir("data")
data_files = [file for file in data_files if file.find("CLEANED") == -1]

result = {}

numeric_fields = ["Temperature (c)", "Salinity (ppt)", "ODO mg/L"]

for file in data_files:
    dropped_rows = 0

    file_path = os.path.join("data", file)

    df = pandas.read_csv(file_path)
    clean = df

    print("Current size: " + str(len(df)) + "\n")

    mean_dict = {}
    std_dict = {}


    for column in numeric_fields:
        mean_dict[column] = float(df[column].mean())
        std_dict[column] = float(df[column].std())

    for i in range(0, len(df)):
        try:
            row = df.iloc[i]
        except Exception:
            break

        for column in numeric_fields:
            value = row[column]
            zscore = (value - mean_dict[column]) / std_dict[column]
            if abs(zscore) > 3:
                clean.drop(i, inplace=True)
                dropped_rows += 1
                print(f"Dropped row #{i} in {file}")
                break

    print(f"\nDropped {dropped_rows} rows from {file}")
    print("New size: " + str(len(clean)) + "\n")
    result[file] = clean

    clean.to_csv(f"data/{file.split('.')[0]}_CLEANED.csv")
