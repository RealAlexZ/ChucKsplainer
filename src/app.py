import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from html_templates import css, bot_template, user_template

def process_chuck_files():
    texts = []
    metadatas = []

    # Process code files (.ck files)
    chuck_files = Path('docs/chuck_scripts/').rglob('*.ck')
    for file in chuck_files:
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
            texts.append(text)
            metadatas.append({'source': 'code', 'file': str(file)})

    # Process documentation files (.html files)
    # html_files = Path('docs/html_files/').rglob('*.html')
    # for file in html_files:
    #     with open(file, 'r', encoding='utf-8') as f:
    #         html_content = f.read()
    #         # Extract text from HTML
    #         soup = BeautifulSoup(html_content, 'html.parser')
    #         text = soup.get_text(separator='\n')
    #         texts.append(text)
    #         metadatas.append({'source': 'documentation', 'file': str(file)})

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

def get_vectorstore(text_chunks, metadatas):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(
        texts=text_chunks,
        embedding=embeddings,
        metadatas=metadatas
    )
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatOpenAI(model_name="gpt-4o")
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    retriever = vectorstore.as_retriever(search_kwargs={'k': 5})
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

def main():
    load_dotenv()
    st.set_page_config(page_title="ChucKsplainer",
                       page_icon="assets/favicon.ico")
    st.write(css, unsafe_allow_html=True)

    st.header("ChucKsplainer")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    # Check if the conversation chain is initialized
    if st.session_state.conversation is None:
        with st.spinner("Loading..."):
            # Get text and metadata from ChucK files and documentation
            texts, metadatas = process_chuck_files()

            # Get the text chunks and their corresponding metadata
            text_chunks, chunk_metadatas = get_text_chunks(texts, metadatas)

            # Create vector store
            vectorstore = get_vectorstore(text_chunks, chunk_metadatas)

            # Create conversation chain
            st.session_state.conversation = get_conversation_chain(vectorstore)

    user_question = st.chat_input("Message ChucKsplainer")
    if user_question:
        handle_userinput(user_question)

if __name__ == '__main__':
    main()
