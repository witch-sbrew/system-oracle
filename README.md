# System Oracle: The Developer's "Black Box" Recorder
### 📖 Overview

**System Oracle** is a distributed observability tool designed to act as a "Black Box Flight Recorder" for developers. It bridges the gap between low-level system telemetry and high-level reasoning by combining a high-performance **C++ System Agent** with an **LLM-powered Diagnostic Engine**. By capturing real-time system vitals, terminal history, and ambient audio "thought logs," it builds a semantic timeline of your development session that can be queried in natural language.

### ✨ Key Features

- **Zero-Latency Telemetry (C++)**: A background producer that monitors process life cycles, CPU spikes, and terminal exit codes with minimal overhead.
- **Ambient "Thought" Ingestion**: Integrated audio capture that uses OpenAI Whisper to transcribe verbal reasoning during debugging sessions.
- **Semantic Root-Cause Analysis**: Uses an LLM (GPT-4o/Llama 3) to correlate terminal errors with system state and voice notes to explain bugs.
- **Time-Travel Querying**: A fullstack dashboard that allows you to search your history (e.g., "What was I saying when the build failed at 3 PM?").

### 🛠️ The Tech Stack

- **Systems Layer**: C++20 (System APIs, Socket Programming)
- **Backend Layer**: Python, FastAPI, _Redis (Task Queueing)_
- **AI Layer**: Ollama, _Whisper (STT)?_, _ChromaDB (Vector Search)?_
- **Frontend Layer**: _React.js/Next.js?_, _Tailwind CSS?_

### 🚀 System Architecture (Producer/Consumer)

The project utilizes a Distributed Producer-Consumer pattern for system stability:
1. **The Producer (C++ Agent)**: Efficiently gathers telemetry and pushes it to a local socket.
2. **The Broker (Redis/FastAPI)**: Buffers incoming data to prevent system lag.
3. **The Consumer (Python Worker)**: Processes heavy tasks like transcription, LLM analysis, and database indexing.
