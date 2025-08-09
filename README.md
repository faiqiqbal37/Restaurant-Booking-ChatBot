# 🍴 Restaurant Booking Agent - TheHungryUnicorn

A conversational AI agent that helps customers make and manage restaurant bookings through natural language interactions. Built with LangGraph, Ollama, and Streamlit for a seamless booking experience.

## 🎯 Overview

This project was developed as part of a technical assessment for Locai Labs, implementing a conversational AI agent for restaurant bookings at TheHungryUnicorn. The system handles natural language requests to book tables, check availability, and manage existing reservations through an intelligent conversation flow.

The agent maintains context across multiple conversation turns, so customers don't need to repeat information they've already provided. It integrates with a mock restaurant booking API and uses local AI processing with Ollama and Llama 3.2.

**Key capabilities:**
- 📅 Check table availability for specific dates and times
- 🍽️ Create new reservations with customer details
- 👀 Retrieve existing booking information
- ✏️ Modify reservation details (date, time, party size)
- ❌ Cancel bookings
- ❓ Answer general restaurant questions

## 🚀 Features

### Core Functionality
- **Natural Language Processing**: Understands booking requests in conversational language
- **Multi-turn Conversations**: Maintains context across multiple exchanges
- **Parameter Extraction**: Intelligently extracts dates, times, party sizes, and contact information
- **API Integration**: Connects to restaurant booking system with proper error handling
- **Dual Interface**: Both CLI and web-based interfaces available

### Technical Highlights
- **Agent Framework**: Built with LangGraph for robust conversation flow management
- **Local AI**: Uses Ollama with Llama 3.2 for privacy-focused AI processing
- **State Management**: Persistent booking context across conversation turns
- **Error Handling**: Graceful handling of API failures and invalid requests
- **Authentication**: Secure Bearer token authentication with booking API

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  LangGraph Agent │───▶│   Booking API   │
│  (CLI/Web UI)   │    │                  │    │   (Mock Server) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Ollama (Llama3) │
                       │  Local LLM       │
                       └──────────────────┘
```


## 🛠️ Technical Stack

- **Agent Framework**: LangGraph 0.0.60
- **LLM**: Ollama with Llama 3.2 (local inference)
- **Backend**: LangChain Community 0.2.1
- **Web Interface**: Streamlit 1.35.0
- **API Client**: Python Requests 2.32.3
- **Configuration**: python-dotenv 1.0.1

## 📋 Prerequisites

### System Requirements
- Python 3.8+ 
- [Ollama](https://ollama.ai/) installed and running
- Mock Restaurant Booking API Server (provided separately)

### Ollama Setup
1. Install Ollama from [https://ollama.ai/](https://ollama.ai/)
2. Pull the required model:
   ```bash
   ollama pull llama3.2
   ```
3. Verify Ollama is running:
   ```bash
   ollama list
   ```

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/faiqiqbal37/Restaurant-Booking-ChatBot
```

### 2. Install Dependencies in the Root Directory as well as the Server Directory
```bash
pip install -r requirements.txt
```


### 3. Start the Mock API Server
1. Follow the instructions at: [Restaurant-Booking-Mock-API-Server](https://github.com/AppellaAI/Restaurant-Booking-Mock-API-Server)
2. Start the server:
   ```bash
   python -m app
   ```
3. Verify the server is running at `http://localhost:8547`

### 4. Run the Application

#### CLI Interface (Terminal)
```bash
python main_cli.py
```

#### Web Interface (Streamlit)
```bash
streamlit run main_web.py
```

Then open your browser to `http://localhost:8501`

## 💻 Usage Examples

### Making a Booking
```
User: "I'd like to book a table for 4 people next Friday at 7:30pm"
Agent: "I'd be happy to help you book a table for 4 people next Friday at 7:30pm. 
        I'll need your name and phone number to complete the reservation."

User: "My name is John Smith and my phone is 555-123-4567"
Agent: "Perfect! I've successfully created your booking for 4 people on 
        December 15, 2024 at 7:30pm. Your booking reference is ABC123."
```

### Checking Availability
```
User: "What times are available this Saturday for 2 people?"
Agent: "Let me check availability for Saturday for 2 people...
        
        Available times:
        • 6:00 PM
        • 6:30 PM  
        • 8:00 PM
        • 8:30 PM
        
        Would you like to book any of these times?"
```

### Managing Existing Bookings
```
User: "What time is my reservation on Saturday?" 
Agent: "Let me look up your reservation... Your booking (Reference: ABC123) 
        is scheduled for Saturday, December 14, 2024 at 7:30pm for 4 people 
        under the name John Smith."
```

## 🏛️ Design Rationale

### Framework and Tool Choices

**Why LangGraph?**
I chose LangGraph for the conversation flow because it handles complex multi-step interactions well. The main advantage is how it manages state between conversation turns - users don't have to repeat information they've already provided. It also makes the code more organized by separating intent classification from API calls, which makes debugging easier when something goes wrong.

**Why Ollama with Llama 3.2?**
The main reason was cost - Ollama with Llama 3.2 is completely free to use, while OpenAI's GPT models charge per token. During development and testing, this saved significant costs since I was running hundreds of test conversations. The model runs locally, which also means faster response times since there's no network latency to external APIs.

**Dual Interface Approach**
I built both CLI and web interfaces because they serve different purposes. The CLI is perfect for quick testing during development, while the Streamlit web interface makes it easy to demo the system and feels more like a real product. Both use the same underlying agent logic, so I only had to write the core functionality once.

### Key Design Decisions and Trade-offs

**State Management**
I decided to keep conversation context in memory rather than using a database. This makes the system simpler to run and test, but means conversations don't persist if the application restarts. For a demo/assessment this seemed like a reasonable trade-off.

**Parameter Processing**
Instead of trying to extract everything at once, I built the system to ask for missing information step by step. This feels more natural in conversation but requires more complex state tracking. The trade-off is worth it for user experience.

**Error Handling**
I focused on graceful degradation - if the AI model fails to parse something, the system falls back to asking clarifying questions rather than crashing. This makes the system more robust but means some interactions take longer.

### Production Scaling Considerations

**Moving to Cloud APIs**
While I used local Llama 3.2 for development, in production we could switch to cloud-based APIs like OpenAI or Anthropic for better reliability and performance. This would require updating the LLM client but the rest of the architecture would remain the same.

**Database Integration**
The current in-memory state would need to be replaced with a proper database (PostgreSQL) for session persistence. We'd also need Redis for caching frequent queries like availability checks.

**Load Balancing**
Multiple agent instances could run behind a load balancer, with session stickiness to ensure users stay connected to the same instance during their conversation.

**API Rate Limiting**
Production would need rate limiting per user to prevent abuse, and connection pooling to handle multiple simultaneous bookings efficiently.

### Current Limitations

**Performance**
The current setup uses locally hosted Llama 3.2, which can be slower than cloud-based APIs. Response times may vary depending on your hardware specifications.

**Memory and Context**
Conversation history is limited to prevent token overflow, so very long conversations might lose early context. The system also doesn't remember users between sessions.

**Single Restaurant Support**
Everything is hardcoded for TheHungryUnicorn. Adding multi-restaurant support would require restructuring how restaurant data is handled.

**Basic Error Recovery**
If the booking API is down, the system can't do much except ask users to try again later. Better error recovery would include retry logic and alternative booking methods.

**Limited Natural Language Understanding**
The current prompt-based approach works well but sometimes misses nuanced requests. More advanced NLP could improve accuracy.

### Security Implementation Strategy

**API Security**
Currently using Bearer token authentication with the booking API. In production, this would need token rotation and more secure credential storage using services like AWS Secrets Manager.

**Input Validation**
All user inputs are processed through the AI model, but additional validation should be added to prevent injection attacks or malicious inputs.

**Data Protection**
Customer data (names, phone numbers) should be encrypted in transit and at rest. Currently this data only exists temporarily in memory.

**Audit Logging**
Production systems would need comprehensive logging of all booking operations for compliance and debugging purposes.

### Future Improvements

**Enhanced User Experience**
- Support for modifying multiple booking details in one request
- Better handling of ambiguous dates ("this Friday" when it's unclear which Friday)
- Integration with calendar applications

**Technical Enhancements**
- Async processing for better performance with multiple users
- Caching layer for availability data to reduce API calls
- Better conversation memory for returning customers
- Support for multiple languages

**Business Features**
- Integration with restaurant management systems
- Analytics dashboard for booking patterns
- Automated confirmation emails and SMS reminders

## 📁 Project Structure

```
restaurant-booking-agent/
├── agent/
│   ├── __init__.py
│   ├── graph.py          # LangGraph workflow definition
│   ├── nodes.py          # Agent node implementations
│   ├── prompts.py        # LLM prompts for different tasks
│   └── state.py          # Conversation state management
├── api/
│   ├── __init__.py
│   └── client.py         # Restaurant API client
├── server/               # Mock API server (included)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── __main__.py   # Server entry point
│   │   ├── main.py       # FastAPI application
│   │   ├── models.py     # Database models
│   │   ├── database.py   # Database configuration
│   │   ├── init_db.py    # Database initialization
│   │   └── routers/      # API route handlers
│   │       ├── availability.py
│   │       └── booking.py
│   └── requirements.txt  # Server dependencies
├── utils/
│   ├── __init__.py
│   └── parsers.py        # Date/time parsing utilities
├── debug/
│   └── test_intents.py   # Debugging utilities
├── .env                  # Environment variables
├── .gitignore
├── main_cli.py           # Terminal interface
├── main_web.py           # Streamlit web interface
├── requirements.txt      # Python dependencies
└── README.md
```

## 🧪 Debugging

### Debug Utilities
The project includes debugging tools in the `debug/` folder:

```bash
python debug/test_intents.py
```


## 🙏 Acknowledgments

- **Locai Labs** for providing the technical assessment opportunity
- **AppellaAI** for the mock API server at: https://github.com/AppellaAI/Restaurant-Booking-Mock-API-Server
- **LangChain Team** for the excellent LangGraph framework  
- **Ollama Team** for making local LLM inference accessible
- **Streamlit Team** for the intuitive web app framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the [original API Server Repository](https://github.com/AppellaAI/Restaurant-Booking-Mock-API-Server) for API-related issues
2. Review the debug utilities in `/debug/test_intents.py` for intent classification problems
3. Open an issue in this repository with detailed information about the problem

---

**Built as part of Locai Labs Technical Assessment**  
*Restaurant Booking Agent for TheHungryUnicorn*
