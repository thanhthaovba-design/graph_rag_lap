import pandas as pd
import os

def inspect_csv(file_path):
    print(f"--- Inspecting {file_path} ---")
    if not os.path.exists(file_path):
         print(f"File {file_path} not found.")
         return None
    df = pd.read_csv(file_path)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    print(f"Primary key check ('id' column): {'Present' if 'id' in df.columns else 'Missing'}")
    
    if 'id' in df.columns:
        dupe_ids = df['id'].duplicated().sum()
        if dupe_ids > 0:
            print(f"Duplicate 'id' values: {dupe_ids}")
            
    # Check nulls
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        print("Null values:")
        for col, count in nulls.items():
            print(f"  - {col}: {count}")
    else:
        print("Null values: 0")
        
    print(f"Duplicate rows: {df.duplicated().sum()}")
    print()
    return df

def check_foreign_keys(source_df, source_col, target_df, target_col, desc):
    if source_df is None or target_df is None: return
    missing = source_df[~source_df[source_col].isin(target_df[target_col])][source_col].dropna().unique()
    if len(missing) > 0:
        print(f"Missing foreign keys ({desc}): {len(missing)} values (e.g., {missing[:3]})")
    else:
        print(f"Missing foreign keys ({desc}): 0")

def main():
    base_dir = "data"
    
    risk_profiles = inspect_csv(os.path.join(base_dir, "risk_profiles_seed.csv"))
    controls = inspect_csv(os.path.join(base_dir, "controls_seed.csv"))
    risk_events = inspect_csv(os.path.join(base_dir, "risk_events_seed.csv"))
    relationships = inspect_csv(os.path.join(base_dir, "relationships_seed.csv"))
    
    if relationships is not None:
        print("--- Relationship Types ---")
        if 'relationship_type' in relationships.columns:
            types = relationships['relationship_type'].value_counts()
            for t, c in types.items():
                print(f"  - {t}: {c}")
        print()
    
    print("--- Foreign Key Checks ---")
    if relationships is not None:
        all_ids = set()
        if risk_profiles is not None: all_ids.update(risk_profiles['id'])
        if controls is not None: all_ids.update(controls['id'])
        if risk_events is not None: all_ids.update(risk_events['id'])
        
        missing_source = relationships[~relationships['source_id'].isin(all_ids)]['source_id'].dropna().unique()
        missing_target = relationships[~relationships['target_id'].isin(all_ids)]['target_id'].dropna().unique()
        
        print(f"Missing source_ids in relationships: {len(missing_source)} {missing_source[:3] if len(missing_source) > 0 else ''}")
        print(f"Missing target_ids in relationships: {len(missing_target)} {missing_target[:3] if len(missing_target) > 0 else ''}")
        
    if risk_events is not None and risk_profiles is not None:
        check_foreign_keys(risk_events, 'risk_id', risk_profiles, 'id', 'risk_events.risk_id -> risk_profiles.id')

if __name__ == "__main__":
    main()
