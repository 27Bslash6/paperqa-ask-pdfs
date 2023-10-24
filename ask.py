import click
from pathlib import Path
import hashlib
import joblib
import sys

from paperqa import Docs, PromptCollection
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import PromptTemplate

DOCS_BASE_PATH = Path(__file__).parent / "docs"
HASHES_FILE_NAME = ".data.hashes"
DATA_FILE_NAME = ".data.joblib"
ALLOWED_FILE_TYPES = [".md", ".txt", ".pdf", ".doc", ".docx"]

class AnswerQuestion:
    def __init__(self, context, question, docs_dir):
        self.context = context
        self.question = question
        self.docs_dir = DOCS_BASE_PATH / docs_dir
        self.data_file = self.docs_dir / DATA_FILE_NAME
        self.hashes_file = self.docs_dir / HASHES_FILE_NAME

        self.my_qaprompt = PromptTemplate(
            input_variables=["context", "question"],
            template="Answer the question '{question}' with the following context:\nContext: {context}.\nIf no references to the indexed materials can be found, do not answer the question.  Format",
        )

        set_llm_cache(SQLiteCache())

        my_llm = ChatOpenAI(model="gpt4")
        self.docs = Docs(prompts=PromptCollection(qa=self.my_qaprompt), llm=my_llm)

    def answer(self):
        if self.hashes_file.exists() and self.hashes_match():
            self.load_docs()
        else:
            self.process_docs()

        answer = self.docs.query(self.context + "\n\n" + self.question, length_prompt="up to 200 words")
        
        click.echo(answer.formatted_answer)  # Print with Markdown formatting


    def hashes_match(self):
        saved_hashes = self.load_saved_hashes()
        current_hashes = self.calculate_hashes(self.get_filepaths())

        return saved_hashes == current_hashes

    def load_saved_hashes(self):
        with self.hashes_file.open("r") as file:
            return file.read().splitlines()

    def calculate_hashes(self, files):
        return [self.calculate_file_hash(file) for file in files]

    def calculate_file_hash(self, file):
        hash_md5 = hashlib.md5(usedforsecurity=False)
        with file.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def process_docs(self):
        file_hashes = self.calculate_hashes(self.get_filepaths())
        self.save_hashes(file_hashes)
        self.add_docs_and_save()

    def save_hashes(self, hashes):
        with self.hashes_file.open("w") as file:
            file.write("\n".join(hashes))

    def add_docs_and_save(self):
        self.add_docs(self.get_filepaths())
        self.save_docs()

    def add_docs(self, files):
        for file in files:
            print(file)
            self.docs.add(str(file))

    def load_docs(self):
        self.docs = joblib.load(self.data_file)

    def save_docs(self):
        joblib.dump(self.docs, self.data_file)

    def get_filepaths(self, allowed_file_types=ALLOWED_FILE_TYPES):
        return [file for file in self.docs_dir.glob("**/*") if file.suffix in allowed_file_types]


@click.command()
@click.option('--dir', '-d', "docs_dir", default="_default", help='Documents directory')
@click.option('--context', '-c', prompt='Enter the context')
@click.option('--question', '-q',  prompt='Enter the question')
def run_answer_question(context, question, docs_dir):
    if context and question:
        answer_question = AnswerQuestion(context, question, docs_dir)
        answer_question.answer()
        return

    try:
        while True:
            answer_question = AnswerQuestion(context, question, docs_dir)
            answer_question.answer()
    except KeyboardInterrupt:
        sys.exit(0)  # Graceful exit on Ctrl+C.

if __name__ == '__main__':
    run_answer_question()
if __name__ == '__main__':
    run_answer_question()

