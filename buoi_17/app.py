import streamlit as st
import os
import sys
import json
from neo4j import GraphDatabase

# Thêm đường dẫn để import được script internal_lookup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
try:
    from scripts.internal_lookup import InternalLookupAI
except ImportError:
    pass

st.set_page_config(page_title="SECURE RAG & COMPLIANCE — BUỔI 17", layout="wide")

# Banner cảnh báo
st.markdown("""
<div style="background-color: #ffcccc; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
    <strong>Demo đào tạo — kết quả AI cần kiểm toán viên xác minh.</strong>
</div>
""", unsafe_allow_html=True)

st.title("SECURE RAG & COMPLIANCE — BUỔI 17")

# Sidebar
st.sidebar.header("User Context")
user_id = st.sidebar.text_input("User ID demo", value="demo01")
roles = ['Admin', 'Risk_Manager', 'Staff', 'HR', 'Guest', 'Unauthorized_User']
user_role = st.sidebar.selectbox("User Role", roles)

# Neo4j status
neo4j_status = "Unknown"
try:
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "abcd1234")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    driver.verify_connectivity()
    neo4j_status = "Connected"
    driver.close()
except Exception as e:
    neo4j_status = "Disconnected"

st.sidebar.text(f"Neo4j Status: {neo4j_status}")

tab1, tab2, tab3 = st.tabs(["TRA CỨU QUY ĐỊNH", "COMPLIANCE GAP CHECKER", "AUDIT"])

with tab1:
    st.subheader("Tra cứu quy định nội bộ (Use Case 1)")
    question = st.text_input("Question / Requirement")
    top_k = st.slider("Top-k", 1, 10, 3)
    
    if st.button("RUN SEARCH"):
        if question:
            with st.spinner("AI đang tìm kiếm & tổng hợp..."):
                try:
                    ai = InternalLookupAI()
                    result = ai.lookup(question, user_role, top_k)
                    
                    st.write("### Answer / Evidence")
                    st.write(result['answer'])
                    
                    if user_role == 'Unauthorized_User' or not result['citations']:
                        st.warning("Access Decision: DENIED hoặc không có dữ liệu để hiển thị")
                    else:
                        st.success("Access Decision: ALLOWED")
                        st.write(f"**Citations**: {', '.join(result['citations'])}")
                        st.write(f"**Document/Chunk**: {', '.join(str(c) for c in result['chunk_ids'])}")
                        
                    st.write(f"**Request ID**: {result['request_id']}")
                except Exception as e:
                    st.error(f"Lỗi khi chạy tra cứu: {e}")
        else:
            st.warning("Vui lòng nhập câu hỏi.")

with tab2:
    st.subheader("Compliance Gap Checker (Use Case 2)")
    st.error("DATA GAP: INTERNAL POLICY NOT FOUND.")
    st.write("Tính năng Gap Checker đã bị vô hiệu hoá do dữ liệu đầu vào không đủ (chỉ có External Requirement, không có Internal Policy) theo báo cáo từ Prompt 6 & 7.")
    st.write("---")
    st.write("**NHNN | INTERNAL | STATUS**")
    st.write("N/A  | N/A        | CHENH_LECH")
    st.warning("NEEDS_HUMAN_REVIEW")

with tab3:
    st.subheader("Audit Trail")
    audit_file = os.path.join(os.path.dirname(__file__), "outputs", "audit_log.jsonl")
    if os.path.exists(audit_file):
        logs = []
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    # Lược bỏ các trường nhạy cảm nếu có (Dù jsonl ở đây đã sạch)
                    log_entry = json.loads(line)
                    logs.append(log_entry)
        
        # Chỉ hiển thị log của chính user đó, trừ phi là Admin (cho phép xem toàn bộ để demo)
        filtered_logs = [log for log in logs if user_role in log.get('user_role', []) or user_role == 'Admin']
        
        if filtered_logs:
            st.dataframe(filtered_logs)
        else:
            st.write("Không có dữ liệu log cho Role này (bạn không có quyền truy cập log của người khác).")
    else:
        st.write("Chưa có file audit log.")
