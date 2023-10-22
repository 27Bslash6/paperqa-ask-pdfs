# Ask your PDFS with Paper-QA

This script is designed to answer a user's question based on a given context. It utilizes the `paperqa` library, along with other dependencies, to generate an answer using a language model.

## Usage

1. Make sure you have the required dependencies installed by running `pip install -r requirements.txt`.
2. Run the script with the following command: `python answer_question.py --context "Enter the context" --question "Enter the question"`.
3. Provide the required input when prompted.
4. The script will generate an answer based on the provided context and question and display it.

## Dependencies

This script relies on the following dependencies:

- `click`: Used for command-line interface.
- `joblib`: Used for object serialization.
- `paperqa`: Dependency for handling document parsing and querying. See [paperqa](https://github.com/whitead/paper-qa#install)
- `langchain`: Language model library for generating answers.
- `langchain.cache`: In-memory cache for language model prompts.
- `langchain.chat_models`: Library for interacting with language models.
- `langchain.callbacks.streaming_stdout`: Callback handler for streaming output.
- `langchain.prompts`: Template for generating prompts.
- 

## Functionality

1. The script prompts the user to enter the context and the question.
2. It creates a prompt template based on the provided context and question.
3. It initializes a language model and sets up prompt handling and callbacks.
4. It checks for saved documents in a specified directory.
5. If no saved documents are found, it prompts the user to provide documents and saves them for future use.
6. If saved documents exist, it loads them.
7. The script queries the documents with the given context and question.
8. It generates an answer based on the query and displays it.

## Data Persistence

The script utilizes the `joblib` library to save and load the document object for future use. The saved document object is stored in the `obj.joblib` file.

Note: Make sure to have write permissions in the directory where the script is executed to store the document object.

## License

This script is licensed under the [MIT License](LICENSE).

Please check the individual licenses of the dependencies mentioned above before using this script in a commercial product.