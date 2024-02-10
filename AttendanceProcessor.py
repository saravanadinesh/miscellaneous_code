import pandas as pd

# Get the attendance file from Google sheets into python and do some initial cleanup
CUNY_corp_fin_doc_id = "1IP9rkHoW75Q4F77luvTTnOxDUg5-ocQonbSSW7igIPk"
sheet_id = CUNY_corp_fin_doc_id
doc_name = "https://docs.google.com/spreadsheets/export?id={}&exportFormat=csv".format(sheet_id)
df = pd.read_csv(doc_name)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%d/%m/%Y %H:%M:%S")
df.rename(columns={"Add your exact numeric numeric-digit CUNY ID#.":"name", "Timestamp":"timestamp", "Email address":"email"}, inplace=True)
df["name"] = df["name"].str.upper()
df["name"] = df["name"].replace(","," ", regex=True)
df["name"] = df["name"].replace("--"," ", regex=True)
df["name"] = df["name"].replace("-"," ", regex=True)
df["name"] = df["name"].replace("  "," ", regex=True)
df.head()

# Get the student database file from Google sheets
db_doc_id = "1m3i5FQx5x1svVnHH1yfFXbiYVtABXbcJgNZyUdM4c5o"
db_doc_name = "https://docs.google.com/spreadsheets/export?id={}&exportFormat=csv".format(db_doc_id)
db = pd.read_csv(db_doc_name, keep_default_na=False)
db.head()

# Remove duplicates
db.drop_duplicates(inplace=True)
indexes_to_drop = []
for index, ref_data in db.iterrows():
    ref_name_set = set(ref_data["Name"].split())
    for cindex, comp_data  in db.iterrows():
        comp_name_set = set(comp_data["Name"].split())
        if ref_name_set.issubset(comp_name_set):
            if index != cindex:
                indexes_to_drop.append(cindex)

db.drop(db.index[indexes_to_drop], inplace=True)
                
# Populate the student database
## Get email IDs of everyone
for index, ref_data in db.iterrows():
    ref_name_set = set(ref_data["Name"].split())
    for rindex, raw_data  in df.iterrows():
        raw_name_set = set(raw_data["name"].split())
        if ref_name_set.issubset(raw_name_set): # If the raw data first name, last name order is different, this will still work
            if len(ref_data["Email IDs"]) == 0:
                db.loc[index, "Email IDs"] = raw_data["email"]
                continue
            if set([raw_data["email"]]).issubset(set([ref_data["Email IDs"]])):     # If we already have the email ID in the student database, we ignore it
                continue
            else:
                db.loc[index, "Email IDs"] = db.loc[index, "Email IDs"]+" "+ raw_data["email"]

# Create the attendance record
unique_dates = list(df["timestamp"].dt.date.unique())
unique_dates_str = list(df["timestamp"].dt.strftime(date_format="%d-%m-%Y").unique())
unique_dates_str = list(filter(lambda x: type(x) == str , unique_dates_str))    # Remove nan
ar_col_names = ["Name", "Email IDs", "Attendance (%)"] + unique_dates_str
ar = pd.DataFrame(columns=ar_col_names)

ar["Name"] = db["Name"]
ar["Email IDs"] = db["Email IDs"]
ar["Attendance (%)"] = 0

# Record attendence for each class
for col_index, timestamp in enumerate(unique_dates):
    email_list = list(df.loc[df["timestamp"].dt.date == timestamp, "email"])
    for index, ar_data in ar.iterrows():
        if len(set(ar_data["Email IDs"].split(" ")).intersection(set(email_list))) > 0:
            ar.loc[index, unique_dates_str[col_index]] = "Y"
            ar.loc[index, "Attendance (%)"] = ar.loc[index, "Attendance (%)"] + (100/len(unique_dates_str))

ar.to_csv('attendance_record.csv')

