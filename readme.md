# Werewolf 12
A highly flexible framework utilizing the features of the Python programming language for multi-Agent scenarios.

## Features
* Core code is less than 100 lines.
* Capable of automatic process control.
* Usable in scenarios requiring collaboration among multiple Agents.
* Equipped with information shielding and domain control functions.
* Provides a complete 12-player Werewolf game case as a reference.

## Preparations Before Use
1. Configure environment variables.
2. Modify the `llm` function to select the model you prefer to use.
# Documentation for Functions

This document provides explanations for each function in the given Python code. The code appears to handle some form of messaging system, possibly for a game or a chat application.

## Function Descriptions

### `split_txt_to_dict(txt)`
- **Purpose**: Splits a given text into dictionary entries based on headers.
- **Parameters**:
  - `txt` (str): The input text to be split.
- **Returns**: A dictionary where the keys are headers (preceded by "###") and the values are the contents following each header.

### `filter_history(history, player_name, phase)`
- **Purpose**: Filters a history of messages to include only those that should be kept for a specific player in a certain phase.
- **Parameters**:
  - `history` (list): A list of message objects.
  - `player_name` (str): The name of the player.
  - `phase` (any): The current phase to filter by.
- **Returns**: A list of message objects that should be kept based on player name and phase.

### `history_to_str(history)`
- **Purpose**: Converts a list of message objects to a formatted string.
- **Parameters**:
  - `history` (list): A list of message objects.
- **Returns**: A string where each message is formatted as "【sender】content", separated by '/n'.

### `llm(prompt=COT_PROMPT, **kwargs)`
- **Purpose**: Sends a prompt to a language model and retries up to twice with a wait of 2 seconds if the request fails.
- **Parameters**:
  - `prompt` (str): The prompt to send to the language model. Defaults to `COT_PROMPT`.
  - `**kwargs`: Additional keyword arguments for formatting the prompt.
- **Returns**: The content of the response from the language model.

### `Message` Class (Dataclass)
- **Attributes**:
  - `sender` (str): The sender of the message. Defaults to "System".
  - `receiver_limit` (list): List of receivers who are allowed to receive the message.
  - `content` (str): The content of the message.
  - `stage_limit` (list): List of stages during which the message can be displayed.
- **Methods**:
  - `is_allowed(role_name, stage)`
    - **Purpose**: Checks if a message is allowed to be received based on role name and stage.
    - **Parameters**:
      - `role_name` (str): The role name to check.
      - `stage` (any): The current stage to check.
    - **Returns**: `True` if the message is allowed, otherwise `False`.

### `history_to_answer(player='Host', receivers=None, stage=None, answer_stage=[])`
- **Purpose**: Converts the history to an answer formatted for a specific player and adds it to the history.
- **Parameters**:
  - `player` (str): The player to generate the answer for. Defaults to 'Host'.
  - `receivers` (list): List of receivers. Defaults to `None`.
  - `stage` (any): The current stage. Defaults to `None`.
  - `answer_stage` (list): The stages for which the answer is valid. Defaults to an empty list.
- **Returns**: The generated answer.

### `parallel_history_to_answer(players=[], receivers=None, stage=None, answer_stage=[])`
- **Purpose**: Generates answers for multiple players in parallel and adds them to the history.
- **Parameters**:
  - `players` (list): List of player names.
  - `receivers` (list): List of receivers. Defaults to `None`.
  - `stage` (any): The current stage. Defaults to `None`.
  - `answer_stage` (list): The stages for which the answer is valid. Defaults to an empty list.

### `history_to_answer_not_adding_to_history(player='Host', stage=None)`
- **Purpose**: Converts the history to an answer for a specific player without adding the answer to the history.
- **Parameters**:
  - `player` (str): The player to generate the answer for. Defaults to 'Host'.
  - `stage` (any): The current stage. Defaults to `None`.
- **Returns**: The generated answer.

### `add_message_to_history(content, player='System', receivers=None, stage=None)`
- **Purpose**: Adds a new message to the history.
- **Parameters**:
  - `content` (str): The content of the message.
  - `player` (str): The player sending the message. Defaults to 'System'.
  - `receivers` (list): List of receivers. Defaults to `None`.
  - `stage` (any): The current stage. Defaults to `None`.