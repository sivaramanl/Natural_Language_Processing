# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 18:12:36 2019

@author: Sivaraman Lakshmipathy, Yatri Modi
"""

import os
import sys
import nltk
from nltk.parse import CoreNLPParser
from gensim.models import KeyedVectors, Word2Vec

from queryForm import queryForm
from transition import transition

class custom_parse_handler:
    corenlp_host = 'http://localhost:9000'  # CoreNLP server host
    main_categories = ['geography', 'music', 'movies']  # Categories utilized in the project

    def __init__(self, input_file, output_file, dbConnector):
        self.ip_file = input_file  # Input statements
        self.op_file = output_file  # Generated output streamed to this file apart from the command prompt

        self.parser = CoreNLPParser(url=self.corenlp_host)  # Initializing the connection with CoreNLP parse
        self.testParserConnection()

        # Setting up the word2vec model
        corpusFilePath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "tools" + os.path.sep + "word2vec"
        corpusFileName = "GoogleNews-vectors-negative300.bin"
        self.filePath = corpusFilePath  # file path
        self.fileName = corpusFilePath + os.path.sep + corpusFileName  # Constructing the full path for the file name
        self.model = KeyedVectors.load_word2vec_format(self.fileName, binary=True)

        self.stopWords = nltk.corpus.stopwords.words('english')
        self.fileNewLine = "\n"

        self.dbConnector = dbConnector

    def testParserConnection(self):
        str = "This is a test statement"
        try:
            list(self.parser.parse(str.split()))
        except Exception as e:
            print("Error while connecting to CoreNLP server. Exiting.")
            sys.exit()

    def getParseTree(self, sentence):
        return list(self.parser.parse(sentence.split()))

    def displayConstructedParseTree(self, parseTree, fileObj=None):
        for entry in parseTree:
            if fileObj is None:
                entry.pretty_print()
            else:
                entry.pretty_print(stream=fileObj)

    def updatePredictedCategoryForWord(self, entry, category_sum):
        for i in range(len(self.main_categories)):
            try:
                sim_val = self.model.similarity(entry, self.main_categories[i])
                category_sum[self.main_categories[i]] += sim_val
            except KeyError:
                pass
        return category_sum

    def getCategoryWithMaxVoting(self, categoryMap):
        max_val = None
        max_category = None
        for entry in categoryMap:
            val = categoryMap[entry]
            if max_val is None or val > max_val:
                max_val = val
                max_category = entry
        return max_category

    def assignCategory(self, statement):
        # Special case: Statements associated with Geography are misclassified when beginning with "where is"
        if statement.lower().startswith('where is'):
            return 'geography'
        tokens = list(self.parser.tokenize(statement))
        filtered_words = [w for w in tokens if not w in self.stopWords]
        filtered_words_lower = [w.lower() for w in filtered_words]
        category_sum = {}
        for entry in self.main_categories:
            # Exclude the category 'geography' if the words related to 'birth' are present in the sentence
            if (entry != 'geography' and 'capital' not in filtered_words_lower) or (
                    entry == 'geography' and not ('born' in filtered_words_lower or 'birth' in filtered_words_lower)):
                category_sum[entry] = 0
        for entry in filtered_words:
            category_sum = self.updatePredictedCategoryForWord(entry, category_sum)
        return self.getCategoryWithMaxVoting(category_sum)

    # Direct the output to the default output stream and an output file.
    def outputGenerator(self, statement, query, answer, opFileObj=None):
        if opFileObj is not None:
            opFileObj.write("<QUESTION> " + statement)
            opFileObj.write(self.fileNewLine)
            opFileObj.write(self.fileNewLine)
            if query is not None:
                opFileObj.write("<QUERY> " + query)
            else:
                opFileObj.write("<QUERY> ")
            opFileObj.write(self.fileNewLine)
            opFileObj.write(self.fileNewLine)
            opFileObj.write("<ANSWER> " + answer)
            opFileObj.write(self.fileNewLine)
            opFileObj.write(self.fileNewLine)
            opFileObj.write(self.fileNewLine)
        print("<QUESTION> ", statement, "\n")
        if query is not None:
            print("<QUERY> ", query, "\n")
        else:
            print("<QUERY>\n")
        print("<ANSWER> ", answer, "\n\n")

    # Process the parse tree to extract projections and perform translation into SQL queries
    def extractProjections(self, parseTree, queryObj, category):
        # Starts off the entire tree recursion process
        for entry in parseTree:
            # entry.pretty_print()
            self.processRecurse(None, entry, queryObj, category)

    # Recursively traverse the parse tree using DFS and generate transitions for each parent, child node-pair
    def processRecurse(self, parent, treeObj, queryObj, category):
        if type(treeObj) != nltk.tree.Tree:  # leaf node
            transition_obj = transition(parent, treeObj, None, queryObj, category)
            return treeObj, transition_obj
        if "." == treeObj.label() or "DT" == treeObj.label():  # do not handle determiners or punctuation
            return "", None
        str_transition = treeObj.label() + " " + "->"
        current_children = []
        for i in range(len(treeObj)):
            label, transition_obj_inter = self.processRecurse(treeObj.label(), treeObj[i], queryObj, category)
            if transition_obj_inter is not None:
                current_children.append(transition_obj_inter)
                str_transition += " " + label
        if treeObj.label() != 'ROOT':
            transition_obj_fin = transition(parent, str_transition, current_children, queryObj, category)
        else:  # Root of the tree is encountered
            transition_obj_fin = None
        return treeObj.label(), transition_obj_fin

    def parseInputFile(self):  # Parse the statements in the input file sequentially and perform semantic tranformation
        ipFileObj = open(self.ip_file, "r")
        opFileObj = open(self.op_file, "w")
        try:
            for entry in ipFileObj:
                question = entry.strip()
                if not question.startswith('--'):
                    queryObj = queryForm()
                    parseTree = self.getParseTree(question)  # Generate parse tree
                    category = self.assignCategory(question)  # Assign probable category
                    self.extractProjections(parseTree, queryObj,
                                            category)  # Extract the projections and generate the query object
                    # queryObj.printComponents()
                    queryObj.constructQuery()  # Construct the final query
                    results = self.dbConnector.getResults(queryObj,
                                                          category)  # Execute the query in the database and generate results
                    self.outputGenerator(question, queryObj.getQueryStr(), results, opFileObj)
        except Exception as e:
            print("Error while processing.")
            print(e)
        finally:
            ipFileObj.close()
            opFileObj.close()
