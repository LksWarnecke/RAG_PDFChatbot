import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub

# extract text from all pdfs and at text to "text" variable
def get_pdf_text(pdf_docs):
    text = ""
    # creating pdf object for each pdf and looping over every page of each pdf to extract + add extracted text
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

#split text string into chunks
def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000, #character size of each chunk
        chunk_overlap=200, #if chunk ends e.g. in middle of sentence this overlap gives it a bit of puffer
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

#put chunks into embedding and save in vecstorstore
def get_vectorstore(text_chunks):
    #huggingface embeddings
    #embeddings = HuggingFaceHub(
    #    repo_id="sentence-transformers/all-MiniLM-L6-v2",  # Fast & free online embedding model
    #    task="feature-extraction"
    #)

    embeddings = OpenAIEmbeddings()
    
    vectorstore= FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# store conversation chain
def get_conversation_chain(vectorstore):
    #huggingface llm
    #llm = HuggingFaceHub(
    #    repo_id="mistralai/Mistral-7B-Instruct",
    #    model_kwargs={"temperature": 0.5, "max_length": 512}
    #)
    
    llm = ChatOpenAI()
    
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs!", page_icon=":books:")
    
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat w/ multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on Process", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get text chunks
                text_chunks = get_text_chunks(raw_text)

                # create vectore store w/ embeddings
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain - session_state -> makes var constant (cant be reinitialized) & makes it available outside of the with scope
                st.session_state.conversation = get_conversation_chain(vectorstore)

if __name__ == '__main__':
    main()