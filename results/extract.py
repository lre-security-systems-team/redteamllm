import os
import json

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
    fields = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Stop if we reach a blank line or end of file
            if not line:
                break
            # Example line: TOTAL_INPUT_TOKEN: 107873
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
                     "act": {only 5 fields},
                     "reason": {only 5 fields},
                     "summarizer": {only 5 fields},
                     "stop_reason": {only 5 fields if file is Stop_Reason/Failure_Reason}
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

    # Scan top-level subdirectories in root_path
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

                    # This substructure will hold: {"saved_1": {...}, "saved_2": {...}}
                    result[top_dir][sub_dir_name] = {}

                    # Inside "no_reason"/"reason", find "saved_#" subdirs
                    for saved_entry in os.scandir(sub_dir_full_path):
                        if saved_entry.is_dir() and saved_entry.name.startswith("saved_"):
                            saved_dir_name = saved_entry.name  # e.g. "saved_1"
                            saved_dir_full_path = os.path.join(sub_dir_full_path, saved_dir_name)

                            result[top_dir][sub_dir_name][saved_dir_name] = {}

                            # Inside each "saved_#", parse *.txt files
                            for file_entry in os.scandir(saved_dir_full_path):
                                if file_entry.is_file() and file_entry.name.lower().endswith(".txt"):
                                    file_path = os.path.join(saved_dir_full_path, file_entry.name)

                                    # Base name without extension; ignore case
                                    base_name = os.path.splitext(file_entry.name)[0]
                                    base_name_lower = base_name.lower()

                                    # Any file containing "stop_reason" or "failure_reason" => "stop_reason" key
                                    if "stop_reason" in base_name_lower or "failure_reason" in base_name_lower:
                                        key_name = "stop_reason"
                                    else:
                                        # Otherwise just use the lowercase of the name, e.g. "act", "reason", "summarizer"
                                        key_name = base_name_lower

                                    parsed_fields = parse_header_fields(file_path)
                                    result[top_dir][sub_dir_name][saved_dir_name][key_name] = parsed_fields
    return result

def main():
    # Change this to your actual directory containing top-level folders (e.g., "westside").
    root_path = "/home/brian/Desktop/recherche-LLM/redteamllm/results"

    full_data = walk_directory_and_build_dict(root_path)

    # Write one JSON file per top-level directory
    for top_dir_name, dir_info in full_data.items():
        output_file = os.path.join(root_path, f"{top_dir_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({top_dir_name: dir_info}, f, indent=2)
        print(f"Created JSON: {output_file}")

if __name__ == "__main__":
    main()
