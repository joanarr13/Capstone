import PyPDF2
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter

pdf_data = PdfReader("C:\\Users\\bruna\\Documents\\Bruna\\school\\IMS\\3ºano\\1ºsemestre\\CP_CapstoneProject\\meds.pdf")
pdf_text = ""

for i, page in enumerate(pdf_data.pages):
    text = page.extract_text()
    if text:
        pdf_text += text

text_splitter = CharacterTextSplitter(
    separator = "\n",
    chunk_size = 700,
    chunk_overlap = 100
)
meds_data = text_splitter.split_text(pdf_text)
