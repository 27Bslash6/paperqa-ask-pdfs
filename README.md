# A Knowledgable System

This is a lightweight CLI wrapper around [paper-qa](https://github.com/whitead/paper-qa) for answering questions of your local documents directory.

## Quickstart

1. **Installation**: Clone the repository and navigate to the project directory.
2. **Environment Setup**: Create and activate a virtual environment (recommended) using your preferred method.
3. **Dependencies**: Install the required dependencies by running `pip install -r requirements.txt`.
4. **Indexing Documents**: Prepare the documents you want to index in a directory. Supported file types include `.md`, `.txt`, `.pdf`, `.doc`, and `.docx`.
5. **Run the Application**: Execute `python aks.py` with the relevant command-line options.

## Features

### Indexing Documents
The application allows you to index a directory containing documents. During the indexing process, the application generates hashes for the files to detect changes and updates in the documents. The indexed documents are stored for faster retrieval and processing.

The application expects a `docs` directory to exist if not using the `-d` flag. The `docs` directory is ignored by git.  You can add subdirectories freely under this folder and query them individually using the `-d` flag, or query the entire directory without the flag. The application will recursively search the directory for supported file types.

### Answering Questions
Using the indexed documents, you can ask questions and receive answers based on the provided context. The application prompts you to enter the context and question, and it leverages the GPT-3.5-turbo model to generate answers. The answer is displayed in Markdown formatting for easy readability.

### Interactive Mode
The application includes an interactive mode, which allows you to ask multiple questions in succession without restarting the application. Once a question is answered, you can enter another question without providing the context again.

### Caching
To optimize performance, the application employs caching. It stores the indexed documents and their corresponding hashes to quickly determine if any changes have occurred. This helps reduce processing time by avoiding unnecessary reindexing.

### Cleaning the Cache
If required, the cache can be cleaned by supplying the --clean-cache flag when executing the application. This removes the saved hashes and the indexed document files to initiate a fresh indexing process.

Note: It's important to be cautious when using the --clean-cache option, as it erases previously indexed documents and may result in longer processing times for subsequent runs.

## Example Usage:

```bash
python ask.py --dir /path/to/documents --context "Introduction to Python. Answer using Markdown" --question "What is a Python decorator?"
```

This command recurses any the documents located under the specified directory (/path/to/documents), sets the provided context (Introduction to Python), and asks the provided question (What is a Python decorator?). The application generates the answer using the indexed documents and displays it in Markdown format.

Feel free to explore additional options and functionalities of the application, including the interactive mode and customization options such as the choice of model to use.

```bash
# Halp
python ask.py -h
```
