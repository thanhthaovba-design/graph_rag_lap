import os
import glob
import re
import pandas as pd
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    report = ["# Báo cáo Kiểm thử Wiki Risk Graph\n"]
    
    # 1. Tổng số file Markdown
    md_files = glob.glob('wiki/**/*.md', recursive=True)
    report.append(f"- **Tổng số file Markdown**: {len(md_files)}")
    
    # Load entities
    entities_df = pd.read_csv('outputs/entities.csv')
    entities_df = entities_df.fillna('')
    entity_ids = set(entities_df['id'].dropna())
    
    # Check 4. Entity bị trùng ID
    duplicated_ids = entities_df[entities_df.duplicated(['id'])]['id'].tolist()
    if duplicated_ids:
        report.append(f"- **Lỗi [Dữ liệu]**: Entity bị trùng ID: {duplicated_ids}")
    else:
        report.append("- **Entity bị trùng ID**: Không có.")
        
    relations_df = pd.read_csv('outputs/relations.csv')
    
    # Check 6. Relation có source hoặc target không tồn tại
    invalid_sources = relations_df[~relations_df['source_id'].isin(entity_ids)]['source_id'].dropna().tolist()
    invalid_targets = relations_df[~relations_df['target_id'].isin(entity_ids)]['target_id'].dropna().tolist()
    if invalid_sources or invalid_targets:
        report.append(f"- **Lỗi [Dữ liệu]**: Relation có source hoặc target không tồn tại.")
        if invalid_sources: report.append(f"  - Missing sources: {invalid_sources}")
        if invalid_targets: report.append(f"  - Missing targets: {invalid_targets}")
    else:
        report.append("- **Relation có source/target không tồn tại**: Không có.")
        
    total_wikilinks = 0
    broken_links = []
    orphan_pages = []
    invalid_id_pages = []
    
    # Build a list of valid target names for wikilinks (which are file names without .md)
    valid_targets = [os.path.basename(f).replace('.md', '') for f in md_files]
    
    for filepath in md_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse YAML frontmatter for ID
        match = re.search(r'---\nid: (.*?)\n', content)
        if match:
            page_id = match.group(1).strip()
            # Check 5. Trang có ID nhưng không tồn tại trong entities.csv
            if page_id and page_id not in entity_ids:
                invalid_id_pages.append((filepath, page_id))
                
        # Find links
        links = re.findall(r'\[\[(.*?)\]\]', content)
        total_wikilinks += len(links)
        
        # Home.md has links but let's check orphans for others
        if len(links) == 0 and os.path.basename(filepath) != 'Home.md':
            # Check if this page is being linked TO. If not linked to AND has no links, it's orphan.
            # However, prompt says "Trang không có liên kết với trang khác". This implies outgoing links.
            # But let's check if it has ANY links. We checked outgoing.
            orphan_pages.append(filepath)
            
        # Check 3. Wikilink trỏ tới trang không tồn tại
        for link in links:
            if link not in valid_targets:
                broken_links.append((filepath, link))
                
    report.append(f"- **Tổng số wikilink**: {total_wikilinks}")
    
    if invalid_id_pages:
        report.append("- **Lỗi [Chương trình]**: Trang có ID không tồn tại trong entities.csv:")
        for fp, pid in invalid_id_pages:
            report.append(f"  - {fp} (ID: {pid})")
    else:
        report.append("- **Trang có ID không tồn tại trong entities.csv**: Không có.")
        
    if broken_links:
        report.append("- **Lỗi [Chương trình]**: Wikilink trỏ tới trang không tồn tại:")
        for fp, link in broken_links:
            report.append(f"  - Trong {fp} trỏ tới [[{link}]]")
    else:
        report.append("- **Wikilink trỏ tới trang không tồn tại**: Không có.")
        
    if orphan_pages:
        report.append("- **Cảnh báo [Dữ liệu/Chương trình]**: Trang không có liên kết ra bên ngoài (orphan outgoing):")
        for fp in orphan_pages:
            report.append(f"  - {fp}")
    else:
        report.append("- **Trang không có liên kết ra bên ngoài**: Không có.")
        
    # Check 7 & 8: RuiRo không có KiemSoat / SuKien
    risks_without_controls = []
    risks_without_events = []
    
    risk_entities = entities_df[entities_df['type'] == 'RuiRo']['id'].tolist()
    for r_id in risk_entities:
        has_ctrl = relations_df[(relations_df['target_id'] == r_id) & (relations_df['relationship_type'] == 'MITIGATES')].shape[0] > 0
        has_evt = relations_df[(relations_df['source_id'] == r_id) & (relations_df['relationship_type'] == 'OBSERVED_AS')].shape[0] > 0
        if not has_ctrl:
            risks_without_controls.append(r_id)
        if not has_evt:
            risks_without_events.append(r_id)
            
    if risks_without_controls:
        report.append("- **Lỗi [Dữ liệu]**: Rủi ro không có bất kỳ Kiểm soát nào:")
        for r_id in risks_without_controls:
            report.append(f"  - {r_id}")
    else:
        report.append("- **Rủi ro không có Kiểm soát**: Không có.")
        
    if risks_without_events:
        report.append("- **Lỗi [Dữ liệu]**: Rủi ro không có bất kỳ Sự kiện nào:")
        for r_id in risks_without_events:
            report.append(f"  - {r_id}")
    else:
        report.append("- **Rủi ro không có Sự kiện**: Không có.")
        
    # Write report
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/wiki_validation_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
        
    print("Kiểm thử thành công. Kết quả đã được lưu tại outputs/wiki_validation_report.md")

if __name__ == "__main__":
    main()
