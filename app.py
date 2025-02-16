import streamlit as st
import anthropic
import base64
import os
import re
import pandas as pd
import plotly.express as px

class MultiBankStatementChatbot:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.statements = {}
        self.currency_symbol = None

    def load_pdfs(self, uploaded_files):
        """Load PDFs and automatically generate summary"""
        try:
            new_files = False
            for file in uploaded_files:
                if file.name not in self.statements:
                    try:
                        pdf_data = base64.b64encode(file.getvalue()).decode('utf-8')
                        self.statements[file.name] = pdf_data
                        st.success(f"Loaded: {file.name}")
                        new_files = True
                    except Exception as e:
                        st.error(f"Error loading {file.name}: {str(e)}")
            
            if new_files:
                st.info(f"Successfully loaded {len(self.statements)} bank statements")
                return self.get_all_statements_summary()
            return None, None, None
        except Exception as e:
            st.error(f"Error in load_pdfs: {str(e)}")
            return None, None, None

    def parse_amount(self, amount_str):
        """Extract numerical value from amount string"""
        try:
            if isinstance(amount_str, str):
                # Remove currency symbols and spaces
                cleaned = re.sub(r'[£$€\s]', '', amount_str)
                # Find number pattern
                amount = re.findall(r'[-]?[\d,]+\.?\d*', cleaned)
                if amount:
                    return float(amount[0].replace(',', ''))
            return 0.0
        except Exception as e:
            st.error(f"Error parsing amount '{amount_str}': {str(e)}")
            return 0.0

    def extract_categories(self, text, section_marker):
        """Extract categories and amounts from text"""
        try:
            categories = {}
            if section_marker in text:
                section = text.split(section_marker)[1].split('\n\n')[0]
                for line in section.split('\n'):
                    if ':' in line and any(symbol in line for symbol in ['$', '€', '£']):
                        category, amount = line.split(':', 1)
                        category = category.strip('- ').strip()
                        amount = self.parse_amount(amount)
                        if category and amount:
                            categories[category] = amount
            return categories
        except Exception as e:
            st.error(f"Error extracting categories: {str(e)}")
            return {}

    def get_all_statements_summary(self):
        """Get summary of all statements with visualization data"""
        try:
            combined_prompt = """
            Analyze this bank statement and provide a summary of all transactions.
            Use the exact currency symbol found in the statement (€ for Euro, $ for Dollar, £ for Pound).
            Group them by category (like Groceries, Utilities, Entertainment, Income, etc.).
            Never have 2 groups of the same label, sum up the amount instead.
            Include the statement period/date if visible in the statement.
            
            Format the response EXACTLY as:
            STATEMENT PERIOD: [Month Year]
            
            DEBITS BY CATEGORY:
            - Category1: [Currency Symbol]1234.56
            - Category2: [Currency Symbol]789.01
            
            CREDITS BY CATEGORY:
            - Category1: [Currency Symbol]1234.56
            - Category2: [Currency Symbol]789.01
            
            TOTAL SUMMARY:
            Total Debits: [Currency Symbol]amount
            Total Credits: [Currency Symbol]amount
            Net Change: [Currency Symbol]amount

            Add a brief analysis of spending patterns and any notable observations.

            Note : Be careful, if the documents that are provided are not bank statements, just say that they are not bank statements.
            So please upload the proper file.
            """
            
            all_summaries = []
            all_debits = {}
            all_credits = {}
            
            for filename, pdf_data in self.statements.items():
                with st.spinner(f"Analyzing statement: {filename}"):
                    response = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1024,
                        messages=[{
                            "role": "user",
                            "content": [{
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": combined_prompt
                            }]
                        }]
                    )
                    
                    if not response or not response.content:
                        continue
                        
                    result_text = response.content[0].text
                    all_summaries.append(f"\n=== {filename} ===\n{result_text}")
                    
                    debit_categories = self.extract_categories(result_text, "DEBITS BY CATEGORY:")
                    credit_categories = self.extract_categories(result_text, "CREDITS BY CATEGORY:")
                    
                    for category, amount in debit_categories.items():
                        all_debits[category] = all_debits.get(category, 0) + amount
                    for category, amount in credit_categories.items():
                        all_credits[category] = all_credits.get(category, 0) + amount
            
            if not all_debits and not all_credits:
                st.warning("No categories could be extracted from the statements.")
                return "\n\n".join(all_summaries), pd.DataFrame(), pd.DataFrame()
            
            debit_df = pd.DataFrame(list(all_debits.items()), columns=['Category', 'Amount'])
            credit_df = pd.DataFrame(list(all_credits.items()), columns=['Category', 'Amount'])
            
            if not debit_df.empty:
                debit_df = debit_df.sort_values('Amount', ascending=True)
            if not credit_df.empty:
                credit_df = credit_df.sort_values('Amount', ascending=True)
            
            return "\n\n".join(all_summaries), debit_df, credit_df
        except Exception as e:
            st.error(f"Error in get_all_statements_summary: {str(e)}")
            return "", pd.DataFrame(), pd.DataFrame()

    def ask_question(self, question):
        """Ask questions about all statements"""
        try:
            context = f"""
            You are a helpful financial advisor analyzing {len(self.statements)} bank statements.
            Provide insights across all statements, including trends and patterns over time.
            Be concise but informative. Note any concerning patterns or provide suggestions.
            Use the appropriate currency symbols and round to 2 decimal places when showing amounts.

            Don't answer anything that is out of the context of financial advising.

            Previous conversation context helps you maintain continuity in the discussion.
            """
            
            documents = []
            for filename, pdf_data in self.statements.items():
                documents.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                })
            
            # Add conversation history to context
            if 'messages' in st.session_state:
                history = "\n".join([f"Human: {q}\nAssistant: {a}" for q, a in st.session_state.messages])
                context += f"\n\nPrevious conversation:\n{history}"
            
            documents.append({
                "type": "text",
                "text": f"{context}\n\nQuestion: {question}"
            })
            
            with st.spinner("Analyzing your question..."):
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": documents
                    }]
                )
                return response.content[0].text
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")
            return "I encountered an error processing your question. Please try again."

def main():
    st.set_page_config(
        page_title="FinanceGPT",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state for messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Sidebar Configuration
    with st.sidebar:
        st.title("💰 FinanceGPT")
        st.subheader("Configuration")
        
        # API Key input in sidebar
        api_key = st.text_input(
            "Enter your Anthropic API Key:",
            type="password",
            help="Enter your API key to start analyzing statements"
        )
        
        # File upload in sidebar
        if api_key:
            st.subheader("Upload Statements")
            uploaded_files = st.file_uploader(
                "Upload Bank Statements (PDF)",
                type=['pdf'],
                accept_multiple_files=True,
                help="Drag and drop your PDF bank statements here"
            )

    # Main content area
    if api_key:
        # Initialize chatbot
        if 'chatbot' not in st.session_state or st.session_state.get('api_key') != api_key:
            st.session_state.chatbot = MultiBankStatementChatbot(api_key)
            st.session_state.api_key = api_key
        
        if uploaded_files:
            try:
                # Process new files
                if 'processed_files' not in st.session_state:
                    st.session_state.processed_files = set()
                
                new_files = False
                for file in uploaded_files:
                    if file.name not in st.session_state.processed_files:
                        new_files = True
                        st.session_state.processed_files.add(file.name)
                
                # Only analyze if there are new files
                if new_files or 'summary' not in st.session_state:
                    summary, debit_df, credit_df = st.session_state.chatbot.load_pdfs(uploaded_files)
                    if summary:
                        st.session_state.summary = summary
                        st.session_state.debit_df = debit_df
                        st.session_state.credit_df = credit_df
                
                # Display visualizations
                if hasattr(st.session_state, 'debit_df') and not st.session_state.debit_df.empty:
                    st.subheader("Transaction Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_debit = px.bar(
                            st.session_state.debit_df,
                            x='Amount',
                            y='Category',
                            orientation='h',
                            title='Debits by Category',
                            color='Amount',
                            color_continuous_scale='Reds'
                        )
                        fig_debit.update_layout(height=400)
                        st.plotly_chart(fig_debit, use_container_width=True)
                    
                    with col2:
                        if hasattr(st.session_state, 'credit_df') and not st.session_state.credit_df.empty:
                            fig_credit = px.bar(
                                st.session_state.credit_df,
                                x='Amount',
                                y='Category',
                                orientation='h',
                                title='Credits by Category',
                                color='Amount',
                                color_continuous_scale='Greens'
                            )
                            fig_credit.update_layout(height=400)
                            st.plotly_chart(fig_credit, use_container_width=True)
                
                # Summary section
                if hasattr(st.session_state, 'summary'):
                    with st.expander("📊 Detailed Summary", expanded=True):
                        st.write(st.session_state.summary)
                
                # Chat interface
                st.subheader("💬 Chat with FinanceGPT")

                # Display chat history
                for message in st.session_state.messages:
                    with st.chat_message(message[0]):
                        st.write(message[1])

                # Chat input using st.chat_input
                if prompt := st.chat_input("Ask about your statement..."):
                    # Display user message
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    # Get and display assistant response
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing..."):
                            try:
                                answer = st.session_state.chatbot.ask_question(prompt)
                                st.write(answer)
                                # Add to message history
                                st.session_state.messages.append(("user", prompt))
                                st.session_state.messages.append(("assistant", answer))
                            except Exception as e:
                                st.error(f"Error getting response: {str(e)}")

                # Example questions (keep in sidebar)
                with st.sidebar:
                    st.subheader("Example Questions")
                    st.markdown("""
                    - How have my expenses changed over time?
                    - Compare my grocery spending across months
                    - Show my income trends
                    - What are my largest recurring expenses?
                    - Any unusual patterns in my spending?
                    """)
                    
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
        else:
            st.info("Please upload your bank statements to begin analysis")
    else:
        st.info("Please enter your API key in the sidebar to get started")

if __name__ == "__main__":
    main()