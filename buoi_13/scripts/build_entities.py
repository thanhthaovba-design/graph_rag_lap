import pandas as pd
import os

def main():
    base_dir = "data"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Read files
    try:
        risk_profiles = pd.read_csv(os.path.join(base_dir, "risk_profiles_seed.csv"))
        controls = pd.read_csv(os.path.join(base_dir, "controls_seed.csv"))
        risk_events = pd.read_csv(os.path.join(base_dir, "risk_events_seed.csv"))
        relationships = pd.read_csv(os.path.join(base_dir, "relationships_seed.csv"))
    except FileNotFoundError as e:
        print(f"Error reading data: {e}")
        return

    entities_list = []
    
    # 1. RuiRo
    for _, row in risk_profiles.iterrows():
        entity = row.to_dict()
        entity['type'] = 'RuiRo'
        entity['source_file'] = 'risk_profiles_seed.csv'
        entities_list.append(entity)

    # 2. KiemSoat
    for _, row in controls.iterrows():
        entity = row.to_dict()
        entity['type'] = 'KiemSoat'
        entity['source_file'] = 'controls_seed.csv'
        entities_list.append(entity)
        
    # 3. SuKienRuiRo
    for _, row in risk_events.iterrows():
        entity = row.to_dict()
        entity['type'] = 'SuKienRuiRo'
        entity['source_file'] = 'risk_events_seed.csv'
        # Mappings specific to risk events
        if 'description' in entity and 'name' not in entity:
            entity['name'] = f"Sự kiện {entity['id']}"
        entities_list.append(entity)

    entities_df = pd.DataFrame(entities_list)
    
    # Ensure minimum schema columns are present
    min_schema = ['id', 'type', 'name', 'description', 'source_file', 'data_origin', 'verification_status']
    for col in min_schema:
        if col not in entities_df.columns:
            entities_df[col] = ''
            
    # Reorder columns to have min_schema first, retaining all business properties
    other_cols = [c for c in entities_df.columns if c not in min_schema]
    entities_df = entities_df[min_schema + other_cols]
    
    # Write entities.csv
    entities_df.to_csv(os.path.join(output_dir, "entities.csv"), index=False)
    
    # Process relationships
    relations_min_schema = ['source_id', 'relationship_type', 'target_id', 'source', 'evidence_quote', 'confidence', 'verification_status', 'data_origin']
    relations_df = relationships.copy()
    
    for col in relations_min_schema:
        if col not in relations_df.columns:
            relations_df[col] = ''
            
    # Filter to only min schema properties as per requirement
    relations_df = relations_df[relations_min_schema]
    
    # Write relations.csv
    relations_df.to_csv(os.path.join(output_dir, "relations.csv"), index=False)
    
    # Reporting
    print("--- Entities Summary ---")
    type_counts = entities_df['type'].value_counts()
    for t, count in type_counts.items():
        print(f"{t}: {count}")
        
    print("\n--- Relations Summary ---")
    rel_counts = relations_df['relationship_type'].value_counts()
    for r, count in rel_counts.items():
        print(f"{r}: {count}")
        
    # Check for orphan references
    print("\n--- Orphan References Check ---")
    all_entity_ids = set(entities_df['id'].dropna())
    
    missing_source = relations_df[~relations_df['source_id'].isin(all_entity_ids)]['source_id'].dropna().unique()
    missing_target = relations_df[~relations_df['target_id'].isin(all_entity_ids)]['target_id'].dropna().unique()
    
    has_orphans = False
    if len(missing_source) > 0:
        print(f"ERROR: Found {len(missing_source)} orphan source_id(s) in relations.csv: {missing_source}")
        has_orphans = True
    if len(missing_target) > 0:
        print(f"ERROR: Found {len(missing_target)} orphan target_id(s) in relations.csv: {missing_target}")
        has_orphans = True
        
    if not has_orphans:
        print("No orphan references found. All source_id and target_id exist in entities.csv.")

if __name__ == "__main__":
    main()
