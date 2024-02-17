from openai import OpenAI


class PromptApp:
    """ A class for interacting with OpenAI's GPT-3.5-turbo model using prompts. """
    def __init__(self, OPENAI_API_KEY):
        self.client_ai = OpenAI(
            api_key=OPENAI_API_KEY,
        )

    def get_llm_response(self, message: list):
        """ Compiling a request from data and outputting the “content” of the response """
        completion = self.client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message,
            temperature=0.8,
        )

        return completion.choices[0].message.content

    @staticmethod
    def valid_prompt_universe(user_prompt: str, universe: dict) -> tuple[str, dict, dict, dict]:
        """ Checking the correctness of incoming parameters """
        try:
            if not type(user_prompt) is str:
                raise Exception('Prompt must be a string')
            characters: dict = universe["characters"]
            locations: dict = universe["locations"]
            emotions: dict = universe["emotions"]

            return user_prompt, characters, locations, emotions

        except KeyError as key_error:
            print(f"KeyError: {key_error} is missing in the 'universe' dictionary.")
        except TypeError as type_error:
            print(f"TypeError: {type_error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        raise Exception('Input parameters error!')

    @staticmethod
    def get_prompt_for_script_json(user_prompt: str, universe: dict) -> list:
        """ Compiling a request from data and outputting the message """
        res = PromptApp.valid_prompt_universe(user_prompt, universe)
        user_prompt, characters, locations, emotions = res

        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates creative dialogues."
                                          "dialogue length=2+ and use all locations."},
            {"role": "user", "content": user_prompt},
            {"role": "assistant",
             "content": "Generate a dialogue between {characters[random]} in "
                        "{locations[random]} that is both substantive and engaging."},
            {"role": "user", "content": f"locations: {locations}"},
            {"role": "user", "content": f"characters: {characters}"},
            {"role": "user", "content": f"emotions: {emotions}"},
            {"role": "assistant",
             "content": "Generate a JSON response with the following structure: {\"scenes\": [{\"location\": "
                        "\"location.key\", \"characters\": [List of participating characters], \"dialogue\": "
                        "[{\"speaker\": \"character `s name\", \"text\": \"dialogue text\", \"emotion\": \"emotion\"}, "
                        "etc.]}]}"}
            ]
        return messages

    def generate_movie_script(self, prompt: str, universe: dict):
        """ Generate a movie script based on the given prompt and universe parameters. """
        # Подготовка данных
        message = self.get_prompt_for_script_json(prompt, universe)

        # Запрос к модели ChatGPT
        responses = self.get_llm_response(message)

        return responses
    