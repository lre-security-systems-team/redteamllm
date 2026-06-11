import os
import json
import pandas as pd

def parse_header_fields(file_path):
    """
    Parses ONLY the following fields from the top lines:
      TOTAL_INPUT_TOKEN, TOTAL_COMPLETION_TOKENS, TOTAL_TOKEN,
      TOTAL_TOOL_CALL, TOTAL_API_CALLS
    Ignores other lines/fields.
    """
    valid_keys = {
        "TOTAL_INPUT_TOKEN",
        "TOTAL_COMPLETION_TOKENS",
        "TOTAL_TOKEN",
        "TOTAL_TOOL_CALL",
        "TOTAL_API_CALLS",
    }
    fields = {
        "TOTAL_INPUT_TOKEN": "",
        "TOTAL_COMPLETION_TOKENS": "",
        "TOTAL_TOKEN": "",
        "TOTAL_TOOL_CALL": "",
        "TOTAL_API_CALLS": ""
    }
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                break
            parts = line.split(":", 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                if key in valid_keys:
                    fields[key] = value
    return fields

def walk_directory_and_build_dict(root_path):
    """
    Walk the given `root_path` and build a nested dictionary
    with the structure:
       {
         <dirname>: {
             "no_reason": {
                 "saved_1": {
                     "act": {the 5 fields},
                     "reason": {the 5 fields},
                     "summarizer": {the 5 fields},
                     "stop_reason": {the 5 fields}
                 },
                 "saved_2": { ... },
                 ...
             },
             "reason": {
                 ...
             }
         },
         <other-top-level-dirs>: ...
       }
    """
    result = {}

    for entry in os.scandir(root_path):
        if entry.is_dir():
            top_dir = entry.name  # e.g., "westside"
            top_dir_full_path = os.path.join(root_path, top_dir)
            result[top_dir] = {}

            # Look for "no_reason" and "reason" directories under top_dir
            for sub_entry in os.scandir(top_dir_full_path):
                if sub_entry.is_dir():
                    sub_dir_name = sub_entry.name.lower()  # "no_reason" or "reason"
                    sub_dir_full_path = os.path.join(top_dir_full_path, sub_entry.name)

                    result[top_dir][sub_dir_name] = {}

                    # Inside "no_reason"/"reason", find "saved_#" subdirs
                    for saved_entry in os.scandir(sub_dir_full_path):
                        if saved_entry.is_dir() and saved_entry.name.startswith("saved_"):
                            saved_dir_name = saved_entry.name  # e.g., "saved_1"
                            saved_dir_full_path = os.path.join(sub_dir_full_path, saved_dir_name)
                            result[top_dir][sub_dir_name][saved_dir_name] = {}

                            # Parse *.txt files
                            for file_entry in os.scandir(saved_dir_full_path):
                                if file_entry.is_file() and file_entry.name.lower().endswith(".txt"):
                                    file_path = os.path.join(saved_dir_full_path, file_entry.name)

                                    # Base name without extension; ignore case
                                    base_name = os.path.splitext(file_entry.name)[0]
                                    base_name_lower = base_name.lower()

                                    # stop_reason -> if filename includes "stop_reason" or "failure_reason"
                                    if "stop_reason" in base_name_lower or "failure_reason" in base_name_lower:
                                        key_name = "stop_reason"
                                    else:
                                        # otherwise, use the base name (act, reason, summarizer, etc.)
                                        key_name = base_name_lower

                                    parsed_fields = parse_header_fields(file_path)
                                    result[top_dir][sub_dir_name][saved_dir_name][key_name] = parsed_fields

    return result

def flatten_nested_dict_to_rows(data):
    """
    Takes the nested dictionary (from walk_directory_and_build_dict) and yields
    rows of the form:

      (
        top_dir,
        reason_type (e.g. "no_reason" or "reason"),
        saved_dir,
        file_type (e.g. "act", "reason", "summarizer", "stop_reason"),
        TOTAL_INPUT_TOKEN,
        TOTAL_COMPLETION_TOKENS,
        TOTAL_TOKEN,
        TOTAL_TOOL_CALL,
        TOTAL_API_CALLS
      )
    """
    for top_dir, reason_dict in data.items():
        for reason_type, saved_dict in reason_dict.items():
            for saved_dir, file_dict in saved_dict.items():
                for file_type, field_values in file_dict.items():
                    yield (
                        top_dir,
                        reason_type,
                        saved_dir,
                        file_type,
                        field_values.get("TOTAL_INPUT_TOKEN", ""),
                        field_values.get("TOTAL_COMPLETION_TOKENS", ""),
                        field_values.get("TOTAL_TOKEN", ""),
                        field_values.get("TOTAL_TOOL_CALL", ""),
                        field_values.get("TOTAL_API_CALLS", "")
                    )

def main():
    # Change this to your actual directory containing top-level folders (e.g., "westside").
    root_path = "/home/brian/Desktop/recherche-LLM/redteamllm/results"

    # 1. Walk directory and build the nested dictionary
    nested_data = walk_directory_and_build_dict(root_path)

    # 2. Flatten it into rows
    rows = list(flatten_nested_dict_to_rows(nested_data))

    # 3. Create a DataFrame
    columns = [
        "top_dir",
        "reason_type",
        "saved_dir",
        "file_type",
        "TOTAL_INPUT_TOKEN",
        "TOTAL_COMPLETION_TOKENS",
        "TOTAL_TOKEN",
        "TOTAL_TOOL_CALL",
        "TOTAL_API_CALLS",
    ]
    df = pd.DataFrame(rows, columns=columns)

    # 4. Export to Excel
    output_excel_path = os.path.join(root_path, "output_data.xlsx")
    df.to_excel(output_excel_path, index=False)
    print(f"Data written to {output_excel_path}")

if __name__ == "__main__":
    main()
