import os
import csv
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from huggingface_hub import login

# Load environment variables
load_dotenv()
login(os.getenv("HUGGINGFACEHUB_API_TOKEN"))
groq_api_key = os.getenv("GROQ_API_KEY")

PDF_PATH = "EnvPolicy.pdf"
VECTORSTORE_DIR = "faiss_index"


# STEP 1: Extract PDF Text
def get_pdf_text(pdf_path):
    text = ""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

# STEP 2: Split Text into Chunks
def get_text_chunks(raw_text):
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return splitter.split_text(raw_text)

# STEP 3: Create or Load Vectorstore
def get_vectorstore(chunks, embeddings):
    vectorstore = FAISS.from_texts(chunks, embeddings)
    vectorstore.save_local(VECTORSTORE_DIR)
    return vectorstore

# Load vectorstore (or create it if missing)
def load_or_build_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    if os.path.exists(VECTORSTORE_DIR):
        return FAISS.load_local(VECTORSTORE_DIR, embeddings,allow_dangerous_deserialization=True)
    else:
        raw_text = get_pdf_text(PDF_PATH)
        chunks = get_text_chunks(raw_text)
        return get_vectorstore(chunks, embeddings)

# STEP 4: Conversation Chain Setup
def get_conversation_chain(vectorstore):
    llm = ChatGroq(
        model_name="llama3-8b-8192",
        temperature=0.5,
        request_timeout=30,
        api_key=groq_api_key
    )
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(llm=llm, retriever=vectorstore.as_retriever(), memory=memory)

# Setup on import
vectorstore = load_or_build_vectorstore()
conversation = get_conversation_chain(vectorstore)

# STEP 5: Query Function
def query_policy(question):
    response = conversation({"question": question})
    return response['answer']
    