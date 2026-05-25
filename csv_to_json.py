import pandas as pd
import json

def csv_to_json():
    df = pd.read_csv('outputs/extract_results/records_validated.csv')
    
    json_data = df.to_dict('records')
    
    with open('outputs/extract_results/structured_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"Converted {len(json_data)} records to structured_data.json")

if __name__ == '__main__':
    csv_to_json()
