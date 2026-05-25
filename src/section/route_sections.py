import os
import yaml
import csv
from typing import List, Dict, Tuple
from src.crawl.load_config import load_config

def load_section_rules(config_path: str = "configs/section_rules.yaml") -> Dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def find_sections(md_content: str, rules: Dict) -> List[Dict]:
    sections = []
    lines = md_content.split('\n')
    current_section = None
    current_content = []
    
    for i, line in enumerate(lines):
        for section_name, section_rules in rules['target_sections'].items():
            include_keywords = section_rules.get('include_keywords', [])
            exclude_keywords = section_rules.get('exclude_keywords', [])
            min_chars = section_rules.get('min_chars', 100)
            
            has_include = any(kw in line for kw in include_keywords)
            has_exclude = any(kw in line for kw in exclude_keywords)
            
            if has_include and not has_exclude:
                if current_section:
                    if len('\n'.join(current_content)) >= min_chars:
                        sections.append({
                            'section_name': current_section,
                            'content': '\n'.join(current_content),
                            'page_start': i // 50 + 1,
                            'page_end': (i + len(current_content)) // 50 + 1
                        })
                current_section = section_name
                current_content = [line]
            elif current_section:
                current_content.append(line)
    
    if current_section and len('\n'.join(current_content)) >= min_chars:
        sections.append({
            'section_name': current_section,
            'content': '\n'.join(current_content),
            'page_start': 1,
            'page_end': len(current_content) // 50 + 1
        })
    
    return sections

def route_sections(config: Dict, rules_path: str = "configs/section_rules.yaml"):
    parsed_dir = "data/parsed"
    metadata_path = config['output']['metadata']
    report_path = "outputs/logs/section_analysis.log"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    rules = load_section_rules(rules_path)
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = [r for r in reader if r['download_status'] == 'success']
    
    section_counts = {}
    total_sections = 0
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Section Analysis Report\n\n")
        f.write("## Summary\n")
        
        for record in records:
            doc_id = record['doc_id']
            md_path = os.path.join(parsed_dir, f"{doc_id}.md")
            
            if not os.path.exists(md_path):
                continue
            
            with open(md_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read()
            
            found_sections = find_sections(content, rules)
            
            if doc_id not in section_counts:
                section_counts[doc_id] = []
            
            for sec in found_sections:
                section_counts[doc_id].append(sec['section_name'])
                total_sections += 1
                
                f.write(f"### {doc_id} - {sec['section_name']}\n")
                f.write(f"- Page: {sec['page_start']}-{sec['page_end']}\n")
                f.write(f"- Content preview (first 200 chars):\n")
                f.write(f"```\n{sec['content'][:200]}...\n```\n\n")
        
        f.write(f"\n## Statistics\n")
        f.write(f"- Total documents processed: {len(section_counts)}\n")
        f.write(f"- Total sections found: {total_sections}\n")
        
        from collections import Counter
        all_sections = []
        for doc, sections in section_counts.items():
            all_sections.extend(sections)
        section_dist = Counter(all_sections)
        
        f.write("\n## Section Distribution\n")
        for section, count in section_dist.items():
            f.write(f"- {section}: {count}\n")
    
    print(f"Section analysis report saved to {report_path}")
    return section_counts

if __name__ == '__main__':
    config = load_config()
    print("Starting section routing...")
    route_sections(config)