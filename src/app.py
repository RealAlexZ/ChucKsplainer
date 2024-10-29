import os 
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from html_templates import css, bot_template, user_template

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
    vectorstore = FAISS.load_local("faiss_index", embeddings)
    return vectorstore

def get_llm_chain():
    llm = ChatOpenAI(model_name="gpt-4")
    prompt_template = """
        You are an AI assistant that provides code snippets and explanations based on the user's question.
        Use the following retrieved content (code snippets and documentation) to help answer the question.
        If you provide any code, make sure it is properly formatted.

        Question: {question}

        Retrieved Content:
        {retrieved_chunks}

        Answer:
    """
    prompt = PromptTemplate(
        input_variables=["question", "retrieved_chunks"],
        template=prompt_template
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    return llm_chain

def handle_userinput(user_question):
    # Retrieve relevant chunks
    docs = st.session_state.vectorstore.similarity_search(
        query=user_question, k=5)
    retrieved_chunks = "\n\n".join([doc.page_content for doc in docs])

    # Generate response using the retrieved chunks
    llm_chain = get_llm_chain()
    response = llm_chain.run(question=user_question, retrieved_chunks=retrieved_chunks)

    # Update chat history
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.write(user_template.replace(
                "{{MSG}}", message["content"]), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message["content"]), unsafe_allow_html=True)

def main():
    load_dotenv()
    st.set_page_config(page_title="ChucKsplainer",
                       page_icon="assets/favicon.ico")
    st.write(css, unsafe_allow_html=True)

    st.header("ChucKsplainer")

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

    user_question = st.chat_input("Message AI")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()
