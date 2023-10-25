import logging
import click
from hashlib import md5
from joblib import dump, load
from sys import exit
from logger import logger
from logging import DEBUG, INFO

from config import settings
from cache import get_cache
from tqdm import tqdm
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from concurrent.futures import ThreadPoolExecutor, as_completed

from paperqa import Docs, PromptCollection
from langchain.globals import set_llm_cache
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from pathlib import Path


class Aks:
    def __init__(self, context: str, docs_dir: str, model: str, clean: bool):
        self.context: str = context
        self.docs_dir: Path = settings.DOCS_BASE_PATH / docs_dir
        self.data_file: Path = self.docs_dir / settings.DATA_FILE_NAME
        self.hashes_file: Path = self.docs_dir / settings.HASHES_FILE_NAME

        self.hash_dict = {}

        if not self.docs_dir.exists():
            click.echo(f"Directory '{docs_dir}' does not exist.")
            exit(1)  # or however you want to handle this error

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

        set_llm_cache(get_cache())

        my_llm = ChatOpenAI(model=model)

        self.docs = Docs(
            prompts=PromptCollection(qa=self.prompt_template), llm=my_llm, memory=True
        )

        if self.hashes_match():
            logger.debug("Hashes match.")
            self.load_docs()
        else:
            logger.debug("Hashes do not match.")
            self.process_docs()

    def answer(self, question: str):
        logger.debug("Asking the LLM ...")
        answer = self.docs.query(
            self.context + "\n\n" + question,
            length_prompt=settings.DEFAULT_LENGTH_PROMPT,
            max_sources=settings.MAX_SOURCES,
        )

        logger.debug("Answer received.")
        if answer.formatted_answer:
            click.echo(answer.formatted_answer)
        else:
            click.echo("No answer found")

    def hashes_match(self) -> bool:
        logger.debug("Matching document hashes.")
        if not self.hashes_file.exists():
            logger.debug("Hash file doesn't exist.")
            return False

        saved_hashes = self.load_saved_hashes()
        current_hashes = self.calculate_hashes(self.get_filepaths())

        return saved_hashes == current_hashes

    def load_saved_hashes(self):
        logger.debug("Loading saved hashes from %s", str(self.hashes_file))
        with self.hashes_file.open("r") as file:
            return file.read().splitlines()

    def calculate_hashes(self, files: list) -> list:
        logger.debug("Calculating hashes.")
        with ThreadPoolExecutor() as executor:
            return list(executor.map(self.calculate_file_hash, files))

    def calculate_file_hash(self, file: Path) -> str:
        logger.debug("Calculating file hash for %s", str(file))
        hash_md5 = md5(usedforsecurity=False)
        with file.open("rb") as f:
            hash_md5.update(f.read())
        self.hash_dict[file] = hash_md5.hexdigest()
        logger.debug("Hash for %s is %s", str(file), self.hash_dict[file])
        return self.hash_dict[file]

    def process_docs(self):
        logger.info("Indexing documents in directory %s ...", self.docs_dir)
        file_hashes = self.calculate_hashes(self.get_filepaths())
        self.save_hashes(file_hashes)
        self.add_docs_and_save()

    def save_hashes(self, hashes: list):
        logger.debug("Saving hashes to %s ...", str(self.hashes_file))
        with self.hashes_file.open("w") as file:
            file.write("\n".join(hashes))

    def add_docs_and_save(self):
        self.add_docs(self.get_filepaths())
        self.save_docs()

    def add_docs(self, files: list):
        logger.debug("Adding documents.")
        with ThreadPoolExecutor(max_workers=settings.MAX_INDEXER_THREADS) as executor:
            futures = [
                executor.submit(self.docs.add, str(file), docname=self.hash_dict[file])
                for file in files
            ]

            with tqdm(total=len(files), desc="Processing files") as pbar:
                for _ in as_completed(futures):
                    pbar.update(1)

    def load_docs(self):
        self.docs = load(self.data_file)

    def save_docs(self):
        dump(self.docs, self.data_file)

    def get_filepaths(
        self, allowed_file_types: list = settings.ALLOWED_FILE_TYPES
    ) -> list:
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
@click.option(
    "--verbose", "verbose", default=False, is_flag=True, help="Verbose logging"
)
def main(
    context: str,
    question: str,
    docs_dir: str,
    interactive: bool,
    model: str,
    clean: bool,
    verbose: bool,
):
    if verbose:
        logger.setLevel(DEBUG)

    logger.debug("Loading history from %s.", settings.PROMPT_HISTORY_FILE)
    history = FileHistory(settings.PROMPT_HISTORY_FILE)

    logger.debug("Starting prompt session.")
    session = PromptSession(history=history)

    if question is not None:
        history.append_string(question)

    try:
        aks = Aks(context, docs_dir, model, clean)
        if context is None:
            context = session.prompt("Context   : ")

        while True:
            if question is None:
                # Prompt for context and question
                question = session.prompt("Question : ")

            logger.debug("Answering question: %s", question)
            aks.answer(question)

            # Reset question, but keep the context for next question
            question = None

            if not interactive:
                break
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    main()
