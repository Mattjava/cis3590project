import pandas, os
from pandas.api.types import is_numeric_dtype

data_files = os.listdir("data")

result = {}

for file in data_files:
    file_path = os.path.join("data", file)

    df = pandas.read_csv(file_path)
    clean = df

    columns = df.columns.to_list()

    numeric_columns = [column for column in columns if is_numeric_dtype(df[column])]


    mean_dict = {}
    std_dict = {}


    for column in numeric_columns:
        mean_dict[column] = float(df[column].mean())
        std_dict[column] = float(df[column].std())

        if std_dict[column] == 0.0:
            numeric_columns.remove(column)

    print(numeric_columns)

    for i in range(0, len(df)):
        try:
            row = df.iloc[i]
        except Exception:
            break

        for column in numeric_columns:
            value = row[column]
            try:
                zscore = (value - mean_dict[column]) / std_dict[column]
            except Exception:
                continue

            if abs(zscore) > 3:
                clean.drop(i)
                break

    print(f"Dropped {len(df) - len(clean)} rows from {file}")
    result[file] = clean

