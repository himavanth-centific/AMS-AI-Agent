import os

def prune_sql_schema(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pruned_lines = []
    for line in lines:
        clean = line.strip()
        # Remove comments, empty lines, and specific MS SQL noise
        if not clean or clean.startswith('--') or clean.startswith('/*') or clean == 'GO':
            continue
        pruned_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(pruned_lines)
    
    print(f"Original: {len(lines)} lines | Pruned: {len(pruned_lines)} lines")

if __name__ == "__main__":
    prune_sql_schema("db_schema.txt", "db_schema_pruned.txt")