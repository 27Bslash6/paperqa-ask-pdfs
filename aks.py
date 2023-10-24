import click
import hashlib
import joblib
import sys

from config import settings
from cache import cache
from tqdm import tqdm
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from concurrent.futures import ThreadPoolExecutor, as_completed

from paperqa import Docs, PromptCollection
from langchain.globals import set_llm_cache
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate


class Aks:
    def __init__(self, context, question, docs_dir, model, clean):
        self.context = context
        self.question = question
        self.docs_dir = settings.DOCS_BASE_PATH / docs_dir
        self.data_file = self.docs_dir / settings.DATA_FILE_NAME
        self.hashes_file = self.docs_dir / settings.HASHES_FILE_NAME

        if not self.docs_dir.exists():
            click.echo(f"Directory '{docs_dir}' does not exist.")
            sys.exit(1)  # or however you want to handle this error

        if not self.data_file.exists() or not self.hashes_file.exists():
            clean = True  # force cleaning if the data or hash file does not exist

        if clean:
            # If 'clean' is True, always remove and regenerate the data and hashes files
            for file in [self.hashes_file, self.data_file]:
                if file.exists():
                    file.unlink()

        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""Answer the question '{question}' with the following context: {context}.
            If no references to the indexed materials can be found, do not answer the question.
            """,
        )

        set_llm_cache(cache)

        my_llm = ChatOpenAI(model=model)

        self.docs = Docs(
            prompts=PromptCollection(qa=self.prompt_template), llm=my_llm, memory=True
        )

        if self.hashes_match():
            self.load_docs()
        else:
            self.process_docs()

    def answer(self):
        answer = self.docs.query(
            self.context + "\n\n" + self.question,
            length_prompt="up to 200 words",
            max_sources=settings.MAX_SOURCES,
        )

        if answer.formatted_answer:
            click.echo(answer.formatted_answer)
        else:
            click.echo("No answer found")

    def hashes_match(self):
        if not self.hashes_file.exists():
            return False

        saved_hashes = self.load_saved_hashes()
        current_hashes = self.calculate_hashes(self.get_filepaths())

        return saved_hashes == current_hashes

    def load_saved_hashes(self):
        with self.hashes_file.open("r") as file:
            return file.read().splitlines()

    def calculate_hashes(self, files):
        with ThreadPoolExecutor() as executor:
            return list(executor.map(self.calculate_file_hash, files))

    def calculate_file_hash(self, file):
        hash_md5 = hashlib.md5(usedforsecurity=False)
        with file.open("rb") as f:
            hash_md5.update(f.read())
        return hash_md5.hexdigest()

    def process_docs(self):
        print("Indexing documents in directory ", self.docs_dir, "...")
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
        with ThreadPoolExecutor(max_workers=settings.MAX_INDEXER_THREADS) as executor:
            futures = [executor.submit(self.docs.add, str(file)) for file in files]

            with tqdm(total=len(files), desc="Processing files") as pbar:
                for _ in as_completed(futures):
                    pbar.update(1)

    def load_docs(self):
        self.docs = joblib.load(self.data_file)

    def save_docs(self):
        joblib.dump(self.docs, self.data_file)

    def get_filepaths(self, allowed_file_types=settings.ALLOWED_FILE_TYPES):
        try:
            files = [
                path
                for i in allowed_file_types
                for path in self.docs_dir.rglob(f"*.{i}")
            ]
            if not files:
                print(f"No files found in directory: {self.docs_dir}")

            return files
        except PermissionError:
            print(f"Permission denied for directory: {self.docs_dir}")
        except Exception as e:
            print(f"Unexpected error: {e}")


@click.command()
@click.option(
    "--dir",
    "-d",
    "docs_dir",
    default="",
    help="Directory containing documents to index",
)
@click.option(
    "--context", "-c", default=settings.DEFAULT_CONTEXT, help="Context to use"
)
@click.option("--question", "-q", default=None, help="Question to answer")
@click.option(
    "--interactive", "-i", default=False, is_flag=True, help="Interactive mode"
)
@click.option("--model", "-m", default="gpt-3.5-turbo", help="Model to use")
@click.option(
    "--clean-cache", "clean", default=False, is_flag=True, help="Clean the cache"
)
def aks_me(context, question, docs_dir, interactive, model, clean):
    history = FileHistory(settings.PROMPT_HISTORY_FILE)
    session = PromptSession(history=history)

    if question is not None:
        history.append_string(question)

    try:
        while True:
            # Check if both context and question are None
            if context is None:
                context = session.prompt("Context   : ")

            if question is None:
                # Prompt for context and question
                question = session.prompt("Question : ")

            answer_question = Aks(context, question, docs_dir, model, clean)
            answer_question.answer()

            # Reset question, but keep the context for next question
            question = None

            # Don't reset the cache *every* question!
            clean = False

            if not interactive:
                break
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    aks_me()
