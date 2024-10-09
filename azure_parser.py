import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from openai import AzureOpenAI
# from azure.ai.formrecognizer import DocumentAnalysisClient
#load from .env file
import json
from tabulate import tabulate

from dotenv import load_dotenv
load_dotenv()


import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

#load from environment variables
AZURE_FORM_RECOGNIZER_ENDPOINT= os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
AZURE_FORM_RECOGNIZER_KEY= os.getenv("AZURE_FORM_RECOGNIZER_KEY")


openai_api_base = os.environ.get('OPENAI_API_ENDPOINT') 
openai_api_version = os.environ.get('OPENAI_API_VERSION') 
openai_api_type = os.environ.get('OPENAI_API_TYPE') 
openai_api_key = os.environ.get('OPENAI_API_KEY') 

client_openai = AzureOpenAI(
    azure_endpoint=openai_api_base,
    api_key=openai_api_key,
    api_version="2024-02-01",
)

deployment_model= "gpt-4-2024"

def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result


def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (
            word.span.offset + word.span.length
        ) <= (span.offset + span.length):
            return True
    return False


def analyze_layout():
    # sample document
    formUrl = "https://raw.githubusercontent.com/bimalb58/azureIntelligence//main/test_doc.pdf"

    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT, credential=AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY)
    )

    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout", AnalyzeDocumentRequest(url_source=formUrl
    ))
    # with open(pdf_path, "rb") as f:
    #     poller = document_intelligence_client.begin_analyze_document(
    #         "prebuilt-layout", AnalyzeDocumentRequest(url_source=f)
    #     )
    result: AnalyzeResult = poller.result()

    # if result.tables:
    #     for table_idx, table in enumerate(result.tables):
    #         print(
    #             f"Table # {table_idx} has {table.row_count} rows and "
    #             f"{table.column_count} columns"
    #         )
    #         if table.bounding_regions:
    #             for region in table.bounding_regions:
    #                 print(
    #                     f"Table # {table_idx} location on page: {region.page_number} is {region.polygon}"
    #                 )
    #         for cell in table.cells:
    #             print(
    #                 f"...Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'"
    #             )
    #             if cell.bounding_regions:
    #                 for region in cell.bounding_regions:
    #                     print(
    #                         f"...content on page {region.page_number} is within bounding polygon '{region.polygon}'"
    #                     )
    return result.tables

    
    # if result.tables:
    #     import openpyxl
    #     from openpyxl import Workbook
    #     wb = Workbook()
    #     summary_ws = wb.active
    #     summary_ws.title = "Summary"
 
    #     for table_idx, table in enumerate(result.tables):
    #         # Create a new worksheet for each table
    #         ws = wb.create_sheet(title=f"Table_{table_idx}")
 
    #         # Add summary information in the Summary sheet
    #         summary_ws.append([f"Table # {table_idx}", f"{table.row_count} rows", f"{table.column_count} columns"])
    #         if table.bounding_regions:
    #             for region in table.bounding_regions:
    #                 summary_ws.append(
    #                     [f"Table # {table_idx} location on page:", region.page_number, str(region.polygon)])
 
    #         # Add table headers (if any)
    #         headers = [f"Column {i}" for i in range(table.column_count)]
    #         ws.append(headers)
 
    #         # Add cell content
    #         for cell in table.cells:
    #             row_idx = cell.row_index + 2  # Offset by 2 to account for headers and 1-based index
    #             col_idx = cell.column_index + 1  # 1-based index
    #             ws.cell(row=row_idx, column=col_idx, value=cell.content)
    #             if cell.bounding_regions:
    #                 for region in cell.bounding_regions:
    #                     summary_ws.append([
    #                         f"...content on page {region.page_number}",
    #                         f"is within bounding polygon '{region.polygon}'"
    #                     ])
 
    #     # Save the workbook
    #     wb.save("result_tables.xlsx")
 
    # print("Data has been written to 'result_tables.xlsx'")
    
table_metadata= analyze_layout()
# print(f'table metadata is {table_metadata}')

#make nice table out of json data
def json_to_table(json_string):
    try:
        # Parse the JSON string
        data = json.loads(json_string)
        
        # Extract headers from the first item
        headers = list(data[0].keys())
        
        # Extract values from all items
        rows = [list(item.values()) for item in data]
        
        # Create and return the formatted table
        table = tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f")
        print(f'Table created')
        return table
    except json.JSONDecodeError:
        return "Error: Invalid JSON string"
    except IndexError:
        return "Error: Empty JSON array"
    except Exception as e:
        return f"Error: {str(e)}"


def llm_output(table_metadata):
    system_prompt=(
    """
    I have a table metadata generated from azure document intelligence service. The table metadata will be given in the form of user query.
    First try to find all the columns and rows in the table along with the data in each of the column. 
    I have another IDEX database with the following columns: Tool (sometimes called Description), length, weight, and OD (outlier diameter. 
    
    Now I want to extract the data from the table and insert it into the IDEX database. Always see the metric to decide the mapping between the column in the table metadata and IDEX database.
    Make sure that you insert the data into the correct columns.
    Please return the response only as a valid JSON object. Do not add any extra formatting, code blocks, or tags around the JSON. Do not include explanation or other non-JSON content.
    Try to generate the full output from the table metadata. Do not hallucinate or add any extra information. All information should be from `table_metadata`.
    Generate the json output that can be used to insert the data into the IDEX database.
    """
    )
    prompt= f'This is the table metadata {table_metadata}.'
    response = client_openai.chat.completions.create(
        model=deployment_model,
        messages=[{
            "role": "system", "content": system_prompt
        }, {
            "role": "user", "content": prompt
        }])
    return response.choices[0].message.content

data_json= llm_output(table_metadata)

try:
    data = json.loads(data_json)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    print(f"Received data: {data_json}")
    exit(1)

# result= json.dumps(json_output)
# cleaned_data= data.replace("json", "").strip()
# cleaned_data= cleaned_data.replace("```", "").strip()
# print("Result:")
# print(result)
# cleaned_data= json.loads(cleaned_data)

# print(f'cleaned data is {cleaned_data}')

df = pd.DataFrame(data)
print(f'Table:\n {df}')
#save dataframe as csv
df.to_csv('table_metadata.csv', index=False)

# Define a function to save as PNG
def save_as_png(df, filename='table.png'):
    fig, ax = plt.subplots(figsize=(12, len(df)*0.5))  # Adjust the figure size based on rows
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()
    
# # Define a function to save as PDF
# def save_as_pdf(df, filename='table.pdf'):
#     pdf = SimpleDocTemplate(filename, pagesize=letter)
#     table_data = [df.columns.to_list()] + df.values.tolist()
    
#     # Create a table
#     table = Table(table_data)
    
#     # Add style to table
#     style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                         ('GRID', (0, 0), (-1, -1), 1, colors.black)])
#     table.setStyle(style)
    
#     # Build PDF
#     elems = []
#     elems.append(table)
#     pdf.build(elems)

save_as_png(df, 'tools_table.png')