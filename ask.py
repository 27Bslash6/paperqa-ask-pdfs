from pathlib import Path
import click
import os
import joblib

from paperqa import Docs, PromptCollection
import langchain
from langchain.cache import InMemoryCache
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import PromptTemplate

DATA_FILE = "obj.joblib"

DOCS_DIR = "docs"
DATA_DIR = "data"


def get_prompts():
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="Answer the question '{question}' "
        "with the following context:\n"
        "Context: {context}"
    )
    return PromptCollection(qa=prompt_template)

def get_llm():
    return ChatOpenAI(callbacks=[StreamingStdOutCallbackHandler()], streaming=True)

def get_docs(dir):    
    docs_dir = Path(DOCS_DIR) / dir

    data_file = docs_dir / "db.joblib"

    docs = Docs(prompts=get_prompts(), llm=get_llm())
    for f in os.listdir(DOCS_DIR):
        filename = os.path.join(DOCS_DIR, f)
        docs.append(filename)

    # Load saved docs if pickle exists
    if not Path(DATA_FILE).exists():
        docs_dir = "docs"
        for f in os.listdir(docs_dir):
            filename = os.path.join(docs_dir, f)
            docs.add(filename)
        # Save the docs
        joblib.dump(docs, DATA_FILE)
    else:
        # Load the docs
        docs = joblib.load(DATA_FILE)


@click.command()
@click.option('--dir', '-d', default="_default", help='Documents directory')
@click.option('--context', prompt='Enter the context')
@click.option('--question', prompt='Enter the question')
def answer_question(dir, context, question):
    langchain.llm_cache = InMemoryCache()

    docs = get_docs(dir)

    answer = docs.query(context + "\n\n" + question)
    
    # click.echo(answer.formatted_answer)
    print(answer.formatted_answer)

if __name__ == '__main__':
    answer_question()
