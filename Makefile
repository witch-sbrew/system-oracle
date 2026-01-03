# --- Configuration ---
BINARY = agent
CXX = /opt/anaconda3/envs/sysoracle/bin/clang++
CXXFLAGS = -std=c++20 -isysroot $(shell xcrun --show-sdk-path)
LIBS = -lcurl -lproc
PYTHON = python3
AGENT_SRC = collector/main.cpp       # Pointing to the new folder
SERVER_DIR = backend          			 # Pointing to the new folder

# --- Build Targets ---

all: build

# Compiles the C++ Agent
build:
	@echo "🛠️  Compiling C++ Collector..."
	$(CXX) $(CXXFLAGS) main.cpp -o $(BINARY) $(LIBS)
	@echo "✅ Build Complete: ./$(BINARY)"

# Starts the FastAPI Backend
server:
	@echo "🚀 Starting FastAPI Ground Station..."
	cd $(SERVER_DIR) && uvicorn main:app --reload --port 8000

# # Runs the Agent (useful for testing)
# run-agent: build
# 	@echo "📡 Running Collector..."
# 	./$(BINARY)

# # Setup the environment (run this once)
# setup:
# 	@echo "📦 Setting up environment..."
# 	conda env create -f environment.yml
# 	pip install -r requirements.txt

# Clean up binaries
clean:
	rm -f $(BINARY)
	@echo "🧹 Cleaned up project files."

.PHONY: all build server run-agent setup clean