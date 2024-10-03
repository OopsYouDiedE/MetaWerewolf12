import openai
from dotenv import load_dotenv

load_dotenv(verbose=True)
client = openai.OpenAI()  # Parameters are set in the .env file

COT_PROMPT = """
### SYSTEM
Your response should be as concise as possible. Please fill in your thought process in the THOUGHT section and provide your conclusion in the ANSWER section.
### HISTORY
{history}
### THOUGHT
(wait to fulfill)
### ANSWER
(wait to fulfill)
"""

CONCLUDE_PROMPT = """
## SYSTEM
Please summarize the content in HISTORY. The summary should retain all key points. Please fill in the summary in the CONCLUDE section.
## HISTORY
{h_str}
## CONCLUDE
(wait to fulfill)
"""

import re


def split_txt_to_dict(txt):
    # Regex rule is ## any
    splits = re.split(r'### (.*?)\s*\n', txt)
    return {splits[i].strip(): splits[i + 1].strip() for i in range(1, len(splits) - 1, 2)}


def filter_history(history, player_name, phase):
    return [msg for msg in history if msg.should_keep(player_name, phase)]


def history_to_str(history):
    return '/n'.join(["【" + msg.sender + "】" + msg.content for msg in history])


from retrying import retry


@retry(stop_max_attempt_number=2, wait_fixed=2000)
def llm(prompt=COT_PROMPT, **kwargs):
    return client.chat.completions.create(
        messages=[{'role': 'user', 'content': [{'type': 'text', 'text': prompt.format(**kwargs)}]}],
        model='claude-3-5-sonnet-20240620').choices[0].message.content


import random

from dataclasses import dataclass


@dataclass
class Message:
    sender: str = "System"
    receiver_limit: list = None
    content: str = ""
    stage_limit: list = None

    def is_allowed(self, role_name, stage):
        allowed_to_receive = not self.receiver_limit or role_name in self.receiver_limit or role_name == self.sender
        message_restricted = not self.stage_limit or stage in self.stage_limit

        return allowed_to_receive and message_restricted


history = []
all_history = ''


def history_to_answer(player='Host', receivers=None, stage=None, answer_stage=[]):
    global history
    global all_history
    if not answer_stage: answer_stage = stage
    filtered_history = filter_history(history, player, stage)
    out = llm(history=history_to_str(filtered_history))
    print(f"## {player}\n{out}\n")
    answer = split_txt_to_dict(out)['ANSWER']
    history.append(Message(player, receivers, answer, answer_stage))
    return answer


def parallel_history_to_answer(players=[], receivers=None, stage=None, answer_stage=[]):
    global history
    if not answer_stage: answer_stage = stage
    history.extend([Message(player, receivers, history_to_answer_not_adding_to_history(player, stage), answer_stage) for player in players])


def history_to_answer_not_adding_to_history(player='Host', stage=None):
    global history
    global all_history
    filtered_history = filter_history(history, player, stage)
    out = llm(history=history_to_str(filtered_history))
    print(f"## {player}\n{out}\n")
    answer = split_txt_to_dict(out)['ANSWER']
    return answer


def add_message_to_history(content, player='System', receivers=None, stage=None):
    global history
    global all_history
    print(f"## {player}\n### GUIDE MESSAGE\n{content}\n")
    history.append(Message(player, receivers, content, stage))


if __name__ == "__main__":
    history = []
    roles = ['Villager'] * 4 + ['Werewolf'] * 4 + ['Witch', 'Seer', 'Hunter', 'Idiot']
    players = [f'Player {i}' for i in range(len(roles))]
    random.shuffle(roles)

    add_message_to_history(
        "You are now playing the Werewolf game. There are a total of 12 players on the field, numbered as Player 0 to Player 11. Among them are 4 Werewolves, 4 Villagers, as well as Witch, Seer, Idiot, and Hunter. The Werewolves' winning condition is to kill all villagers or all special roles, while the villagers and special roles' winning condition is to kill all werewolves.")
    history += [Message("System", player, f"{player}, your role is {role}", None) for player, role in
                zip(players, roles)]
    add_message_to_history(
        "There are a total of 12 players on the field, with IDs ranging from Player 0 to Player 11. Here are the identity details of these players: " + str(
            {player: role for player, role in zip(players, roles)}),
        receivers='Host')
    add_message_to_history("It's nighttime, please close your eyes. Werewolves, please open your eyes.")
    stage = "Night Werewolves"
    add_message_to_history("Please tell me the currently surviving Werewolves, the return should be list[str]",
                           "System", "Host", stage)
    werewolf_list = eval(history_to_answer('Host', 'System', stage))
    add_message_to_history(f"Your teammates are {', '.join(werewolf_list)}.", "Host", werewolf_list, None)
    for round in range(1, 8):
        stage = f"Night Werewolves {round}"
        add_message_to_history("Tell me which player you want to kill tonight.", "Host", werewolf_list, stage)
        for werewolf in werewolf_list: history_to_answer(werewolf, werewolf_list + ['Host'], stage)
        add_message_to_history(
            "Which player was most voted to be killed by the werewolves? (If tied, please randomly select one) Please respond by saying: Player x was killed by werewolves last night.",
            'System', 'Host', stage)
        history_to_answer('Host', 'System', stage, None)

        stage = f"Night Witch {round}"
        add_message_to_history("Please tell me the currently surviving Witch, the return should be list[str]", 'System',
                               'Host', stage)
        witch_list = eval(history_to_answer('Host', 'System', stage))
        if witch_list:
            add_message_to_history(
                "The Witch has one healing potion and one poison. If the Witch has used the healing potion, respond 'skip'. Otherwise, tell the Witch the name of the person who died last night, then ask if the Witch wants to use the healing potion. The Witch cannot use the potion on themselves, but they can use the poison before they die.",
                'System', 'Host', stage)
            if "skip" not in history_to_answer('Host', witch_list, stage):
                history_to_answer(witch_list[0], 'Host', stage, None)
            add_message_to_history(
                "The Witch has one healing potion and one poison. If the Witch has used the poison, respond 'skip'. Otherwise, ask the Witch which player they want to poison.",
                'System', 'Host', stage)
            if "skip" not in history_to_answer('Host', witch_list, stage):
                history_to_answer(witch_list[0], 'Host', stage, None)

        stage = f"Night Seer {round}"
        add_message_to_history("Please tell me the currently surviving Seer, the return should be list[str]", 'System',
                               'Host', stage)
        seer_list = eval(history_to_answer('Host', 'System', stage))
        if seer_list:
            add_message_to_history("Seer, tell me which player you want to check the identity of?", 'Host',
                                   seer_list[0])
            history_to_answer(seer_list[0], 'Host', stage)
            add_message_to_history(
                "Only tell the Seer whether the person they checked is good or bad. Do not consider whether this person is alive.",
                'System', 'Host', stage)
            history_to_answer('Host', seer_list, stage, None)

        stage = f"Night Hunter {round}"
        add_message_to_history(
            "If the Hunter was killed last night but not by the Witch, return a list[str] containing the name of the Hunter, otherwise return an empty list",
            'System', 'Host', stage)
        hunter_list = eval(history_to_answer('Host', 'System', stage))
        if hunter_list:
            add_message_to_history(
                "Hunter, you were killed last night. Do you choose to take revenge? If so, which player do you choose?",
                'Host', hunter_list[0])
            history_to_answer(hunter_list[0], 'Host', stage, None)

        if round == 1:
            stage = "Sheriff Election Phase"
            add_message_to_history(
                "Players, please prepare to run for Sheriff. The Sheriff can decide the speaking order, whether to start from their left or right. The Sheriff also has two votes during voting. If you want to run for Sheriff, give a speech, if not, say 'skip'",
                "Host", None, stage)
            parallel_history_to_answer(players, players, stage)
            add_message_to_history("Players, please vote for the Sheriff, only one player can be voted for.", "Host",
                                   None, stage)
            parallel_history_to_answer(players, players + ['Host'], stage)
            add_message_to_history("If there is a tie, say 'Re-vote'. Otherwise, announce which player is the Sheriff.",
                                   "Host", None, stage)
            result = history_to_answer('Host', None, stage, None)
            if 'tie' in result:
                add_message_to_history("Players, please vote again, only one player can be voted for.", "Host", None,
                                       stage)
                parallel_history_to_answer(players, players + ['Host'], stage)
                add_message_to_history(
                    "If it is still a tie, announce no one is elected as Sheriff. Otherwise, announce which player is the Sheriff.",
                    "Host", None, stage)
                result = history_to_answer('Host', None, stage, None)

        stage = f"Daybreak {round}"
        add_message_to_history("It's daybreak.")
        add_message_to_history("Please tell everyone who was killed last night.", 'System', 'Host', stage)
        add_message_to_history(
            "If the Sheriff was killed last night, return a list[str] containing the name of the Sheriff, otherwise return an empty list",
            "Host", None, stage)
        sheriff_list = eval(history_to_answer('Host', 'System', stage, None))
        if sheriff_list:
            add_message_to_history("Sheriff, you have two options. Pass the badge to someone else, or destroy it.",
                                   'Host', sheriff_list[0])
            history_to_answer(sheriff_list[0], None, stage, None)
        history_to_answer('Host', None, stage, None)
        add_message_to_history(
            "Please tell me the currently surviving players, the return should be list[str]. If the identity of the Idiot is revealed, the Idiot will be excluded.",
            "System", "Host", stage)

        player_list = eval(history_to_answer('Host', 'System', stage, None))
        add_message_to_history(
            "Please tell me if the game has reached an end condition, where either all Werewolves, Villagers, or special roles are dead? If all Villagers or special roles are dead, say: 'Werewolves win'. If all Werewolves are dead, say: 'Villagers win'. Otherwise, say: 'skip'.",
            "System", "Host", stage)
        finish = history_to_answer('Host', 'System', stage, stage)
        if 'skip' not in finish:
            print(finish)
            break

        if round == 1:
            add_message_to_history("Please tell me the players who died last night, the return should be list[str].",
                                   'System', 'Host', stage)
            dead_player_list = eval(history_to_answer('Host', 'System', stage, None))
            add_message_to_history("Let the players who died on the first night leave their last words.", "Host", None,
                                   stage)
            parallel_history_to_answer(dead_player_list, player_list + ['Host'], stage)

        add_message_to_history(
            "If the Sheriff is still alive, return a list[str] containing the name of the Sheriff, otherwise return an empty list",
            "Host", None, stage)
        sheriff_list = eval(history_to_answer('Host', 'System', stage, None))
        if sheriff_list:
            add_message_to_history(
                "Sheriff, tell me if you choose to start the speeches from the left or the right side of you. You should be the last to speak. Provide a speaking order, a list[str] containing the names of all surviving players. If the identity of the Idiot is revealed, the Idiot will be excluded.",
                'Host', sheriff_list[0])
            player_list = eval(history_to_answer('Sheriff', 'System', stage, stage))

        history_to_answer('Host', None, stage, None)
        add_message_to_history("Please speak in the above order. After the speeches, players will vote.", "System",
                               "Host", stage)
        parallel_history_to_answer(player_list, player_list + ['Host'], stage)
        add_message_to_history("Please think and summarize the current situation.", 'System', player_list, stage)
        parallel_history_to_answer(player_list, [''], stage, None)

        stage = f"Voting {round}"
        add_message_to_history("Which player do you want to vote for?", "Host", player_list, stage)
        parallel_history_to_answer(player_list, player_list + ['Host'], stage)
        add_message_to_history(
            "Which player received the most votes? (If there's a tie or no one voted, say 'Due to a tie, no one is voted out'). The Sheriff counts as 2 votes. Respond by saying: Player x was voted out during the day.",
            'System', 'Host', stage)
        history_to_answer('Host', None, stage, None)
        add_message_to_history("Please think and summarize the current situation.", 'System', player_list, stage)
        for player in player_list: history_to_answer(player, [''], stage, None)

        stage = f"After Voting {round}"
        add_message_to_history("Please tell me which player was voted out, the return should be list[str]", "System",
                               'Host', stage)
        voted_out_player_list = eval(history_to_answer('Host', 'System', stage, None))
        add_message_to_history("Players who were voted out, please leave your last words.", "Host", None, stage)
        for player in voted_out_player_list: history_to_answer(player, voted_out_player_list, stage)
        add_message_to_history(
            "If the Hunter was voted out, return a list[str] containing the name of the Hunter, otherwise return an empty list",
            'System', 'Host', stage)
        hunter_list = eval(history_to_answer('Host', 'System', stage))
        if hunter_list:
            add_message_to_history("Hunter, do you choose to take revenge? If so, which player do you choose?", 'Host',
                                   hunter_list[0])
            history_to_answer(hunter_list[0], 'Host', stage, None)

        add_message_to_history(
            "Was the player who was voted out the Idiot? If so, say 'Player x is the Idiot, they cannot participate in further discussions, nor can they be chosen as Sheriff.'",
            "Host", None, stage)
        history_to_answer('Host', None, stage)

