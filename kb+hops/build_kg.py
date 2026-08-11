import sys
import pandas as pd
import json
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

sys.stdout.reconfigure(encoding='utf-8')

# Configure Neo4j connection
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "abcd1234"
DB_NAME = "neo4j"

# Load SentenceTransformer model on CPU
model = SentenceTransformer('thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5', device='cpu')

def clean_and_chunk_html(html_content):
    """
    Cleans HTML and chunks it hierarchically based on headers.
    Returns a list of chunks, where each chunk is a dict:
    { 'chunk_id': str, 'parent_id': str, 'text': str, 'embedding': list }
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Simple chunking logic (could be improved based on actual HTML structure)
    # Extract headers and paragraphs
    chunks = []
    
    # Try to find structural elements (h1, h2, h3, p, table)
    elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table'])
    
    current_parents = {}
    current_chunk_idx = 0
    
    for el in elements:
        text = el.get_text(strip=True)
        if not text:
            continue
            
        chunk = {
            'text': text,
            'tag': el.name
        }
        chunks.append(chunk)

    # Let's assign IDs and relationships
    final_chunks = []
    parent_stack = []
    
    for i, c in enumerate(chunks):
        tag = c['tag']
        chunk_id = f"chunk_{i}"
        
        # Determine level for hierarchy (p and table are lowest level)
        level = 10 
        if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
            level = int(tag[1])
            
        # maintain parent stack
        while parent_stack and parent_stack[-1]['level'] >= level:
            parent_stack.pop()
            
        parent_id = parent_stack[-1]['id'] if parent_stack else None
        
        c_node = {
            'chunk_id': chunk_id,
            'text': c['text'],
            'parent_id': parent_id,
            'next_id': f"chunk_{i+1}" if i < len(chunks)-1 else None
        }
        
        final_chunks.append(c_node)
        
        if tag.startswith('h'):
            parent_stack.append({'id': chunk_id, 'level': level})
            
    # Compute embeddings
    texts = [c['text'] for c in final_chunks]
    if texts:
        embeddings = model.encode(texts)
        for i, emb in enumerate(embeddings):
            final_chunks[i]['embedding'] = emb.tolist()
            
    return final_chunks

def get_session(driver):
    return driver.session(database=DB_NAME)

def load_data():
    # Read files
    print("Loading CSV files...")
    df_meta = pd.read_csv("metadata.csv", encoding="utf-8")
    df_content = pd.read_csv("content.csv", encoding="utf-8")
    df_rel = pd.read_csv("relationships.csv", encoding="utf-8")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with get_session(driver) as session:
        # 1. Create Document nodes
        print("Creating Document nodes...")
        for _, row in df_meta.iterrows():
            props = row.to_dict()
            # replace NaN with None
            props = {k: v for k, v in props.items() if pd.notnull(v)}
            session.run("""
                MERGE (d:Document {id: $id})
                SET d += $props
            """, id=str(props.get('id', '')), props=props)
            
        # 2. Process and create Chunk nodes
        print("Processing HTML content and creating Chunk nodes...")
        for _, row in df_content.iterrows():
            doc_id = str(row['id'])
            html = row['content_html']
            if not isinstance(html, str):
                continue
                
            chunks = clean_and_chunk_html(html)
            print(f"Doc {doc_id}: extracted {len(chunks)} chunks")
            
            # Print sample of the first document to satisfy step 1 requirement
            if _ == 0:
                print("--- Sample Extracted Chunks ---")
                for c in chunks[:5]:
                    print(f"ID: {c['chunk_id']} | Parent: {c['parent_id']} | Text: {c['text'][:50]}...")
                print("-------------------------------")
            
            for c in chunks:
                chunk_node_id = f"{doc_id}_{c['chunk_id']}"
                parent_node_id = f"{doc_id}_{c['parent_id']}" if c['parent_id'] else None
                next_node_id = f"{doc_id}_{c['next_id']}" if c['next_id'] else None
                
                # Create Chunk
                session.run("""
                    MERGE (c:Chunk {id: $id})
                    SET c.text = $text, c.embedding = $embedding
                    WITH c
                    MATCH (d:Document {id: $doc_id})
                    MERGE (c)-[:PART_OF]->(d)
                """, id=chunk_node_id, text=c['text'], embedding=c['embedding'], doc_id=doc_id)
                
                # Create Parent relationship
                if parent_node_id:
                    session.run("""
                        MATCH (child:Chunk {id: $child_id})
                        MERGE (parent:Chunk {id: $parent_id})
                        MERGE (parent)-[:PARENT_OF]->(child)
                    """, child_id=chunk_node_id, parent_id=parent_node_id)
                else:
                    # If no parent chunk, it's top level, parent is Document
                    session.run("""
                        MATCH (child:Chunk {id: $child_id})
                        MATCH (parent:Document {id: $doc_id})
                        MERGE (parent)-[:PARENT_OF]->(child)
                    """, child_id=chunk_node_id, doc_id=doc_id)
                    
                # Create Next relationship
                if next_node_id:
                    session.run("""
                        MATCH (curr:Chunk {id: $curr_id})
                        MERGE (next:Chunk {id: $next_id})
                        MERGE (curr)-[:NEXT]->(next)
                    """, curr_id=chunk_node_id, next_id=next_node_id)
                    
        # 3. Create document relationships
        print("Creating document relationships...")
        for _, row in df_rel.iterrows():
            source = str(row['doc_id'])
            target = str(row['other_doc_id'])
            rel_type = str(row['relationship_type']).upper().replace(" ", "_") # e.g. CAN_CU
            
            query = f"""
                MATCH (s:Document {{id: $source}})
                MATCH (t:Document {{id: $target}})
                MERGE (s)-[:{rel_type}]->(t)
            """
            session.run(query, source=source, target=target)
            
        # Verify stats
        print("Verifying statistics...")
        doc_count = session.run("MATCH (d:Document) RETURN count(d) as count").single()['count']
        doc_rel_count = session.run("MATCH (d1:Document)-[r]->(d2:Document) RETURN count(r) as count").single()['count']
        chunk_count = session.run("MATCH (c:Chunk) RETURN count(c) as count").single()['count']
        
        print(f"Number of Document nodes: {doc_count}")
        print(f"Number of Document-to-Document relationships: {doc_rel_count}")
        print(f"Number of Chunk nodes: {chunk_count}")

    driver.close()
    print("Done!")

if __name__ == "__main__":
    load_data()
