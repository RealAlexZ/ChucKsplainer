import os 
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from anthropic import Anthropic
from html_templates import css, bot_template, user_template
from agents import ProgrammerAgent, TestDesignerAgent, TestExecutorAgent
import time

def process_files():
    texts = []
    metadatas = []

    # Process code files (.ck files)
    code_snippets = Path('docs/code_snippets/').rglob('*.ck')
    for file in code_snippets:
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
            texts.append(text)
            metadatas.append({'source': 'code', 'file': str(file)})

    # Process documentation files (.html files)
    html_files = Path('docs/html_files/').rglob('*.html')
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            # Extract text from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n')
            texts.append(text)
            metadatas.append({'source': 'documentation', 'file': str(file)})

    return texts, metadatas

def get_text_chunks(texts, metadatas):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    chunks = []
    chunk_metadatas = []

    for text, metadata in zip(texts, metadatas):
        splits = text_splitter.split_text(text)
        chunks.extend(splits)
        chunk_metadatas.extend([metadata] * len(splits))

    return chunks, chunk_metadatas

def create_and_save_vectorstore(text_chunks, metadatas):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(
        texts=text_chunks,
        embedding=embeddings,
        metadatas=metadatas
    )
    vectorstore.save_local("faiss_index")
    return vectorstore

def load_vectorstore():
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    return vectorstore

def get_agents():
    client = Anthropic()
    programmer = ProgrammerAgent(client)
    test_designer = TestDesignerAgent(client)
    test_executor = TestExecutorAgent()
    return programmer, test_designer, test_executor

def handle_code_generation(question, retrieved_chunks):
    # Get the agents
    programmer, test_designer, test_executor = get_agents()
    
    # Create a task description that includes the retrieved context
    task_description = f"""
    Task: {question}
    
    Available Context and Documentation:
    {retrieved_chunks}
    """
    
    # Generate initial code
    code = programmer.generate_code(task_description)
    
    # Generate test cases
    test_cases = test_designer.generate_test_cases(task_description)
    
    # Execute and test the code
    feedback = test_executor.execute_code_with_tests(code, test_cases)
    
    # If there are errors, try to refine the code
    max_attempts = 3
    attempt = 1
    
    while "error" in feedback.lower() and attempt < max_attempts:
        # Update task description with error feedback
        task_description = f"""
        Task: {question}
        
        Previous Code:
        {code}
        
        Error Feedback:
        {feedback}
        
        Available Context and Documentation:
        {retrieved_chunks}
        
        Please fix the code based on the error feedback.
        """
        
        # Generate refined code
        code = programmer.generate_code(task_description)
        feedback = test_executor.execute_code_with_tests(code, test_cases)
        attempt += 1
    
    # Prepare the response
    response = f"""
    Generated ChucK Code:
    ```chuck
    {code}
    ```
    
    Test Cases:
    ```chuck
    {test_cases}
    ```
    
    Execution Result:
    {feedback}
    """
    
    return response

def handle_userinput(user_question):
    # Retrieve relevant chunks
    docs = st.session_state.vectorstore.similarity_search(
        query=user_question, k=5)
    retrieved_chunks = "\n\n".join([doc.page_content for doc in docs])

    # Display user message immediately
    st.write(user_template.replace(
        "{{MSG}}", user_question), unsafe_allow_html=True)

    # Create placeholder for AI response
    response_placeholder = st.empty()
    
    # Generate response using the multi-agent system
    response = handle_code_generation(user_question, retrieved_chunks)

    # Display AI response with typing effect
    for i in range(len(response) + 1):
        response_placeholder.write(bot_template.replace(
            "{{MSG}}", response[:i] + "▌"
        ), unsafe_allow_html=True)
        time.sleep(0.01)  # Adjust speed as needed
    
    # Final message without cursor
    response_placeholder.write(bot_template.replace(
        "{{MSG}}", response
    ), unsafe_allow_html=True)

    # Update chat history
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

def main():
    load_dotenv()
    st.set_page_config(page_title="ChucKsplainer",
                       page_icon="assets/favicon.ico")
    st.write(css, unsafe_allow_html=True)

    st.header("ChucKsplainer")
    
    # Add welcome message with typing animation
    welcome_placeholder = st.empty()
    welcome_message = "Hi! I am ChucKsplainer, your personal ChucK tutor. I can explain code examples, help you understand ChucK concepts, and even generate and test code for you. Let's chat and ChucK!"
    
    # Simulate typing effect
    for i in range(len(welcome_message) + 1):
        welcome_placeholder.write(bot_template.replace(
            "{{MSG}}", welcome_message[:i] + "▌"
        ), unsafe_allow_html=True)
        time.sleep(0.01)  # Adjust speed as needed
    
    # Final message without cursor
    welcome_placeholder.write(bot_template.replace(
        "{{MSG}}", welcome_message
    ), unsafe_allow_html=True)

    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Initialize vectorstore
    if st.session_state.vectorstore is None:
        with st.spinner("Loading vectorstore..."):
            # Check if vectorstore exists
            if Path("faiss_index").exists():
                # Load the vectorstore from disk
                st.session_state.vectorstore = load_vectorstore()
            else:
                # Get text and metadata from code snippets and documentation
                texts, metadatas = process_files()

                # Get the text chunks and their corresponding metadata
                text_chunks, chunk_metadatas = get_text_chunks(texts, metadatas)

                # Create vector store and save it to disk
                st.session_state.vectorstore = create_and_save_vectorstore(
                    text_chunks, chunk_metadatas)

    user_question = st.chat_input("Message ChucKsplainer")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()
