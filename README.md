# Water Quality Project

## What is it about?

This project aims at cleaning water quality data and displaying it in a clean fashion. This involves removing any outliers with Pandas and then displaying the resulting data through an API and frontend interface.

## How did you clean the data.

To clean the data, we have to remove outliters in each data-set. To identify these outliers, we use a z-score for each row and their column. The z-score is a number that can be calculated with the function (x - m) / std. The "m" variable refers to the mean of the current column, and the "std" variable refers to that column's standard deviation.

First, the program calculates the mean and standard deviation of each column. From there, it goes through each row in the data-set. It calculates the z-score for each value that corresponds to a column. If it detects that a value is an outlier, it drops the row from the data-set. At the end, the resulting data-set is a copy of the previous set without outliters.

## How does the API work?

The API includes multiple endpoints the user can connect to. Here is a list of a few examples.

### /api/health/
Checks the health of the API and see if it is working

### /api/observations/
Returns a document based off of the cleaned data. The user is able to implement parameters to change the document.

### /api/statisics/

Returns a complete JSON file containing the statistical information of the clean data set. This includes the mean, standard deviation, and other significant values.

### /api/outliers/?field=<field_name>&method=<method_name>&k=<k_value>

Makes the API recheck a set or field (indicated by the field_name parameter) for any outliers. The user is able to use certain methods such as IQR to check for outliers through the method_name parameter. They're also able to set a value of K (in the k_value parameter) for certain methods.

## Set-up
There are multiple ways to run some of the files in this repository. 

### Data Cleaner (cleaner.py)
If you wish to run the data cleaner, please run cleaner.py. Make sure you have installed the requirements in requirements.txt before running.

### MongoDB (db.py)
If you want to save data into a MongoDB cluster, make an .env file in your local repository. There, copy and paste the link of your MongoDB cluster to a variable called "MONGO_URL" in the environment file. Once that is done, run db.py. It will instantly run cleaner.py to generate the clean data, so you don't need to run cleaner.py

### Flask API (/api/api.py)
Similar to db.py, make an .env file, paste your MongoDB cluster link, and then run the file directly. If you want to try out the API, either visit the link the Flask framework provides or use a tool like Postman.

### Client-side interface (client/frontend.py)
To run this file, please run the API in the background. The client needs the API to grab and use the clean data. Look back at the previous step for more information. Once you have the API up and running, run the file.

## Credits

This project is created by @Mattjava and @dpuer on GitHub.