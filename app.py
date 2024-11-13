from openai import OpenAI
import streamlit as st
import tabula
import pandas as pd
import tempfile

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    uploaded_file = st.file_uploader("Upload Bank Statement PDF Files", type=['pdf'], accept_multiple_files=True)
    
st.title("💬 FinanceGPT")
st.caption("💰 A Chatbot for your bank statement")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with your personnal finance?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)



def extract_tables_from_pdfs(uploaded_files):
    """Extract all tables from multiple PDF files using tabula."""
    all_tables = []
    
    for uploaded_file in uploaded_files:
        try:
            # Create a temporary file for tabula to process
            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
                # Write the uploaded file data to the temporary file
                tmp_file.write(uploaded_file.getvalue())
                tmp_file.flush()  # Ensure all data is written
                
                # Read all tables from the PDF using the temporary file path
                tables = tabula.read_pdf(
                    tmp_file.name,  # Use the temporary file's path
                    pages='all',
                    multiple_tables=True,
                    guess=True,
                    lattice=True,
                    stream=True
                )
                
                # Store tables with metadata
                all_tables.append({
                    'filename': uploaded_file.name,
                    'tables': tables,
                    'num_tables': len(tables)
                })
                
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    return all_tables



