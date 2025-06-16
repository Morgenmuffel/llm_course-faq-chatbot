import streamlit as st
import os
import time
from rag_llm import RAGSystem, InitializationState

# Page configuration
st.set_page_config(
    page_title="Courses FAQ Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS from external file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css('styles.css')

@st.cache_resource
def get_rag_system():
    """Initialize RAG system (cached so it only runs once)"""
    return RAGSystem()

def display_initialization_status(rag_system):
    """Display initialization status with proper UI feedback"""
    status = rag_system.get_initialization_status()
    state = status["state"]
    progress = status["progress"]
    error = status["error"]
    
    if state == InitializationState.READY.value:
        return True
    elif state == InitializationState.FAILED.value:
        st.error(f"❌ Initialization failed: {error}")
        if st.button("🔄 Retry Initialization"):
            # Clear cache and restart
            st.cache_resource.clear()
            st.rerun()
        return False
    else:
        # Show spinner with current progress
        with st.spinner(f"🚀 {progress}"):
            # Auto-refresh every 2 seconds while initializing
            time.sleep(2)
            st.rerun()
        return False

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🤖 Course FAQ Chatbot</h1>
        <p class="main-subtitle">Ask questions about zoomcamp courses</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize RAG system
    rag_system = get_rag_system()

    # Handle initialization status
    if not display_initialization_status(rag_system):
        return  # Exit early if not ready

    # System is ready - get health status for sidebar
    is_healthy, health_message = rag_system.health_check()

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        
            <h3>🔧 System Status</h3>
            <p><span class="status-indicator {'status-online' if is_healthy else 'status-offline'}"></span>System: {health_message}</p>

        """, unsafe_allow_html=True)

 
        st.markdown("### 📚 Course Selection")

        courses = rag_system.get_courses() if is_healthy else []

        course_options = ["All Courses"] + courses
        selected_course = st.selectbox(
            "Choose a course:",
            course_options,
            index=0
        )

        course_filter = None if selected_course == "All Courses" else selected_course

    # Main content - system is ready
    if not is_healthy:
        st.error("⚠️ System not ready. Please check the status in the sidebar.")
        return


    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = "👋 Hello! I'm your course assistant. Ask me anything about the courses!"
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">🧑‍💻 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

    # Initialize input counter for clearing
    if "input_counter" not in st.session_state:
        st.session_state.input_counter = 0

    # Chat input - sticky bottom (styling in styles.css)
    user_input = st.text_input(
        "Ask your question:",
        placeholder="Type your question and press Enter...",
        key=f"user_input_{st.session_state.input_counter}",
        label_visibility="collapsed"
    )

    # Process input on Enter
    if user_input and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get bot response
        with st.spinner("🤔 Thinking..."):
            response = rag_system.ask(user_input, course_filter)
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Clear the input field by incrementing counter (forces new widget)
        st.session_state.input_counter += 1
        st.rerun()

if __name__ == "__main__":
    main()
