# Agentic Customer Support System

An intelligent customer support system that uses AI agents to provide context-aware, empathetic responses to customer inquiries. Built with Python,Pydantic-AI, Streamlit, and GPT-4.

## 🌟 Features

- **Smart Context Handling**: Maintains customer history and preferences
- **Tier-Based Service**: Different service levels for different customer tiers
- **Order Tracking**: Real-time order status and tracking information
- **Sentiment Analysis**: Analyzes customer sentiment for better responses
- **Knowledge Base Integration**: Quick access to shipping, return, and warranty policies
- **Error Handling**: Graceful degradation when services are unavailable

## 🛠️ Tech Stack

- Python 3.8+
- Streamlit
- Pydantic
- Pydanic-AI
- OpenAI GPT-4

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/Croups/agentic-customer-support-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## 💻 Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Use the interface to:
   - View customer information
   - Check order status
   - Access shipping information
   - View return policies
   - Get warranty information

## 📁 Project Structure

```
├── app.py                 # Streamlit interface
├── support_system.py      # Core agent system
├── requirements.txt       # Project dependencies
├── .env                  # Environment variables
└── README.md             # Project documentation
```

## 🤖 Agent Capabilities

- Order status lookup
- Shipping information retrieval
- Policy information access
- Customer history analysis
- Sentiment-aware responses
- Automated escalation

## ⚠️ Known Limitations

- Real-time shipping status updates may be limited in UI
- Some agent tools require additional configuration
- Response times may vary based on API load


Feel free to reach me out on linkedin : www.linkedin.com/in/enes-koşar



