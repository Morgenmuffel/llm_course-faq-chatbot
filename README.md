# llm_course-faq-chatbot
# ===================================
# FILE: README.md
# ===================================
# 🤖 Course FAQ Chatbot

A beautiful, local RAG-powered chatbot that answers questions about course materials using Elasticsearch and OpenAI.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd course-faq-chatbot
```

### 2. Configure Environment
```bash
# Edit .env and add your OpenAI API key
nano .env

pyenv install 3.11.13
pyenv virtualenv 3.11.13 llm-course
pyenv activate llm-course
pyenv versions

pip install -r requirements.txt

```

### 3. Run the Application
```bash
# Start all services

docker-compose up

# Or run in background
docker-compose up -d
```

### 4. Access the Chatbot
- Open your browser to http://localhost:8501
- Wait for data to load (first run takes ~30 seconds)
- Start chatting!

## 🛠️ Development

### Running Individual Services
```bash
# Start only Elasticsearch
docker-compose up elasticsearch

# Start the app for development (with hot reload)
docker-compose up streamlit-app
```

### Viewing Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs elasticsearch
docker-compose logs streamlit-app
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

## 📊 Features

- ✅ Real-time search across course materials
- ✅ Beautiful dark mode interface
- ✅ Course filtering
- ✅ Chat history
- ✅ Health monitoring
- ✅ Automatic data loading

## 🔧 Architecture

- **Elasticsearch**: Document storage and search
- **Streamlit**: Web interface
- **OpenAI GPT-4**: Response generation
- **Docker Compose**: Service orchestration

## 📝 Troubleshooting

### Elasticsearch won't start
```bash
# Check available memory
docker-compose logs elasticsearch

# Reduce memory if needed (edit docker-compose.yml)
ES_JAVA_OPTS: "-Xms512m -Xmx512m"
```

### Data not loading
```bash
# Check if Elasticsearch is healthy
curl http://localhost:9200

# Manually trigger data loading
docker-compose exec streamlit-app python load_data.py
```

### OpenAI errors
- Check your API key in `.env`
- Verify you have credits in your OpenAI account

## 🎯 Usage Examples

### Sample Questions to Try:
- "How do I run Kafka?"
- "What is Docker Compose?"
- "How to set up the environment?"
- "Explain machine learning workflow"

### Course Filtering:
- Select "All Courses" for broad search
- Choose specific course for targeted results

## 🔄 Updates and Maintenance

### Updating Course Data
The app automatically loads fresh data from the course repository on startup. To manually refresh:

```bash
docker-compose exec streamlit-app python load_data.py
```

### Backing Up Data
```bash
# Elasticsearch data is stored in a Docker volume
docker volume ls | grep elasticsearch

# To backup (optional)
docker run --rm -v course-faq-chatbot_elasticsearch_data:/data -v $(pwd):/backup alpine tar czf /backup/elasticsearch-backup.tar.gz /data
```

---

## 🎉 You're All Set!

Your local Course FAQ Chatbot is ready to go. The system will:

1. **Auto-start Elasticsearch** with proper memory settings
2. **Load course data** automatically on first run
3. **Provide a beautiful interface** with dark mode
4. **Handle course filtering** dynamically
5. **Maintain chat history** during your session

**Next Steps:**
- Try asking questions about different courses
- Experiment with the course filter
- Check out the system status in the sidebar
