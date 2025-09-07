import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000" 

st.set_page_config(page_title="Legal Document Reviewer", layout="wide")

st.title("⚖️ Legal Document Reviewer & Analysis Platform")

# ------------------ FILE UPLOAD ------------------
st.header("📂 Upload Documents")
uploaded_files = st.file_uploader("Upload legal documents", type=["pdf", "docx", "txt"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
        if response.status_code == 200:
            st.success(f"✅ {file.name} uploaded successfully")
        else:
            st.error(f"❌ Failed to upload {file.name}")

st.divider()

# ------------------ CHAT SECTION ------------------
st.header("💬 Chat with your Legal Assistant")
user_input = st.text_input("Ask a question about the uploaded documents:")

if st.button("Ask"):
    if user_input:
        with st.spinner("Analyzing..."):
            response = requests.post(f"{BACKEND_URL}/ask", json={"question": user_input})
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    st.subheader("📌 Answer:")
                    st.write(data["answer"])
                else:
                    st.error("❌ Backend error: " + data.get("message", "Unknown issue"))

                if "sources" in data:
                    st.subheader("📎 Sources:")
                    for src in data["sources"]:
                        st.write(f"- {src}")
            else:
                st.error("❌ Error processing your request.")
    else:
        st.warning("Please enter a question first.")

