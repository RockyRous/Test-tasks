## Project Name

Prompt Engineer Test Project

## Description

This project is a demonstration of a Prompt Engineer utilizing OpenAI's GPT-3.5-turbo model to generate movie scripts based on user prompts.

## Project Structure

- **main.py:** Entry point for running the project.
- **app.py:** Contains the `PromptApp` class, a class for interacting with OpenAI's GPT-3.5-turbo model using prompts.



## App Module (`app.py`)

### `PromptApp` Class

A class for interacting with OpenAI's GPT-3.5-turbo model using prompts.

#### Methods

- `__init__(self, OPENAI_API_KEY):` Initializes the `PromptApp` instance with the provided OpenAI API key.
- `get_llm_response(self, message: list):` Compiles a request from data and outputs the content of the response.
- `valid_prompt_universe(user_prompt: str, universe: dict) -> tuple[str, dict, dict, dict]:` Checks the correctness of incoming parameters.
- `get_prompt_for_script_json(user_prompt: str, universe: dict) -> list:` Compiles a request from data and outputs the message.
- `generate_movie_script(self, prompt: str, universe: dict):` Generates a movie script based on the given prompt and universe parameters.



## Possible Improvements

1. **Optimizing Requests:**
   - Utilize methods for reducing request costs, such as compressing JSON to minimize the transmitted data volume.
   - Explore strategies to decrease the length of requests without losing meaning, e.g., optimizing the structure of messages.

2. **Integration with Telegram API:**
   - Consider integrating with the Telegram API to enhance user convenience for input and output. This could provide a more flexible and user-friendly interface.

3. **Fine-Tuning Bot Responses:**
   - Implement the ability to finely adjust parameters of bot responses, such as temperature of generation, dialogue length, and other settings. This allows users more flexible control over the style and nature of responses.

4. **Model Training with Paid Learning:**
   - Explore more efficient methods for model training, possibly using paid learning to fine-tune the model for specific queries and user preferences.

5. **Adoption of LangChain Library:**
   - Investigate the possibility of transitioning to work with the LangChain library for structuring various processes. This could simplify the management of different stages of data processing and interactions with the model.
