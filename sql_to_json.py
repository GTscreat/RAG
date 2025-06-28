import re
import json
from collections import defaultdict

def parse_create_table(lines):
    """
    Վերադարձնում է dict՝ {աղյուսակ: [դաշտ1, դաշտ2, ...]}
    """
    table_columns = {}
    current_table = None
    columns = []
    for line in lines:
        # Սկսում է CREATE TABLE public.news (
        m = re.match(r'CREATE TABLE public\.([a-zA-Z_][\w]*) \(', line)
        if m:
            if current_table and columns:
                table_columns[current_table] = columns
            current_table = m.group(1)
            columns = []
            continue
        # Վերջացնում է աղյուսակը
        if current_table and line.strip().startswith(');'):
            if current_table and columns:
                table_columns[current_table] = columns
            current_table = None
            columns = []
            continue
        # Ավելացնում է դաշտի անունը
        if current_table and line.strip() and not line.strip().startswith('--'):
            mcol = re.match(r'\s*"?(?P<colname>[a-zA-Z_][\w]*)"?\s+', line)
            if mcol:
                columns.append(mcol.group('colname'))
    return table_columns

def split_values(values_str):
    vals = []
    depth = 0
    cur = ''
    in_str = False
    prev = ''
    for c in values_str:
        if c == "'" and prev != '\\':
            in_str = not in_str
        if c == '(' and not in_str:
            if depth == 0:
                cur = ''
            depth += 1
        if depth > 0:
            cur += c
        if c == ')' and not in_str:
            depth -= 1
            if depth == 0:
                vals.append(cur)
        prev = c
    return vals

def parse_row(row_str):
    vals = []
    cur = ''
    in_str = False
    prev = ''
    i = 0
    while i < len(row_str):
        c = row_str[i]
        if c == "'" and prev != '\\':
            in_str = not in_str
            cur += c
        elif c == ',' and not in_str:
            vals.append(cur.strip())
            cur = ''
        else:
            cur += c
        prev = c
        i += 1
    if cur:
        vals.append(cur.strip())
    res = []
    for v in vals:
        v = v.strip()
        if v.upper() == 'NULL':
            res.append(None)
        elif v.startswith("'") and v.endswith("'"):
            val = v[1:-1].replace("\\'", "'").replace('\\"', '"')
            res.append(val)
        elif re.match(r'^-?\d+\.\d+$', v):
            res.append(float(v))
        elif re.match(r'^-?\d+$', v):
            res.append(int(v))
        else:
            res.append(v)
    return res

def fix_news_row(row):
    # news աղյուսակի համար՝ դաշտերի վերանվանում, meta json-ի դաշտը dict դարձնել
    if "meta" in row and isinstance(row["meta"], str):
        try:
            row["meta"] = json.loads(row["meta"])
        except Exception:
            row["meta"] = None
    if "website_id" in row:
        # Եթե պետք է փոխել website_id-ը website (անունով), այստեղ կարող եք ավելացնել մեփփինգ
        pass
    return row

def sql_to_json(sql_path):
    with open(sql_path, encoding='utf-8') as f:
        lines = f.readlines()
    table_columns = parse_create_table(lines)
    table_data = defaultdict(list)
    for line in lines:
        insert_match = re.match(r"INSERT INTO public\.([a-zA-Z_][\w]*) VALUES (.*);", line.strip())
        if insert_match:
            table = insert_match.group(1)
            values_str = insert_match.group(2)
            values_list = split_values(values_str)
            for value_row in values_list:
                row = parse_row(value_row[1:-1])  # հանում է '(' և ')'
                columns = table_columns.get(table)
                if columns and len(columns) == len(row):
                    row_dict = dict(zip(columns, row))
                else:
                    row_dict = {f"col{i+1}": v for i, v in enumerate(row)}
                # Մասնավոր փոփոխումներ news աղյուսակի համար
                if table == "news":
                    row_dict = fix_news_row(row_dict)
                table_data[table].append(row_dict)
    # Արտահանում է տվյալները
    for table, rows in table_data.items():
        json_path = f"{table}.json"
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"Converted {len(rows)} rows from '{table}' to '{json_path}'")

if __name__ == "__main__":
    sql_to_json("data/scrapped.sql")  # փոխեք ձեր SQL ֆայլի անունով