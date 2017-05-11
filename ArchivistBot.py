# ArchivistBot.py
# Version 0.1
# Purpose:
# For the indexing and querying of text

import discord
import asyncio
import random
import secrets
import pickle
import re
from make_index import reverse_tree

ADMIN_ID = "Put your ID here as a string"
INPUT_DICT = {"tts": "TTS.pickle"}
BOOL_FLAGS = ["-exact"]
FLAGS = ["-chapter", "-context"]
CONTEXT_LIMIT = 2
SEARCH_LIMIT = 5

HELP_MESSAGE = """```Commands:
!random name_of_work WORD WORD : Pick a random paragraph
!search name_of_work WORD WORD : Show all found (Up to 5)
!index name_of_work CHAPTER# PARAGRAPH#: Return specified Chapter and Paragraph

By default searches look for paragraphs that have all the words (in any order). The following flags are available:

-exact : Makes the search look for that exact phrase
-chapter # : Makes the search only look in a specific chapter
-context # : Will provide 0-2 additional paragraphs before and after each result.

Works available: tts
```"""

def full_query(big_tree, chapter_dict, tree_depth, query_list):
    if len(query_list) <= tree_depth:
        return big_tree.full_query(query_list)
    query_response = big_tree.full_query(query_list[:tree_depth])
    actual_list = []
    for chapter, paragraph in query_response:
        this_paragraph = chapter_dict[chapter][paragraph]
        ascii_paragraph = this_paragraph.encode("utf-8", "ignore").decode("ascii", "ignore")
        word_list = re.split('[\s—\n\r]', this_paragraph)  
        for index, word in enumerate(word_list):
            word_list[index] = re.sub('([^\w\-é\'])+', '', word)
        word_list = [w for w in word_list if w]
        # Search this list for query_list. Yes this is inefficient. There are much better algorithms for this (suffix search, etc.) but fuck it for now.
        for x in range(len(word_list) - len(query_list) + 1):
            found = True
            for counter, y in enumerate(word_list[x:x + len(query_list)]):
                if query_list[counter] != y.lower():
                    found = False
                    break
            if found:
                actual_list.append((chapter, paragraph))
    return actual_list
    
def process_flags(message_list):
    new_message_list = []
    flag_dict = {}
    skip = False
    for index, word in enumerate(message_list):
        if skip:
            skip = False
            continue
        if word in FLAGS:
            skip = True
            flag_dict[word] = message_list[index+1]
        elif word in BOOL_FLAGS:
            flag_dict[word] = True
        else:
            new_message_list.append(word)
    return flag_dict, new_message_list
    
def isolate_chapter(query_response, chapter):
    return [x for x in query_response if x[0] == "Chapter " + chapter]
    
def chapter_get(chapter_dict, chapter, paragraph, context=0):
    context = int(context)
    if context > CONTEXT_LIMIT:
        context = CONTEXT_LIMIT
    minimum = max(0, paragraph - context)
    maximum = min(len(chapter_dict[chapter]) - 1, paragraph + context)
    out_list = []
    for x in range(minimum, maximum + 1):
        out_list.append(chapter_dict[chapter][x])
    return "```" + "".join(out_list) + "\n- " + chapter + ", Paragraph " + str(paragraph) + "```"

class Archivebot(object):
    def main(self):
        client = discord.Client()
        
        lookup_dict = {}
        for key, value in INPUT_DICT.items():
            lookup_dict[key] = {}
            with open(value, "rb") as file:
                lookup_dict[key]["chapter_dict"] = pickle.load(file)
                lookup_dict[key]["big_tree"] = pickle.load(file)
                lookup_dict[key]["tree_depth"] = pickle.load(file)
        
        @client.event
        async def on_ready():
            print('Logged in as')
            print(client.user.name)
            print(client.user.id)
            print('------')

        @client.event
        async def on_message(message):
            
            this_message = message.content.lower()
            if this_message == "!help search":
                await client.send_message(message.channel, HELP_MESSAGE)
            attempt_split = this_message.split()
            if len(attempt_split) > 1:
                if attempt_split[0] in ["!random", "!search"]:
                    if attempt_split[1] not in lookup_dict:
                        return
                    big_tree = lookup_dict[attempt_split[1]]["big_tree"]
                    chapter_dict = lookup_dict[attempt_split[1]]["chapter_dict"]
                    tree_depth = lookup_dict[attempt_split[1]]["tree_depth"]
                    flag_dict, new_message_list = process_flags(attempt_split[2:])
                    if "-exact" in flag_dict:
                        if not new_message_list:
                            query_result = full_query(big_tree, chapter_dict, tree_depth, [])
                        else:
                            query_result = full_query(big_tree, chapter_dict, tree_depth, new_message_list)
                    else:
                        query_result = big_tree.query(new_message_list)
                    query_result = isolate_chapter(query_result, flag_dict["-chapter"]) if "-chapter" in flag_dict else query_result
                    if not query_result:
                        return
                    context = flag_dict["-context"] if "-context" in flag_dict else 0
                    if attempt_split[0] == "!random":
                        temp = random.choice(list(query_result))
                        await client.send_message(message.channel, chapter_get(chapter_dict, temp[0], temp[1], context))
                    elif attempt_split[0] == "!search":
                        temp = list(query_result)
                        for para in temp[:min(len(temp), SEARCH_LIMIT)]:
                            await client.send_message(message.channel, chapter_get(chapter_dict, para[0], para[1], context))
                        if len(temp) > SEARCH_LIMIT:
                            await client.send_message(message.channel, "WARNING: RESULTS EXCEEDED SEARCH LIMIT. TRY BEING MORE SPECIFIC.")       
                    return
                elif attempt_split[0] == "!index":
                    if attempt_split[1] not in lookup_dict:
                        return
                    chapter_dict = lookup_dict[attempt_split[1]]["chapter_dict"]
                    flag_dict, new_message_list = process_flags(attempt_split[2:])
                    context = flag_dict["-context"] if "-context" in flag_dict else 0
                    await client.send_message(message.channel, chapter_get(chapter_dict, "Chapter " + new_message_list[0], int(new_message_list[1]), context))
            
            #Return Status of the bot
            if message.content.lower() == '!botstat' :
                await client.send_message(message.channel, 'Gamebot Online')
                await client.send_file(message.channel, 'Botishere.png')   
                return
                
            elif message.content.lower() == '!archiveshutdown' and message.author.id == ADMIN_ID:
                await client.logout()
                return

            
                    
                
        # Blocking. Must be last.
        client.run(secrets.BOT_TOKEN)

if __name__ == '__main__':
    bot = Archivebot()
    bot.main()
    
    


