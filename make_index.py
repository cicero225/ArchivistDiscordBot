
from collections import deque
import os
import re
import string
import pickle

FOLDER_NAME = "TTS"
TREE_DEPTH = 3
OUTPUT_FILE = "TTS.pickle"

class reverse_tree:
    def __init__(self):
        self.node = {}
        self.terminal = set()
    
    def query(self, words):
        out_set = set()
        if words:
            first = True
            for word in words:
                if word not in self.node:
                    return set()
                if first:
                    first = False
                    out_set = self.node[word].full_query([])
                else:
                    out_set &= self.node[word].full_query([])
                if not out_set:
                    break
        return out_set        
    
    def full_query(self, words):
        words = list(words)
        out_set = set()
        if not words:
            out_set |= self.terminal
            for leaf in self.node.values():
                out_set |= leaf.full_query(words)
        else:
            this_word = words[0].lower()
            if this_word in self.node:
                out_set |= self.node[this_word].full_query(words[1:])
        return out_set
        
    def add_entry(self, words, entry):
        words = list(words)
        if not words:
            self.terminal.add(entry)
        else:
            this_word = words[0].lower()
            if this_word not in self.node:
                self.node[this_word] = reverse_tree()
            self.node[this_word].add_entry(words[1:], entry)

    def __repr__(self):
        part = self.node.__repr__()
        part += "\n" + self.terminal.__repr__()
        return part
            
def main():
    _, _, filenames = next(os.walk(os.path.join(os.path.curdir, FOLDER_NAME)))
    chapter_dict = {}
    counter = 0
    for fname in filenames:
        clean_name, _ = os.path.splitext(fname[5:])
        chapter_dict[clean_name] = []
        paragraph_counter = 0
        with open(os.path.join(os.path.curdir, FOLDER_NAME, fname), "r", encoding='utf8') as file:
            chapter_dict[clean_name].append("")
            for line in file:
                if re.fullmatch('[\r\n]+', line):
                    paragraph_counter += 1
                    chapter_dict[clean_name].append("")
                chapter_dict[clean_name][paragraph_counter] +=  line
        counter += 1
    big_tree = reverse_tree()
    for name, chapter in chapter_dict.items():
        for counter, paragraph in enumerate(chapter):
            ascii_paragraph = paragraph.encode("utf-8", "ignore").decode("ascii", "ignore")
            word_list = re.split('[\s—\n\r]', paragraph)    
            for index, word in enumerate(word_list):
                word_list[index] = re.sub('([^\w\-é\'])+', '', word)
            word_list = [w for w in word_list if w]
            tracking_list = deque(maxlen = TREE_DEPTH)
            for word in word_list:
                tracking_list.append(word)
                big_tree.add_entry(tracking_list, (name, counter))
    
    with open(OUTPUT_FILE, "wb") as file:
        pickle.dump(chapter_dict, file, -1)
        pickle.dump(big_tree, file, -1)
        pickle.dump(TREE_DEPTH, file, -1)

if __name__ == "__main__":
    main()