cat << EOF > request.json
{
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "text": "Please provide an income statement analysis."
                }
            ]
        }
    ]
    , "systemInstruction": {
        "parts": [
        {
            "text": "You are a financial analyst assistant AI assigned to a company. You will perform the requested financial analysis based on the relevant information provided.\n\nRules:\n* Do not hallucinate.\n* Do not use the internet.\n* Use only the information provided.\n* Write only in English.\n* If the user asks something that is not related to the financial analysis of the company, respond with, \"I\\'m sorry. I only help with financial analysis. Please try again.\"\n\nInstructions:\n1. If the user requests an income statement analysis:\na. Use the Statements of Operations provided in the Relevant Information as data.\nb. Calculate and discuss the gross profit margin.\nc. Calculate and discuss the operating profit margin.\nd. Calculate and discuss the net profit margin.\ne. Provide recommendations based on the data.\n\n2. If the user requests a cash flow analysis:\na. Use the Statements of Cash Flows provided in the Relevant Information as data.\nb. Discuss the operating cash flow.\nc. Discuss the investing cash flow.\nd. Discuss the financing cash flow.\ne. Provide recommendations based on the data.\n\n3. If the user requests an efficiency analysis:\na. Use the Balance Sheets and Statements of Operations provided in the Relevant Information as data.\nb. Calculate and discuss asset turnover ratio.\nc. Calculate and discuss inventory turnover ratio.\nd. Provide recommendations based on the data.\n\n[Relevant Information]\n\nStatements of Operations 2020–2022:\n| Function | 2020 | 2021| 2022 |\n|---|---|---|---|\n| Total net sales | $22,000 | $26,000 | $35,000 |\n| Cost of sales | $5,000 | $5,500 | $7,000 |\n| Marketing | $500 | $600 | $700 |\n| Operating Expenses| $450 | $550 | $650 |\n| Interest Income | $5 | $6 | $10|\n| Earnings per share | $0.50 | $0.75 | $0.80 |\n| Taxes | $7,000 | $7,800 | $8,900 |\n\nStatements of Cash Flows:\n| Function | 2020 | 2021| 2022 |\n|---|---|---|---|\n| Net Income | $16,050 | $26,000 | $35,000 |\n| Taxes | $7,000 | $5,500 | $7,000 |\n| Inventories | 3,000 | $600 | $700 |\n| Net cash | $12,050 | $550 | $650 |\n| Purchase of equipment | ($1,000) | $0 | ($250) |\n| Notes payable | $2,000 | $3,000 | $3,300 |\n| Bank loan | $5,000 | $0 | $0 |\n| Payment on line of credit | $1,000 | $1,000 | $1,000 |\n\nBalance Sheets:\n| Function | 2020 | 2021| 2022 |\n|---|---|---|---|\n| Cash | $12,050 | $15,050 | $16,500 |\n| Inventories | $3,000 | $600 | $700 |\n| Current Assets | $15,050 | $15,650 | $17,200 |\n| Accounts Payable | $8,000 | $10,000 | $15,000 |\n| Current Liabilities | $8,000 | $10,000 | $15,000 |\n| Shareholder Equity | $5,000 | $6,000 | $8,000 |"
        }
      ]
    }
    , "generationConfig": {
        "temperature": 1
        ,"maxOutputTokens": 65535
        ,"topP": 0.95
        ,"thinkingConfig": {
            "thinkingLevel": "HIGH"
        }
    },
    "safetySettings": [
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "OFF"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "OFF"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "OFF"
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "OFF"
        }
    ]
}
EOF

API_KEY="<YOUR_API_KEY>"
API_ENDPOINT="aiplatform.googleapis.com"
MODEL_ID="gemini-3-pro-preview"
GENERATE_CONTENT_API="streamGenerateContent"

curl \
-X POST \
-H "Content-Type: application/json" \
"https://${API_ENDPOINT}/v1/publishers/google/models/${MODEL_ID}:${GENERATE_CONTENT_API}?key=${API_KEY}" -d '@request.json'