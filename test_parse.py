from llama_parse import LlamaParse

from sqlalchemy import create_engine



# Create a database connection
engine = create_engine('sqlite:///parsed_data.db')


import sqlite3
import re

def extract_markdown_tables(markdown):
    # Extract all markdown tables using regular expressions
    tables = re.findall(r"(\|.*?\|(?:\n\|.*?\|)+)", markdown, re.DOTALL)
    return tables

def markdown_to_sqlite(markdown_table, db_name, table_name):
    # Connect to SQLite database (it will create the db file if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Split the markdown table into lines
    lines = markdown_table.strip().split("\n")
    
    # Extract the column headers
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    
    # Detect basic column types based on data in the first row
    first_data_line = lines[2]  # Assuming first data line comes after the separator
    first_row = [r.strip() for r in first_data_line.split("|") if r.strip()]
    
    # Infer column types from the first data row (using basic type inference)
    column_types = []
    for value in first_row:
        if value.isdigit():
            column_types.append("INT")
        elif re.match(r"^\d+(\.\d+)?$", value):  # Check if it's a float
            column_types.append("REAL")
        else:
            column_types.append("TEXT")

    # Generate the SQL CREATE TABLE statement
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    for header, col_type in zip(headers, column_types):
        create_table_sql += f"    {header} {col_type},\n"
    create_table_sql = create_table_sql.rstrip(",\n") + "\n);"
    
    # Execute CREATE TABLE
    cursor.execute(create_table_sql)
    
    # Insert data rows (skipping header and separator lines)
    for line in lines[2:]:  # Start from the third line (skip headers and separator)
        if "---" in line:  # Skip separator lines
            continue
        row = [r.strip() for r in line.split("|") if r.strip()]
        # Prepare the SQL insert statement
        placeholders = ", ".join(["?" for _ in row])
        insert_sql = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({placeholders})"
        cursor.execute(insert_sql, row)
    
    # Commit and close the connection
    conn.commit()
    conn.close()

    return create_table_sql


def save_to_db(documents):
    with engine.connect() as conn:
        for doc in documents:
            conn.execute(
                "INSERT INTO parsed_documents (content) VALUES (?)", (doc.text,)
            )

parsing_instruction="""
This is the pdf containing different columns.
I want to generate a markdown that i can easily convert to sql table.

"""

parser= LlamaParse(
    api_key="llx-dvEB9UEguQEldpE77u96bvLuhbP4oqzdUYNHrK5mMVLsnnKA", 
    result_type="text",
    parsing_instruction=parsing_instruction,
    verbose=True,
)

parsed_doc= parser.load_data('./test_doc.pdf')

# parsed_list= [doc.text for doc in parsed_doc]
# # save_to_db(parsed_doc)

# parsed_filter= extract_markdown_tables(parsed_list[0])

# db_name = "parsed_data.db"
# table_name = "parsed_documents"

#read text file 
# with open('./parsed_doc.txt', 'r') as f:
#     parsed_text = f.read()
# print(parsed_filter)

# create_table_sql = markdown_to_sqlite(parsed_text, db_name, table_name)

#save to markdown
# with open('./parsed_doc.md', 'w') as f:
#     for doc in parsed_doc:
#         f.write(doc.text+ '\n')

with open('./parsed_doc.txt', 'w') as f:
    for doc in parsed_doc:
        f.write(doc.text+ '\n')