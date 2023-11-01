import os
import openai
import gradio as gr
import csv
import re
import datetime

# Set your OpenAI API key
openai.api_key = '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'

# Load data from the CSV file when the application starts
data = None

def load_training_data():
    global data
    if data is None:
        data = {}
        with open("docs/your_data.csv", "r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                plate_number = row.get("رقم المركبة", "").strip()
                company_name = row.get("اسم الشركه", "").strip()
                date = row.get("تاريخ الدخول", "").strip()

                if plate_number not in data:
                    data[plate_number] = []
                data[plate_number].append(row)

                if company_name not in data:
                    data[company_name] = []
                data[company_name].append(row)

                if date not in data:
                    data[date] = []
                data[date].append(row)

# Create a function to search for partial matches in company names and dates
def search_partial_matches(input_text):
    input_text = input_text.strip()
    matching_records = {}
    for key in data.keys():
        if input_text in key:
            matching_records[key] = data[key]
    return matching_records

# Create a function to interact with the chatbot using the OpenAI model
def chatbot(input_text):
    load_training_data()
    matching_records = search_partial_matches(input_text)

    # Initialize total money
    total_money = 0

    def calculate_total_money_this_week():
        load_training_data()

        # Get the current date
        current_date = datetime.date(2023, 11, 1)
        
        # Calculate the start date for the current week (Saturday)
        start_date = current_date - datetime.timedelta(days=current_date.weekday() % 7)
        
        # Filter records for this week's dates
        total_money_week = 0
        for key, records in data.items():
            for info in records:
                entry_date = datetime.datetime.strptime(info.get("تاريخ الدخول", ""), "%d.%m.%Y").date()
                if start_date <= entry_date <= current_date:
                    report = info.get("تقرير نهائي", "")
                    money_values = re.findall(r'(\d+)\s*شيكل', report)
                    money_values = [int(value) for value in money_values]
                    total_money_week += sum(money_values)

        return total_money_week

    # Filter records based on the presence of "شيكل" inside the "تقرير نهائي" field
    filtered_records = {}
    for key, records in matching_records.items():
        filtered_records[key] = [info for info in records if "شيكل" in info.get("تقرير نهائي", "")]

    if filtered_records:
        responses = []
        for key, records in filtered_records.items():
            for info in records:
                response = "\n".join([f"{key}: {value}" for key, value in info.items()])
                responses.append(response)
                # Extract and accumulate the money from the final report
                report = info.get("تقرير نهائي", "")
                money_values = re.findall(r'(\d+)\s*شيكل', report)
                money_values = [int(value) for value in money_values]
                total_money += sum(money_values)

        # Calculate total money for this week
        total_money_week = calculate_total_money_this_week()

        # Add total money to the response
        num_records_found = f"Number of records found: {len(responses)}"
        total_money_str = f"Total Money: {total_money} شيكل"
        total_money_week_str = f"Total Money this week: {total_money_week} شيكل"

        response = f"{num_records_found} - {total_money_str} - {total_money_week_str}\n\n" + "\n\n---\n\n".join(responses)
        return (num_records_found, response)
    else:
        response = "No matching entries found in the data."
        return response

# Create a Gradio interface for user interaction
iface = gr.Interface(
    fn=chatbot,
    inputs="text",
    outputs=["text", "text"],
    live=True,
    title="شركه ابناء عرفات",
    description="بحث حسب اسم الشركه - التاريخ - نمره الشاحنه",
)

# Start the Gradio interface with the share parameter set to True
iface.launch(share=True)
