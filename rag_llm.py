import os
import requests
import time
import logging
import threading
from enum import Enum
from elasticsearch import Elasticsearch
from openai import OpenAI
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InitializationState(Enum):
    NOT_STARTED = "not_started"
    CONNECTING = "connecting"
    LOADING_DATA = "loading_data"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"

class RAGSystem:
    def __init__(self):
        self.es_client = None
        self.openai_client = None
        self.index_name = "course-questions"
        self.initialization_state = InitializationState.NOT_STARTED
        self.initialization_error = None
        self.initialization_progress = ""
        self.document_count = 0
        
        # Start initialization in background
        self._start_initialization()

    def _start_initialization(self):
        """Start the initialization process in a background thread"""
        if self.initialization_state == InitializationState.NOT_STARTED:
            self.initialization_state = InitializationState.CONNECTING
            initialization_thread = threading.Thread(target=self._initialize_async, daemon=True)
            initialization_thread.start()
            
    def _initialize_async(self):
        """Asynchronous initialization process"""
        try:
            logger.info("🚀 Starting RAG System initialization...")
            
            # Step 1: Initialize connections
            self.initialization_state = InitializationState.CONNECTING
            self.initialization_progress = "Connecting to services..."
            
            if not self._initialize_connections():
                self.initialization_state = InitializationState.FAILED
                self.initialization_error = "Failed to connect to required services"
                return
            
            # Step 2: Initialize data
            self.initialization_state = InitializationState.LOADING_DATA
            self.initialization_progress = "Loading course data..."
            
            if not self._initialize_data():
                self.initialization_state = InitializationState.FAILED
                self.initialization_error = "Failed to initialize course data"
                return
                
            # Success!
            self.initialization_state = InitializationState.READY
            self.initialization_progress = f"Ready with {self.document_count} documents"
            logger.info("✅ RAG System initialization completed!")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            self.initialization_state = InitializationState.FAILED
            self.initialization_error = str(e)

    def _initialize_connections(self):
        """Initialize Elasticsearch and OpenAI connections"""
        # Elasticsearch connection
        es_url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')

        # Wait for Elasticsearch to be ready
        logger.info("🔌 Connecting to Elasticsearch...")
        for attempt in range(30):
            try:
                self.es_client = Elasticsearch(es_url)
                if self.es_client.ping():
                    logger.info("✅ Connected to Elasticsearch")
                    break
            except Exception as e:
                if attempt < 29:  # Don't log on last attempt
                    logger.info(f"⏳ Waiting for Elasticsearch... (attempt {attempt + 1})")
                    time.sleep(2)

        if not self.es_client or not self.es_client.ping():
            logger.error("❌ Failed to connect to Elasticsearch")
            return False

        # OpenAI connection
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY not found")
            return False

        self.openai_client = OpenAI(api_key=api_key)
        logger.info("✅ Connected to OpenAI")
        return True

    def create_index(self):
        """Create the course-questions index"""
        if not self.es_client:
            logger.error("Elasticsearch client not available")
            return False

        index_settings = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "section": {"type": "text"},
                    "question": {"type": "text"},
                    "course": {"type": "keyword"}
                }
            }
        }

        try:
            if self.es_client.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} already exists")
                return True

            self.es_client.indices.create(index=self.index_name, body=index_settings)
            logger.info(f"Created index {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    def load_course_data(self):
        """Load course data from GitHub"""
        try:
            docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
            response = requests.get(docs_url)
            response.raise_for_status()

            documents_raw = response.json()

            documents = []
            for course in documents_raw:
                course_name = course['course']
                for doc in course['documents']:
                    doc['course'] = course_name
                    documents.append(doc)

            logger.info(f"Loaded {len(documents)} documents from {len(documents_raw)} courses")
            return documents

        except Exception as e:
            logger.error(f"Failed to load course data: {e}")
            return []

    def index_documents(self, documents: List[Dict]):
        """Index documents in Elasticsearch"""
        if not self.es_client:
            logger.error("Elasticsearch client not available")
            return False

        try:
            self.initialization_state = InitializationState.INDEXING
            self.initialization_progress = f"Indexing {len(documents)} documents..."
            
            for i, doc in enumerate(documents):
                self.es_client.index(index=self.index_name, id=i, document=doc)
                
                # Update progress periodically
                if i % 100 == 0:
                    self.initialization_progress = f"Indexed {i}/{len(documents)} documents..."

            # Refresh index to make documents searchable
            self.es_client.indices.refresh(index=self.index_name)
            self.document_count = len(documents)
            logger.info(f"Indexed {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return False

    def _initialize_data(self):
        """Initialize Elasticsearch with course data if needed"""
        if not self.es_client:
            logger.error("Elasticsearch client not available")
            return False

        try:
            # Check if data already exists
            if self.es_client.indices.exists(index=self.index_name):
                count = self.es_client.count(index=self.index_name)['count']
                if count > 0:
                    self.document_count = count
                    logger.info(f"Data already exists ({count} documents)")
                    return True
        except:
            # Index doesn't exist, need to create it
            pass

        logger.info("Initializing data...")

        # Create index
        if not self.create_index():
            return False

        # Load and index documents
        documents = self.load_course_data()
        if not documents:
            return False

        if not self.index_documents(documents):
            return False

        logger.info("✅ Data initialization completed")
        return True

    def search_documents(self, query: str, course: Optional[str] = None, size: int = 5) -> List[Dict]:
        """Search documents in Elasticsearch"""
        search_query = {
            "size": size,
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": query,
                            "fields": ["question^3", "text", "section"],
                            "type": "best_fields"
                        }
                    }
                }
            }
        }

        # Add course filter if specified
        if course:
            search_query["query"]["bool"]["filter"] = {
                "term": {"course": course}
            }

        try:
            if not self.es_client:
                return []
            response = self.es_client.search(index=self.index_name, body=search_query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_courses(self) -> List[str]:
        """Get list of all available courses"""
        try:
            if not self.es_client:
                return []
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "courses": {
                            "terms": {"field": "course", "size": 100}
                        }
                    }
                }
            )
            return [bucket['key'] for bucket in response['aggregations']['courses']['buckets']]
        except Exception as e:
            logger.error(f"Failed to get courses: {e}")
            return []

    def build_prompt(self, query: str, search_results: List[Dict]) -> str:
        """Build prompt for the LLM"""
        prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

        context = ""
        for doc in search_results:
            context += f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['text']}\n\n"

        return prompt_template.format(question=query, context=context).strip()

    def generate_answer(self, prompt: str) -> str:
        """Get response from OpenAI"""
        try:
            if not self.openai_client:
                return "OpenAI client not configured"
            response = self.openai_client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def ask(self, query: str, course: Optional[str] = None) -> str:
        """Main RAG pipeline: search + generate"""
        try:
            search_results = self.search_documents(query, course)

            if not search_results:
                return "I couldn't find any relevant information in the course materials."

            prompt = self.build_prompt(query, search_results)
            answer = self.generate_answer(prompt)
            return answer

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return f"Sorry, I encountered an error processing your question: {str(e)}"

    def health_check(self):
        """Check system health"""
        try:
            # Check initialization state
            if self.initialization_state == InitializationState.FAILED:
                error_msg = self.initialization_error or "Unknown initialization error"
                return False, f"Initialization failed: {error_msg}"
                
            if self.initialization_state != InitializationState.READY:
                return False, self.initialization_progress

            # Check Elasticsearch
            if not self.es_client or not self.es_client.ping():
                return False, "Elasticsearch not connected"

            # Check OpenAI
            if not self.openai_client:
                return False, "OpenAI not configured"

            # Check if index exists and has data
            if not self.es_client.indices.exists(index=self.index_name):
                return False, "Index not found"

            count = self.es_client.count(index=self.index_name)['count']
            if count == 0:
                return False, "No documents in index"

            return True, f"Healthy with {count} documents"

        except Exception as e:
            return False, f"Health check failed: {e}"
    
    def is_ready(self):
        """Check if the system is ready to handle requests"""
        return self.initialization_state == InitializationState.READY
    
    def get_initialization_status(self):
        """Get detailed initialization status"""
        return {
            "state": self.initialization_state.value,
            "progress": self.initialization_progress,
            "error": self.initialization_error,
            "document_count": self.document_count
        }
