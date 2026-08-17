import pandas as pd
import os
import re
import sys

def sanitize_filename(name):
    # keep it simple, remove very illegal chars for windows
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    entities_df = pd.read_csv("outputs/entities.csv")
    relations_df = pd.read_csv("outputs/relations.csv")
    
    # Fill NA to empty string for safety
    entities_df = entities_df.fillna('')
    relations_df = relations_df.fillna('')
    
    # Create dicts
    entities = {}
    for _, row in entities_df.iterrows():
        entities[row['id']] = row.to_dict()
        # Create sanitized filename
        entities[row['id']]['filename'] = sanitize_filename(row['name'])
        
    # We'll store relation links in the entities
    for k in entities.keys():
        entities[k]['incoming_rels'] = []
        entities[k]['outgoing_rels'] = []
        
    for _, rel in relations_df.iterrows():
        src = rel['source_id']
        tgt = rel['target_id']
        if src in entities and tgt in entities:
            rel_info = rel.to_dict()
            entities[src]['outgoing_rels'].append(rel_info)
            entities[tgt]['incoming_rels'].append(rel_info)
            
    # Create directories
    dirs = ['wiki', 'wiki/risks', 'wiki/controls', 'wiki/events']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    total_pages = 0
    total_links = 0
    
    def write_md(filepath, content):
        nonlocal total_pages
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        total_pages += 1
        
    def count_links(content):
        nonlocal total_links
        total_links += len(re.findall(r'\[\[.*?\]\]', content))

    # Helper for relations string
    def format_rel(rel, target_entity):
        # target_entity is the one we link to
        link = f"[[{target_entity['filename']}]]"
        details = []
        if rel['evidence_quote']:
            details.append(f"Evidence: {rel['evidence_quote']}")
        if rel['verification_status']:
            details.append(f"Status: {rel['verification_status']}")
        
        detail_str = f" ({', '.join(details)})" if details else ""
        return f"- {rel['relationship_type']} {link}{detail_str}"

    risks = [e for e in entities.values() if e['type'] == 'RuiRo']
    controls = [e for e in entities.values() if e['type'] == 'KiemSoat']
    events = [e for e in entities.values() if e['type'] == 'SuKienRuiRo']

    # Generate Risks
    for r in risks:
        content = f"""---
id: {r['id']}
type: {r['type']}
verification_status: {r['verification_status']}
data_origin: {r['data_origin']}
---
# {r['name']}

**ID**: {r['id']}
**Category**: {r.get('category', '')}
**Owner Unit ID**: {r.get('owner_unit_id', '')}
**Inherent Level**: {r.get('inherent_level', '')}
**Residual Level**: {r.get('residual_level', '')}

## Mô tả
{r.get('description', '')}

## Nguyên nhân (Cause)
{r.get('cause', '')}

## Sự kiện (Event)
{r.get('event', '')}

## Tác động (Impact)
{r.get('impact', '')}

## Kiểm soát liên quan
"""
        has_controls = False
        for rel in r['incoming_rels']:
            if rel['relationship_type'] == 'MITIGATES':
                ctrl = entities[rel['source_id']]
                content += format_rel(rel, ctrl) + "\n"
                has_controls = True
        if not has_controls:
            content += "Không có kiểm soát nào.\n"
            
        content += "\n## Sự kiện liên quan\n"
        has_events = False
        for rel in r['outgoing_rels']:
            if rel['relationship_type'] == 'OBSERVED_AS':
                evt = entities[rel['target_id']]
                content += format_rel(rel, evt) + "\n"
                has_events = True
        if not has_events:
            content += "Không có sự kiện nào.\n"

        count_links(content)
        write_md(os.path.join("wiki/risks", f"{r['filename']}.md"), content)

    # Generate Controls
    for c in controls:
        content = f"""---
id: {c['id']}
type: {c['type']}
verification_status: {c['verification_status']}
data_origin: {c['data_origin']}
---
# {c['name']}

**ID**: {c['id']}
**Control Type**: {c.get('control_type', '')}
**Frequency**: {c.get('frequency', '')}
**Effectiveness**: {c.get('effectiveness', '')}
**Owner Role ID**: {c.get('owner_role_id', '')}

## Rủi ro được giảm thiểu
"""
        has_risks = False
        for rel in c['outgoing_rels']:
            if rel['relationship_type'] == 'MITIGATES':
                rsk = entities[rel['target_id']]
                content += format_rel(rel, rsk) + "\n"
                has_risks = True
        if not has_risks:
            content += "Không giảm thiểu rủi ro nào.\n"
            
        count_links(content)
        write_md(os.path.join("wiki/controls", f"{c['filename']}.md"), content)

    # Generate Events
    for e in events:
        content = f"""---
id: {e['id']}
type: {e['type']}
verification_status: {e['verification_status']}
data_origin: {e['data_origin']}
---
# {e['name']}

**ID**: {e['id']}
**Occurred At**: {e.get('occurred_at', '')}
**Discovered At**: {e.get('discovered_at', '')}
**Severity**: {e.get('severity', '')}
**Loss Amount VND**: {e.get('loss_amount_vnd', '')}

## Mô tả
{e.get('description', '')}

## Thuộc rủi ro
"""
        has_risks = False
        for rel in e['incoming_rels']:
            if rel['relationship_type'] == 'OBSERVED_AS':
                rsk = entities[rel['source_id']]
                content += format_rel(rel, rsk) + "\n"
                has_risks = True
        if not has_risks:
            content += "Không thuộc rủi ro nào.\n"
            
        count_links(content)
        write_md(os.path.join("wiki/events", f"{e['filename']}.md"), content)

    # Generate Home.md
    home_content = f"""# Trang Chủ Wiki Risk Graph

Đây là hệ thống Wiki quản lý rủi ro.

## Thống kê
- **Tổng số Node (Thực thể)**: {len(entities)}
  - Rủi ro: {len(risks)}
  - Kiểm soát: {len(controls)}
  - Sự kiện: {len(events)}
- **Tổng số Edge (Quan hệ)**: {len(relations_df)}

## Danh sách Rủi ro
"""
    for r in risks:
        home_content += f"- [[{r['filename']}]]\n"
        
    home_content += "\n## Danh sách Kiểm soát\n"
    for c in controls:
        home_content += f"- [[{c['filename']}]]\n"
        
    home_content += "\n## Danh sách Sự kiện rủi ro\n"
    for e in events:
        home_content += f"- [[{e['filename']}]]\n"

    count_links(home_content)
    write_md("wiki/Home.md", home_content)
    
    # Path example output
    print(f"Tổng số trang Wiki đã tạo: {total_pages}")
    print(f"Tổng số wikilink: {total_links}")
    
    # Example Path: Control -> Risk -> Event
    print("\nVí dụ đường đi KiemSoat -> RuiRo -> SuKienRuiRo:")
    example_found = False
    for r in risks:
        if r['incoming_rels'] and r['outgoing_rels']:
            ctrl_rel = next((rel for rel in r['incoming_rels'] if rel['relationship_type'] == 'MITIGATES'), None)
            evt_rel = next((rel for rel in r['outgoing_rels'] if rel['relationship_type'] == 'OBSERVED_AS'), None)
            if ctrl_rel and evt_rel:
                ctrl_name = entities[ctrl_rel['source_id']]['name']
                risk_name = r['name']
                evt_name = entities[evt_rel['target_id']]['name']
                print(f"[{ctrl_name}] --MITIGATES--> [{risk_name}] --OBSERVED_AS--> [{evt_name}]")
                example_found = True
                break
    if not example_found:
        print("Không tìm thấy đường đi hoàn chỉnh nào.")

if __name__ == "__main__":
    main()
