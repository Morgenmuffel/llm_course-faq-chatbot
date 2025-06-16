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
        <div class="sidebar-content">
            <h3>🔧 System Status</h3>
            <p><span class="status-indicator {'status-online' if is_healthy else 'status-offline'}"></span>System: {health_message}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("### 📚 Course Selection")
        st.markdown('</div>', unsafe_allow_html=True)

        courses = rag_system.get_courses() if is_healthy else []

        course_options = ["All Courses"] + courses
        selected_course = st.selectbox(
            "Choose a course:",
            course_options,
            index=0
        )

        course_filter = None if selected_course == "All Courses" else selected_course

        # Course info
        if courses:
            st.markdown(f"""
            <div class="sidebar-content">
                <strong>Available Courses:</strong> {len(courses)}
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View all courses"):
                for course in courses:
                    st.write(f"• {course}")

    # Main content - system is ready
    if not is_healthy:
        st.error("⚠️ System not ready. Please check the status in the sidebar.")
        return

    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

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

    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    col1, col2 = st.columns([4, 1])

    with col1:
        user_input = st.text_input(
            "Ask your question:",
            placeholder="e.g., How do I run Kafka?",
            key="user_input",
            label_visibility="collapsed"
        )

    with col2:
        send_button = st.button("Send 🚀", use_container_width=True)

    # Process input
    if send_button and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get bot response
        with st.spinner("🤔 Thinking..."):
            response = rag_system.ask(user_input, course_filter)
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        welcome_msg = "👋 Hello! I'm your course assistant. Ask me anything about the courses!"
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        st.rerun()

if __name__ == "__main__":
    main()
