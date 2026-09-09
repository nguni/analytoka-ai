# 📊 Analytoka AI

> **An Intelligent AI Data Analyst Agent for conversational data exploration, cleaning, analysis, and visualization.**

**Analytoka AI** is an AI-powered Data Analyst Agent developed by **John Muthoka**. It allows users to upload CSV or Excel datasets and interact with their data using natural language.

Instead of requiring users to write SQL queries, Python scripts, or complex spreadsheet formulas, Analytoka AI combines **LLM reasoning with deterministic Python analytical tools** to explore datasets, calculate metrics, identify patterns, clean data, detect anomalies, and generate visualizations.

---

## 👋 Meet Analytoka AI

**Hey there, I'm Analytoka AI. 👋**

Upload your Excel or CSV dataset and ask me questions about your data.

I can help you:

- 🔎 Explore and understand your dataset
- 🧹 Identify and clean data-quality issues
- 📊 Analyze business metrics
- 📈 Generate visualizations
- 🧠 Discover trends, correlations, and outliers
- 💬 Ask questions using natural language

You don't need to write SQL or Python — just ask questions about your data.

---

## ✨ Key Features

### 🔎 Dataset Exploration

Analytoka AI can inspect unfamiliar datasets before performing analysis.

It can:

- Inspect dataset dimensions
- Identify available columns
- Detect data types
- Preview sample records
- Count missing values
- Detect duplicate records
- Calculate unique values
- Generate descriptive statistics

This allows the agent to understand a dataset dynamically instead of relying on a predefined schema.

---

### 🧹 Data Cleaning

Analytoka AI includes a deterministic data-cleaning workspace.

Users can:

- Remove duplicate rows
- Trim leading and trailing whitespace
- Remove completely empty columns
- Fill missing text values
- Fill missing numeric values using column medians
- Drop rows with remaining missing values
- Review cleaning actions
- Reset to the original dataset
- Download cleaned data

The original uploaded dataset is not modified directly. Cleaning operations are performed on a working copy.

Cleaned datasets can be downloaded as:

- CSV
- Excel

---

### 📊 Data Analysis

Analytoka AI can perform analytical operations such as:

- Column-level statistics
- Grouped aggregations
- Ranking
- Exploratory Data Analysis
- Distribution analysis
- Correlation analysis
- Outlier detection
- Time-series analysis
- Business metric comparisons

Example:

```text
Which region generated the highest revenue?
```

The agent can determine the appropriate columns, calculate revenue by region using Python, rank the results, and explain the findings.

---

### 📈 AI-Generated Visualizations

Analytoka AI can decide when a visualization would help answer a user's question.

Currently supported visualizations include:

- 📊 Bar charts
- 📈 Line charts
- 🔵 Scatter plots
- 📉 Histograms
- 📦 Box plots
- 🥧 Pie charts
- 🔗 Correlation heatmaps

Example:

```text
Show revenue by region as a bar chart.
```

Or:

```text
Plot the monthly revenue trend.
```

The agent selects the appropriate visualization and generates it using Python.

---

### 🧠 Exploratory Data Analysis

Users can request a broad analysis without specifying individual calculations.

For example:

```text
Perform a full exploratory analysis of this dataset.
```

Analytoka AI can inspect:

- Dataset size
- Column types
- Missing values
- Duplicate records
- Numeric distributions
- Categorical distributions
- Summary statistics
- Correlations
- Potential outliers
- Important patterns

The AI then explains the results in understandable business language.

---

### 💬 Natural Language Analytics

Analytoka AI provides a conversational interface for data analysis.

Instead of:

```sql
SELECT
    region,
    SUM(revenue)
FROM sales
GROUP BY region
ORDER BY SUM(revenue) DESC;
```

A user can simply ask:

```text
Which region generated the highest revenue?
```

The agent determines which analytical operation is required and executes it using the available Python tools.

---

## 🧠 How Analytoka AI Works

Analytoka AI follows an **agentic tool-calling architecture**.

```text
                    ┌───────────────────────┐
                    │       USER            │
                    │  Natural Language     │
                    │      Question         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      STREAMLIT        │
                    │    User Interface     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      AI AGENT         │
                    │   LLM Reasoning       │
                    └───────────┬───────────┘
                                │
                         Selects Tool
                                │
                                ▼
                    ┌───────────────────────┐
                    │     TOOL ROUTER       │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Data Tools       Analysis Tools      Chart Tools
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    PYTHON / PANDAS    │
                    │ Actual Calculations   │
                    └───────────┬───────────┘
                                │
                           Tool Result
                                │
                                ▼
                    ┌───────────────────────┐
                    │      AI AGENT         │
                    │ Interpret Results     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    FINAL RESPONSE     │
                    │ Insights + Charts     │
                    └───────────────────────┘
```

The agent can execute multiple analytical steps before producing its final answer.

---

## 🎯 Core Design Principle

A major design principle behind Analytoka AI is:

> ### **LLM for reasoning and explanation. Python for calculations.**

The language model does not need to guess numerical results.

Instead:

1. The LLM understands the user's question.
2. The agent determines which analytical tool is required.
3. Python/Pandas performs the actual calculation.
4. The result is returned to the LLM.
5. The LLM interprets and explains the result.

This architecture helps reduce hallucination and improves analytical reliability.

---

## 🔄 Agent Loop

The application follows the general agent loop:

```text
DECIDE
   ↓
SELECT TOOL
   ↓
EXECUTE TOOL
   ↓
OBSERVE RESULT
   ↓
DECIDE AGAIN
   ↓
FINAL ANSWER
```

This means Analytoka AI can perform multiple operations before responding to the user.

For example:

```text
User:
"Which region has the highest revenue? Show me a chart."
```

The agent may:

```text
1. Inspect the dataset
        ↓
2. Identify region and revenue columns
        ↓
3. Group revenue by region
        ↓
4. Determine the highest-performing region
        ↓
5. Generate a bar chart
        ↓
6. Explain the result
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application and agent logic |
| **Streamlit** | Interactive web interface |
| **Groq API** | LLM inference and tool calling |
| **GPT-OSS** | Language model reasoning |
| **Pandas** | Data manipulation and analysis |
| **Matplotlib** | Data visualization |
| **OpenPyXL** | Excel file processing |
| **python-dotenv** | Local environment configuration |
| **Git** | Version control |
| **GitHub** | Source-code hosting |

---

## 🧰 Agent Tools

Analytoka AI currently exposes several deterministic tools to the AI agent.

### Data Tools

```text
inspect_dataset()
get_dataset_sample()
get_column_statistics()
group_and_aggregate()
sort_and_rank()
```

These tools allow the agent to understand unfamiliar datasets and perform common analytical calculations.

### Analysis Tools

```text
exploratory_analysis()
correlation_analysis()
detect_outliers()
analyze_distribution()
analyze_time_series()
```

These provide more advanced analytical capabilities.

### Visualization Tools

```text
create_chart()
```

The chart engine currently supports:

```text
bar
line
scatter
histogram
boxplot
pie
correlation_heatmap
```

### Cleaning Tools

The cleaning layer includes operations for:

```text
Duplicate removal
Missing-value handling
Whitespace trimming
Empty-column removal
Median imputation
CSV export
Excel export
```

---

## 📂 Project Structure

The current development repository contains the broader AI Agent learning environment, with Analytoka AI located under the projects directory.

```text
AI-Agent-Lab/
│
├── .gitignore
├── requirements.txt
│
├── lessons/
│
└── projects/
    │
    └── ai_data_analyst/
        │
        ├── app.py
        ├── agent.py
        ├── agent_groq.py
        ├── README.md
        │
        ├── tools/
        │   ├── __init__.py
        │   ├── data_tools.py
        │   ├── cleaning_tools.py
        │   ├── analysis_tools.py
        │   └── chart_tools.py
        │
        ├── data/
        │   └── sample_sales.csv
        │
        └── outputs/
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nguni/analytoka-ai.git
```

Navigate into the repository:

```bash
cd analytoka-ai
```

---

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Once activated, your terminal should look similar to:

```text
(.venv) PS C:\...\analytoka-ai>
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The main dependencies include:

```text
streamlit
pandas
openpyxl
matplotlib
groq
python-dotenv
```

---

### 4. Configure the Groq API Key

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
```

The `.env` file should remain private and must not be committed to GitHub.

Your `.gitignore` should include:

```gitignore
.env
.venv/
__pycache__/
*.pyc
outputs/*.png
```

---

### 5. Run Analytoka AI

From the repository root:

```bash
streamlit run projects/ai_data_analyst/app.py
```

Streamlit will start the application and provide a local address that can be opened in a browser.

---

## 📁 Supported Data Sources

Analytoka AI currently supports:

### CSV

```text
.csv
```

### Excel

```text
.xlsx
.xls
```

For Excel workbooks, users can select the worksheet they want Analytoka AI to analyze.

---

## 💡 Example Questions

After uploading a dataset, try asking:

### General Analysis

```text
Perform a full exploratory analysis of this dataset.
```

```text
Give me the most important insights from this data.
```

### Business Analysis

```text
Which region generated the highest revenue?
```

```text
Which products are performing best?
```

```text
Rank the regions from highest to lowest revenue.
```

### Time-Series Analysis

```text
Plot the monthly revenue trend.
```

```text
How has revenue changed over time?
```

### Data Quality

```text
Are there any missing values in this dataset?
```

```text
Are there duplicate records?
```

### Outlier Analysis

```text
Are there any unusual values or outliers?
```

### Correlation Analysis

```text
Analyze correlations between the numeric variables.
```

```text
Analyze correlations and show me a heatmap.
```

### Visualization

```text
Show revenue by region as a bar chart.
```

```text
Create a histogram of revenue.
```

```text
Show me a box plot of unit price.
```

---

## 🧹 Data Cleaning Workflow

Analytoka AI follows a safe cleaning approach:

```text
Original Dataset
       ↓
Data Quality Assessment
       ↓
User Selects Cleaning Actions
       ↓
Python Applies Cleaning
       ↓
Working Dataset Created
       ↓
Review Results
       ↓
Analyze Cleaned Dataset
       ↓
Download CSV / Excel
```

The original uploaded dataset remains unchanged.

This follows another important design principle:

> **AI can recommend or coordinate cleaning, but deterministic Python performs the actual data modification.**

---

## 🔐 Security & Data Privacy

API credentials are not stored directly in the source code.

For local development, credentials should be stored in:

```text
.env
```

The `.env` file is excluded from Git using `.gitignore`.

For cloud deployment, API credentials should be stored using the deployment platform's secrets-management functionality.

### Important

Users should avoid uploading:

- Passwords
- API keys
- Financial credentials
- Confidential company datasets
- Personally identifiable information
- Sensitive client information

to a publicly hosted demonstration environment.

---

## 🌐 Deployment

Analytoka AI is designed to be deployable as a Streamlit application.

The intended deployment architecture is:

```text
Developer
    ↓
Git
    ↓
GitHub
    ↓
Streamlit Community Cloud
    ↓
Public Analytoka AI Application
```

Application secrets such as:

```text
GROQ_API_KEY
```

should be configured securely on the deployment platform rather than committed to GitHub.

---

## ⚠️ Current Limitations

Analytoka AI is actively under development.

Current limitations include:

- Chat history is currently session-based
- Conversation context across complex follow-up questions is still being improved
- Cross-sheet analysis is limited
- Multi-dataset relationships are not yet supported
- Cleaning recommendations are currently primarily user-controlled
- Generated chart files use temporary/local storage
- Advanced BI calculations are still being expanded
- Persistent authentication and user accounts are not yet implemented

---

## 🗺️ Roadmap

Future development is planned across several areas.

### 💬 Conversational Intelligence

- Conversational memory
- Better follow-up question understanding
- Context-aware analysis
- Persistent chat history

### 📊 Advanced Analytics

- Group comparisons
- Percentage-change calculations
- Month-over-month analysis
- Year-over-year analysis
- Pivot analysis
- Target vs actual analysis
- Advanced KPI calculations
- Trend detection

### 🧹 Intelligent Data Cleaning

- AI-generated cleaning recommendations
- Column-specific cleaning strategies
- Data-type correction
- Category standardization
- Outlier treatment
- Before/after comparison
- Cleaning undo functionality

### 📈 Visualization

- Improved automatic chart selection
- Additional chart types
- Interactive charts
- Dashboard-style summaries

### 📁 Data Support

- Cross-sheet Excel analysis
- Multi-file analysis
- Larger dataset support
- Data dictionary support
- RAG-assisted metadata understanding

### 📄 Reporting

- Automated executive summaries
- Downloadable analytical reports
- PDF reports
- Analysis export

### 🤖 AI Architecture

- Additional LLM providers
- Improved tool routing
- More specialized analytical tools
- Improved agent orchestration
- More robust error recovery

---

## 🎯 Why I Built Analytoka AI

Traditional Business Intelligence and Data Analytics often require analysts to manually:

- Understand unfamiliar datasets
- Clean data
- Write queries
- Calculate metrics
- Create visualizations
- Interpret results
- Communicate insights

Generative AI creates an opportunity to make this workflow more conversational.

Analytoka AI explores how an AI agent can act as an intelligent interface between the user and traditional analytical tools while still relying on deterministic computation for numerical accuracy.

The project combines concepts from:

- Business Intelligence
- Data Analytics
- Data Science
- Generative AI
- AI Agents
- LLM Tool Calling
- Python Automation
- Data Visualization

---

## 🎓 Learning Objectives

This project was also developed as a hands-on exploration of how AI agents work from first principles.

Concepts implemented include:

```text
LLM API Integration
        ↓
Dynamic User Input
        ↓
Conversation State
        ↓
Python Tools
        ↓
Function Calling
        ↓
Tool Execution
        ↓
Tool Results
        ↓
Tool Registry / Router
        ↓
Agent Loop
        ↓
Dataset Inspection
        ↓
Data Analysis
        ↓
Data Cleaning
        ↓
Exploratory Analysis
        ↓
AI-Generated Visualizations
        ↓
Full AI Data Analyst Agent
```

Rather than relying immediately on an agent framework, the project implements the underlying agent mechanics directly to demonstrate how tool-calling AI systems operate.

---

## 🤝 Contributing

Analytoka AI is currently a personal portfolio and learning project.

Suggestions, feedback, and ideas for improving the project are welcome through GitHub issues.

---

## 👨‍💻 Author

### John Muthoka

**Business Intelligence & Data Professional**

Analytoka AI was designed and developed as a portfolio project exploring the intersection of:

**Data Analytics × Business Intelligence × Generative AI × AI Agents**

---

## 📄 Copyright

**© 2026 John Muthoka. All rights reserved.**

**Analytoka AI — Intelligent Data Analyst Agent**

Designed & Developed by **John Muthoka**.

---

<p align="center">
  <strong>📊 Analytoka AI</strong><br>
  Ask your data. Understand your business.
</p>
