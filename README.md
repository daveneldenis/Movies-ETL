# Movies-ETL

Objectives
The goals of this challenge are for you to:

Create an automated ETL pipeline.
Extract data from multiple sources.
Clean and transform the data automatically using Pandas and regular expressions.
Load new data into PostgreSQL.

For this task, assume that the updated data will stay in the same formats: Wikipedia data in JSON format and Kaggle metadata and rating data in CSV formats. Follow these steps:

Create a function that takes in three arguments:
Wikipedia data
Kaggle metadata
MovieLens rating data (from Kaggle)

Use the code from your Jupyter Notebook so that the function performs all of the transformation steps. Remove any exploratory data analysis and redundant code.

Add the load steps from the Jupyter Notebook to the function. You’ll need to remove the existing data from SQL, but keep the empty tables.
Check that the function works correctly on the current Wikipedia and Kaggle data.

Document any assumptions that are being made. Use try-except blocks to account for unforeseen problems that may arise with new data.

Presents a cohesive written analysis that documents 5+ valid assumptions.
Assumption 1: All data is being captured with the function set in Jupyter Notebook
Assumption 2: JSON data format is accessible with the function used and cleaned to give the accurate data points
Assumption 3: All pertinent data from the CSV files (Kaggle Metadata) is captured with the function to provide accurate data
Assumption 4: All transformation steps are iomportanted accurately to produce one clean combined data set
Assumption 5: The try-except alleviates any issues/errors that would occur during the function run
