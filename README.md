# FinanceGPT

An AI-powered bank statement analyzer that helps individuals and professionals understand their financial transactions better using Claude AI.

## Overview

FinanceGPT is a Streamlit-based web application that allows users to:
- Upload bank statements in PDF format
- Get automated analysis of transactions
- Chat with an AI assistant about their financial data
- Detect potential fraudulent activities
- Receive personalized financial insights

## Features

- PDF to Image Conversion: Processes bank statements from PDF format
- OCR Integration: Extracts text from statement images
- Claude AI Analysis: Provides detailed transaction analysis
- Interactive Chat: Ask questions about your financial data
- Fraud Detection: Identifies unusual transaction patterns
- Financial Insights: Offers spending optimization suggestions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FinanceGPT.git
cd FinanceGPT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
export ANTHROPIC_API_KEY='your_claude_api_key'
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your bank statement PDF

4. View the automated analysis and ask questions about your finances

## Security Note

This application processes sensitive financial information. We recommend:
- Running the application locally
- Not storing bank statements
- Using secure API key management
- Reviewing the Claude API documentation for security best practices

## Claude API Integration

This project uses the Claude API for natural language processing. For more information about Claude and API usage, visit:
- [Claude Documentation](https://docs.anthropic.com/claude/docs)
- [API Reference](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Anthropic for the Claude AI API
- Streamlit for the web framework
- The open-source community for various tools and libraries used in this project