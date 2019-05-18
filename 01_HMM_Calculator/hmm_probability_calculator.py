# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 16:35:24 2019

@author: Sivaraman Lakshmipathy
"""

class tag_unit:
    tag = ""
    count = 0
    likelihood_prob = 0

    def __init__(self, tag_val, count=1):
        self.tag = tag_val
        self.count = count
        self.likelihood_prob = 0

    def increment_count(self, count=1):
        self.count += count

    def get_count(self):
        return self.count

    def get_likelihood_prob(self):
        return self.likelihood_prob

    def get_tag(self):
        return self.tag

    def calculate_likelihood_prob(self, tag_count):
        self.likelihood_prob = round(self.count / tag_count, 3)

class lexical_unit:
    value = ""
    tag = {}

    def __init__(self, val, tag_val, count=1):
        self.value = val
        self.tag = {}
        self.tag[tag_val] = tag_unit(tag_val, count)

    def increment_count(self, tag_val, count=1):
        if tag_val in self.tag:
            self.tag[tag_val].increment_count(count)
        else:
            self.tag[tag_val] = tag_unit(tag_val, count)

    def get_tags(self):
        return self.tag.keys()

    def get_count(self, tag_val):
        return self.tag[tag_val].get_count()

    def get_likelihood_prob(self, tag_val):
        return self.tag[tag_val].get_likelihood_prob()

    def calculate_likelihood_prob(self, tag_val, tag_count):
        self.tag[tag_val].calculate_likelihood_prob(tag_count)

    def get_likelihood_prob_str(self, tag_val):
        if tag_val in self.tag:
            return "P(" + self.value + "|" + tag_val + ") = " + str(self.tag[tag_val].get_likelihood_prob())
        else:
            return "P(" + self.value + "|" + tag_val + ") = 0"

    def get_count_str(self, tag_val):
        if tag_val in self.tag:
            return "C(" + self.value + "|" + tag_val + ") = " + str(self.tag[tag_val].get_count())
        else:
            return "C(" + self.value + "|" + tag_val + ") = 0"

    def print_lexical_tag_unit_count(self):
        for tags in self.tag:
            print(self.get_count_str(tags))

    def print_lexical_tag_unit_likelihood_prob(self):
        for tags in sorted(self.tag):
            print(self.get_likelihood_prob_str(tags))

    def writeToFile_lexical_tag_unit_likelihood_prob(self, fileObj, endLine):
        for tags in sorted(self.tag):
            fileObj.write(self.get_likelihood_prob_str(tags))
            fileObj.write(endLine)

    def get_lex_tag_obj(self, tag_val):
        if tag_val in self.tag:
            return self.tag[tag_val]
        else:
            return None

class hmm:
    corpus_filepath = ""
    corpus_filename = ""
    unique_lexical_tag_combo = {} #to hold the unique lexical units in the corpus
    unique_tag = {} #to hold the counts of all unique tags in the corpus
    tag_transition = {} #to hold all the possible tag transitions in the corpus
    tag_transition_prob = {} #to hold all the possible tag transition probabilities in the corpus

    def __init__(self, filename):
        self.corpus_filename = filename
        self.unique_lexical_tag_combo = {}
        self.unique_tag = {
            "<s>": 0
        }
        self.tag_transition = {}
        self.tag_transition_prob = {}
        self.populate_corpus_memory()

    def populate_corpus_memory(self):
        file_obj = open(self.corpus_filename, "r")
        for line in file_obj:
            self.process_lines(line)
        self.calculate_likelihood_probabilities()
        self.calculate_transition_probabilities()

    def calculate_likelihood_probabilities(self):
        for key in self.unique_lexical_tag_combo.keys():
            lex_obj = self.unique_lexical_tag_combo[key]
            for tag_obj in lex_obj.get_tags():
                lex_obj.calculate_likelihood_prob(tag_obj,  self.unique_tag[tag_obj])

    def print_likelihood_probabilities(self):
        for key in sorted(self.unique_lexical_tag_combo.keys()):
            lex_obj = self.unique_lexical_tag_combo[key]
            lex_obj.print_lexical_tag_unit_likelihood_prob()

    def writeToFile_likelihood_probabilities(self, fileObj, endLine):
        for key in sorted(self.unique_lexical_tag_combo.keys()):
            lex_obj = self.unique_lexical_tag_combo[key]
            lex_obj.writeToFile_lexical_tag_unit_likelihood_prob(fileObj, endLine)

    def calculate_transition_probabilities(self):
        for entry in self.tag_transition:
            prev_tag = entry.split("|")[1]
            self.tag_transition_prob[entry] = round(self.tag_transition[entry] / self.unique_tag[prev_tag], 3)

    def print_transition_probabilities(self):
        for entry in sorted(self.tag_transition_prob):
            print("P(" + entry + ") = " + str(self.tag_transition_prob[entry]))

    def writeToFile_transition_probabilities(self, fileObj, endLine):
        for entry in sorted(self.tag_transition_prob):
            fileObj.write("P(" + entry + ") = " + str(self.tag_transition_prob[entry]))
            fileObj.write(endLine)


    def process_lines(self, line):
        tokens = line.strip().split(" ")
        self.unique_tag["<s>"] += 1
        prev_tag = "<s>"
        for token in tokens:
            split_token = token.split("/")
            word = split_token[0]
            tag = split_token[1]
            cur_tag = tag
            transition_tags = cur_tag + "|" + prev_tag
            if word in self.unique_lexical_tag_combo:
                self.unique_lexical_tag_combo[word].increment_count(tag)
            else:
                new_lex_obj = lexical_unit(word, tag)
                self.unique_lexical_tag_combo[word] = new_lex_obj
            if tag in self.unique_tag:
                self.unique_tag[tag] += 1
            else:
                self.unique_tag[tag] = 1
            if transition_tags in self.tag_transition:
                self.tag_transition[transition_tags] += 1
            else:
                self.tag_transition[transition_tags] = 1
            prev_tag = tag

    def writeToFile(self, type, fileName):
        fileObj = open(fileName, "w")
        endLine = "\n"

        if "lexical_prob" == type:
            self.writeToFile_likelihood_probabilities(fileObj, endLine)
        elif "tag_transition" == type:
            self.writeToFile_transition_probabilities(fileObj, endLine)

        fileObj.close()

    def mle_calculator(self, test_str, prev_tag="<s>", prev_const_prob_seq="", prev_const_prob=1, prob_map = {}):
        if "." == test_str:
            first_token = test_str
            new_test_str = ""
        elif " " not in test_str:
            first_token = test_str[:len(test_str)-1]
            new_test_str = "."
        elif " " in test_str:
            first_token_indx = test_str.index(" ")
            first_token = test_str[:first_token_indx]
            new_test_str = test_str[first_token_indx+1:]
        else:
            print("Empty string encountered.")
            return prob_map
        if first_token not in self.unique_lexical_tag_combo:
            return prob_map
        lex_obj = self.unique_lexical_tag_combo[first_token]
        tag_list = lex_obj.get_tags()
        for tag_obj in tag_list:
            cur_tag_obj = lex_obj.get_lex_tag_obj(tag_obj)
            cur_tag = cur_tag_obj.get_tag()
            tag_transition_str = cur_tag + "|" + prev_tag
            constr_seq = prev_const_prob_seq + "(" + first_token + "|" + cur_tag + ")"
            if tag_transition_str in self.tag_transition_prob:
                constr_prob = prev_const_prob * cur_tag_obj.get_likelihood_prob() * self.tag_transition_prob[tag_transition_str]
            else:
                constr_prob = 0

            if "." == first_token:
                prob_map[len(prob_map) + 1] = {
                    "seq": constr_seq,
                    "prob": constr_prob
                }
                return prob_map
            else:
                prob_map = self.mle_calculator(new_test_str, cur_tag, constr_seq, constr_prob, prob_map)
        if "<s>" != prev_tag:
            return prob_map
        return prob_map

    def calculate_mle(self, test_str, output_filename):
        prob_map = self.mle_calculator(test_str)
        fileObj = open(output_filename, "w")
        endLine = "\n"
        self.printLexTagProb(prob_map)
        self.writeLexTagProb(prob_map, fileObj, endLine)
        fileObj.write(endLine)
        self.printMaxProbTaggingSeq(prob_map)
        self.writeMaxProbTaggingSeq(prob_map, fileObj, endLine)
        fileObj.close()

    def printLexTagProb(self, prob_map, fileObj = None, endLine = "\n"):
        if fileObj is not None:
            self.writeLexTagProb(prob_map, fileObj, endLine)
            return
        print("Available Lexical Tagging combinations with their calculated probabilities:")
        if len(prob_map) < 1:
            print("None")
            return
        for indx in prob_map.keys():
            entry = prob_map[indx]
            seq = entry["seq"]
            prob = entry["prob"]
            print(seq + " : " + str(prob))

    def writeLexTagProb(self, prob_map, fileObj = None, endLine = "\n"):
        fileObj.write("Available Lexical Tagging combinations with their calculated probabilities:")
        fileObj.write(endLine)
        if len(prob_map) < 1:
            fileObj.write("None")
            fileObj.write(endLine)
            return
        for indx in prob_map.keys():
            entry = prob_map[indx]
            seq = entry["seq"]
            prob = entry["prob"]
            fileObj.write(seq + " : " + str(prob))
            fileObj.write(endLine)

    def printMaxProbTaggingSeq(self, prob_map, fileObj = None, endLine = "\n"):
        if fileObj is not None:
            self.writeMaxProbTaggingSeq(prob_map, fileObj, endLine)
            return
        print("POS tagging with maximum probability:")
        if len(prob_map) < 1:
            print("None")
            return
        max = 0.0
        max_indx = -1
        for indx in prob_map.keys():
            entry = prob_map[indx]
            prob = entry["prob"]
            if max < prob:
                max = prob
                max_indx = indx
        if max_indx == -1:
            print("None")
            return
        else:
            print(prob_map[max_indx]["seq"] + " : " + str(max))

    def writeMaxProbTaggingSeq(self, prob_map, fileObj = None, endLine = "\n"):
        fileObj.write("POS tagging with maximum probability:")
        fileObj.write(endLine)
        if len(prob_map) < 1:
            fileObj.write("None")
            return
        max = 0.0
        max_indx = -1
        for indx in prob_map.keys():
            entry = prob_map[indx]
            prob = entry["prob"]
            if max < prob:
                max = prob
                max_indx = indx
        if max_indx == -1:
            fileObj.write("None")
            fileObj.write(endLine)
            seq = prob_map[1]["seq"]
            self.writeSeqProb(fileObj, seq, endLine)
            return
        else:
            seq = prob_map[max_indx]["seq"]
            fileObj.write(prob_map[max_indx]["seq"] + " : " + str(max))
            fileObj.write(endLine)
            self.writeSeqProb(fileObj, seq, endLine)

    def writeSeqProb(self, fileObj, seq, endLine = "\n"):
        fileObj.write(endLine)
        fileObj.write("Probability values used:")
        print("\nProbability values used:")
        fileObj.write(endLine)
        tokens = seq.strip().split(")")
        prev_tag = "<s>"
        for token in tokens:
            if "" == token:
                return
            token_strip = token.strip("(").strip(")")
            indv_token = token_strip.split("|")
            lex = indv_token[0]
            tag = indv_token[1]
            tag_transition = tag + "|" + prev_tag
            lex_prob = 0
            tag_transition_prob = 0
            if lex in self.unique_lexical_tag_combo:
                lex_prob = self.unique_lexical_tag_combo[lex].tag[tag].get_likelihood_prob()
            if tag_transition in self.tag_transition_prob:
                tag_transition_prob = self.tag_transition_prob[tag_transition]
            fileObj.write("P" + token + ") : " + str(lex_prob))
            fileObj.write(", ")
            fileObj.write("P(" + tag_transition + ") : " + str(tag_transition_prob))
            fileObj.write(endLine)
            print("P" + token + ") : " + str(lex_prob) + ", " + "P(" + tag_transition + ") : " + str(tag_transition_prob))
            prev_tag = tag

def readTestData(fileName):
    fileObj = open(fileName, "r")
    return fileObj.readline().strip()

def main():
    corpus_filename = "POS_corpus.txt"
    lexical_prob_output_file = "lexical_prob.txt"
    transition_prob_output_file = "transition_prob.txt"
    testset_input_file = "testset.txt"
    testset_tag_output_file = "testset_output.txt"
    hmm_processor = hmm(corpus_filename)
    hmm_processor.writeToFile("lexical_prob", lexical_prob_output_file)
    hmm_processor.writeToFile("tag_transition", transition_prob_output_file)
    test_set = readTestData(testset_input_file)
    hmm_processor.calculate_mle(test_set, testset_tag_output_file)

if __name__ == '__main__':
    main()
