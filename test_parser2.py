import re

def parse_line(line):
    # Split the line and extract relevant data
    parts = re.split(r'\s{2,}', line.strip())
    if len(parts) >= 7:
        return {
            'tool_name': parts[0],
            'outer_diameter': float(parts[1]),
            'length': float(parts[2]),
            'weight_kg': float(parts[3]),
            'supplied_by': parts[4],
            'accumulated_length': float(parts[5])
        }
    return None

def generate_sql_insert(data):
    return f"INSERT INTO tool_string (tool_name, outer_diameter, length, weight_kg, supplied_by, accumulated_length) VALUES ('{data['tool_name']}', {data['outer_diameter']}, {data['length']}, {data['weight_kg']}, '{data['supplied_by']}', {data['accumulated_length']});"

def process_text_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    sql_inserts = []
    for line in lines:
        data = parse_line(line)
        if data:
            sql_inserts.append(generate_sql_insert(data))

    return sql_inserts


file_path= 'parsed_doc.txt'
sql_statements = process_text_file(file_path)

for statement in sql_statements:
    print(statement)