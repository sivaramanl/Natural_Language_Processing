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
import sqlite3

#Class to execute queries and convert resultsets into natural language answers.
class sqlConnector:
    #Default responses
    response_Yes = 'Yes'
    response_No = 'No'

    def __init__(self):
        self.dbPath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "Sqlite.Db"
        self.db_music = 'music.sqlite' #music database
        self.db_movie = 'oscar-movie_imdb.sqlite' #movie database
        self.db_geography = 'WorldGeography.sqlite' #geography database

        self.conn_music = self.getConnection(self.dbPath + os.path.sep + self.db_music, 'music')
        self.conn_movie = self.getConnection(self.dbPath + os.path.sep + self.db_movie, 'movie')
        self.conn_geo = self.getConnection(self.dbPath + os.path.sep + self.db_geography, 'geography')

    def getConnection(self, dbFilePath, dbName):
        #To connect to the databases
        try:
            if not os.path.isfile(dbFilePath):
                print("Unable to find the '" + str(dbName) + "' database. Exiting.")
                sys.exit()
            conn_obj = sqlite3.connect(dbFilePath)
            return conn_obj
        except sqlite3.Error:
            #Terminate the execution if the connection is unsuccesful.
            print("Unable to connect to the '" + str(dbName) + "' database. Please check the availability of the database.\nExiting.")
            sys.exit()

    def endConnection(self):
        #Close the connections to the databases.
        if self.conn_music:
            self.conn_music.close()
        if self.conn_movie:
            self.conn_movie.close()
        if self.conn_geo:
            self.conn_geo.close()

    def getResults(self, queryObj, category):
        #To get the final answer to the question given the query
        #i.e., Yes/No or the proper answer for WH- questions
        queryStmt = queryObj.getQueryStr()
        queryType = queryObj.getQueryType()

        try:
            if queryStmt is None: #No query
                return "I do not know"
            if category == 'movies':
                cursor = self.conn_movie.cursor()
            elif category == 'geography':
                cursor = self.conn_geo.cursor()
            else:
                cursor = self.conn_music.cursor()
            #Query execution
            cursor.execute(queryStmt)

            rows = cursor.fetchall()

            if queryType == queryObj.query_type_yes_no: #Yes/No type: Return yes if there is atleast one row in the resultset
                count = 0
                for row in rows:
                    count += 1
                    break
                if count > 0:
                    return self.response_Yes
                return self.response_No
            else:
                #Wh type: Return the values in the resultset
                responseList = []
                for row in rows:
                    val = row[0]
                    if val not in responseList:
                        responseList.append(val)
                if len(responseList) > 0:
                    responseStr = ''
                    for entry in responseList:
                        responseStr += str(entry) + ', '
                    responseStr = responseStr[0:-2]
                    return responseStr
                else:
                    return "Information not available"
        except Exception as e:
            #print(e)
            return "I do not know"

#This class contains the query object being constructed.
#Once the query object is constructed, it can be converted into a well formed SQL query.
class queryForm:
    #Converting grammar rules to SQL query form
    type_select = 'SELECT'
    type_from = 'FROM'
    type_table = 'TABLE'
    type_where = 'WHERE'
    type_like = 'LIKE'
    type_lambda = 'LAMBDA'
    type_join = 'JOIN'
    type_on = 'ON'
    type_and = 'AND'
    type_query_end = ';'
    default_space = ' '
    query_type_wh = 'Wh'
    query_type_yes_no = 'y_n'

    def __init__(self):
        self.query = None
        self.queryComponents = {}
        self.queryType = None
        self.category = []

    def isEmpty(self):
        #Check if query is empty
        if self.query is None:
            return True
        return False

    def printComponents(self):
        print("Components")
        print(self.queryComponents)

    def buildQuery(self, type, argument, val1, val2=None, op=None, isLambda=False):
        #SELECT component
        if type == self.type_select:
            if type not in self.queryComponents:
                self.queryComponents[type] = argument
            #else:
                #print("SELECT already defined! Error! Ignoring current transformation.")
        #TABLE component: Contains the list of tables involved in the query
        elif type == self.type_table:
            if type not in self.queryComponents:
                self.queryComponents[type] = []
            if argument == 'NAME':
                if val1 not in self.queryComponents[type]:
                    self.queryComponents[type].append(val1)
        #WHERE component: Each where component is a dict containing the column, value, operator and if lambda substitution is required
        elif type == self.type_where:
            if type not in self.queryComponents:
                self.queryComponents[type] = []
            self.queryComponents[type].append({
                'column': argument,
                'val': val1,
                'eql': op,
                'isLambda': isLambda
            })
        #DELETE component: to delete any entries from the different components
        elif type == 'DELETE':
            if argument in self.queryComponents:
                arg = self.queryComponents[argument]
                l = len(arg)
                if val1 > 0 and val1-1 < l:
                    del self.queryComponents[argument][val1-1]
                elif val1 < 0:
                    val1 = -val1
                    if val1-1 < l:
                        del self.queryComponents[argument][l-val1]
        #LAMDBA component: contains all the constants to be utilized for lambda substitution
        elif type == self.type_lambda:
            if type not in self.queryComponents:
                self.queryComponents[type] = []
            if val1.lower() not in self.queryComponents[type]:
                self.queryComponents[type].append(val1.lower())
        #JOIN: Contains the list of joins to be constructed. The dict contains the two tables, the join type and the operator to be used for join
        elif type == self.type_join:
            if type not in self.queryComponents:
                self.queryComponents[type] = []
            if op == 'EQUALS':
                op = '='
            self.queryComponents[type].append({
                't1': val1,
                't2': val2,
                'join': argument,
                'op': op
            })

    #To construct the query from the query object
    def constructQuery(self):
        if self.type_select not in self.queryComponents or self.type_table not in self.queryComponents:
            #print("Query hasn't been constructed.")
            return None
        #Constructing actual SQL query string to be used to database
        queryStr = 'SELECT' + self.default_space
        queryStr += self.queryComponents[self.type_select]
        queryStr += self.default_space + 'FROM'
        tables = self.queryComponents[self.type_table]
        aliasMap = {} #Alias names are constructed for tables and utilized in the query
        itrVal = 1
        joinList = []
        try:
            #Single table and hence no join is necessary
            if len(tables) == 1:
                #Table Alias needed for inner join components of SQL query
                tableAlias = 'T' + str(itrVal)
                itrVal += 1
                aliasMap[tables[0]] = tableAlias
                queryStr += self.default_space + tables[0] + self.default_space + tableAlias
            else:
                joinVals = self.queryComponents[self.type_join].copy()
                parseCounter = 0
                while len(joinVals) > 0 and parseCounter < 3:
                    i = -1
                    processed_entries_indx = []
                    for entry in joinVals:
                        i += 1
                        t1 = entry['t1'].split('|')
                        table1 = t1[0].upper()
                        column1 = t1[1].upper()
                        t2 = entry['t2'].split('|')
                        table2 = t2[0].upper()
                        column2 = t2[1].upper()
                        join_type = entry['join'].upper()
                        operator = entry['op']

                        if len(joinList) == 0:
                            tableAlias1 = 'T' + str(itrVal)
                            itrVal += 1
                            joinList.append(table1)
                            aliasMap[table1] = tableAlias1
                            queryStr += self.default_space + table1 + self.default_space + tableAlias1
                            queryStr += self.default_space + join_type
                            tableAlias2 = 'T' + str(itrVal)
                            itrVal += 1
                            joinList.append(table2)
                            aliasMap[table2] = tableAlias2
                            queryStr += self.default_space + table2 + self.default_space + tableAlias2
                            queryStr += self.default_space + self.type_on
                            queryStr += self.default_space + tableAlias1 + "." + column1
                            queryStr += self.default_space + operator
                            queryStr += self.default_space + tableAlias2 + "." + column2
                        elif not (table1 in joinList and table2 in joinList):
                            if table1 in joinList or table2 in joinList:
                                if table1 in joinList:
                                    table2, table1 = table1, table2
                                    column2, column1 = column1, column2
                                elif table2 in joinList:
                                    pass
                                elif table2 not in joinList:
                                    table1, table2 = table2, table1
                                    column1, column2 = column2, column1
                                queryStr += self.default_space + join_type
                                tableAlias = 'T' + str(itrVal)
                                itrVal += 1
                                joinList.append(table1)
                                aliasMap[table1] = tableAlias
                                queryStr += self.default_space + table1 + self.default_space + tableAlias
                                queryStr += self.default_space + self.type_on
                                queryStr += self.default_space + tableAlias + "." + column1
                                queryStr += self.default_space + operator
                                queryStr += self.default_space + aliasMap[table2] + "." + column2
                        processed_entries_indx.append(i)
                    processed_entries_indx.sort(reverse=True)
                    for entry in processed_entries_indx:
                        del joinVals[entry]
                    parseCounter += 1
            if self.type_where in self.queryComponents: #Construct the where component of the query using the alias names and lamdba substitutions
                whereComp = self.queryComponents[self.type_where]
                if self.type_lambda in self.queryComponents:
                    lambdaVals = self.queryComponents[self.type_lambda]
                else:
                    lambdaVals = []
                if len(whereComp) > 0:
                    queryStr += self.default_space + self.type_where
                    whereClauseAppend = self.type_and
                    firstEntry = True
                    for entry in whereComp:
                        tableCol = entry['column'].split('.')
                        val = entry['val']
                        equalizer = entry['eql']
                        isLambda = entry['isLambda']

                        tableName = tableCol[0]
                        columnName = tableCol[1]
                        if tableName in aliasMap:
                            tableName = aliasMap[tableName]
                        if isLambda:
                            if len(lambdaVals) > 0:
                                val = lambdaVals[0]
                                del lambdaVals[0]
                            # else:
                            #     print("Expected substitution value but unavailable. Ignoring here... Check final query before execution.")
                        if val is not None and '' != val.strip():
                            if not firstEntry:
                                queryStr += self.default_space + whereClauseAppend
                            else:
                                firstEntry = False
                            queryStr += self.default_space + tableName + "." + columnName
                            queryStr += self.default_space + equalizer
                            if equalizer == self.type_like:
                                queryStr += self.default_space + '\'%' + val + '%\'' #Wildcard characters introduction
                            else:
                                queryStr += self.default_space + val
            queryStr += self.type_query_end

            #transform table names in select clause to alias names
            toTransform = queryStr[queryStr.index('SELECT') + len('SELECT'):queryStr.index('FROM')].strip()
            remQueryStr = queryStr[queryStr.index('FROM'):].strip()

            fromClause = ''
            #Transform the select clause if it is not equivalent to '*'
            if '*' != toTransform:
                tableCol = toTransform.split('.')
                tableName = tableCol[0]
                columnName = tableCol[1]
                if tableName in aliasMap:
                    tableName = aliasMap[tableName]
                fromClause = tableName + "." + columnName
            else:
                fromClause = toTransform
            queryStr = 'SELECT' + self.default_space
            queryStr += fromClause
            queryStr += self.default_space + remQueryStr

            self.queryStr = queryStr
        except Exception as e:
            #Error in query construction
            self.queryStr = None


    #Method to update the list of lambda values
    def updateLambda(self, oldVal, newVal, updateType):
        if oldVal in self.queryComponents[self.type_lambda]:
            indx = self.queryComponents[self.type_lambda].index(oldVal)
            if updateType == 'APPEND':
                self.queryComponents[self.type_lambda][indx] = oldVal + newVal
            elif updateType == 'REMOVE':
                del self.queryComponents[self.type_lambda][indx]

    def getQueryStr(self):
        try:
            return self.queryStr
        except:
            return None

    def setQueryTypeWh(self):
        if self.queryType is None:
            self.queryType = self.query_type_wh

    def setQueryTypeYN(self):
        if self.queryType is None:
            self.queryType = self.query_type_yes_no

    def getQueryType(self):
        return self.queryType

#Class to hold the individual transitions encountered while parsing the parse tree and convert them to SQL query components using semantic attachments
class transition:
    type_const = 'const'
    type_transform = 'transform'

    def __init__(self, parent, str, children, queryObj, category):
        #Note: Each transition is split into lhs and rhs
        #For example, S -> NP VP is converted into LHS = S, RHS = NP VP
        self.table = None
        self.children = children
        #self.printChildren()
        self.transition = str.strip()
        splits = str.split("->")
        splits = [x.strip() for x in splits]
        self.setLHS(splits[0])
        if children is None:
            self.setVal(self.getLHS())
            self.setType(self.type_const)
            self.transform(parent, children, queryObj, category)
        else:
            self.setType(self.type_transform)
            self.setRHS(splits[1])
            self.transform(parent, children, queryObj, category)

    def printChildren(self):
        print("Enumerating children")
        if self.children is None:
            print("None")
            return
        for entry in self.children:
            print(entry.getVal())

    def setLHS(self, lhs):
        self.lhs = lhs

    def setRHS(self, rhs):
        self.rhs = rhs

    def getLHS(self):
        return self.lhs

    def getRHS(self):
        return self.rhs

    def getVal(self):
        try:
            return self.val.lower()
        except:
            return None

    def getType(self):
        return self.type

    def setVal(self, val):
        #print("Setting val to ", val)
        self.val = val

    def setType(self, type):
        self.type = type

    def transform(self, parent, children, queryObj, category):
        if children is None:
            return
        if category == 'movies':
            self.transform_movie(parent, children, queryObj)
        elif category == 'geography':
            self.transform_geo(parent, children, queryObj)
        else:
            self.transform_music(parent, children, queryObj)

    #Get concatenated leaf values for embedded node processing
    def getLeafValues(self, node, val = ''):
        for entry in node:
            children = entry.children
            if children is None:
                currentVal = entry.getVal()
                if currentVal is not None:
                    val += ' ' + entry.getVal()
            else:
                val += ' ' + self.getLeafValues(children)
        val = val.strip()
        return val

    def transform_music(self, parent, children, queryObj):
        #Recursive parsing of embedded subtrees
        if self.lhs == 'S' and parent != 'ROOT':
            queryObj.buildQuery('LAMBDA', None, self.getLeafValues(children))
        #Converting music category grammar transitions to SQL query form by mapping
        #Construct SQL query components based on LHS -> RHS transitions
        if self.lhs.startswith('W'):
            queryObj.setQueryTypeWh()
            if self.lhs == 'WP' or self.lhs.startswith('WD') or self.lhs.startswith('WR'):
                if self.lhs == 'WP':
                    queryObj.category.append('who')
                    if queryObj.isEmpty():
                        queryObj.buildQuery('TABLE', 'NAME', 'ARTIST')
                        queryObj.buildQuery('SELECT', 'ARTIST.NAME', None)
                elif self.lhs == 'WDT':
                    queryObj.category.append('which')
                elif self.lhs == 'WRB':
                    queryObj.category.append('when')
        elif self.lhs == 'SQ' and self.rhs.startswith('VB'):
            queryObj.setQueryTypeYN()
            if queryObj.isEmpty() and queryObj.queryType != queryForm.query_type_wh:
                queryObj.buildQuery('SELECT', '*', None)
        elif self.lhs == 'VP' and self.rhs.startswith('VB') and self.rhs.endswith('SBAR'):
            queryObj.setQueryTypeYN()
            if queryObj.isEmpty() and queryObj.queryType != queryForm.query_type_wh:
                queryObj.buildQuery('SELECT', '*', None)
        elif self.rhs.lower() == 'does':
            if queryObj.isEmpty() and queryObj.queryType != queryForm.query_type_wh:
                queryObj.setQueryTypeYN()
                queryObj.buildQuery('SELECT', '*', None)
        elif self.lhs.startswith('NNP'):
            if len(children) == 1 and children[0].getType() == self.type_const:
                queryObj.buildQuery('LAMBDA', None, self.getChildVal(children))
        elif self.lhs in ['NNP', 'NNPS', 'NN', 'CD', 'POS', 'NP']:
            self.setVal(self.getChildVal(children))
            if self.rhs == 'CD':
                #Add query for year
                queryObj.buildQuery('WHERE', 'ARTIST.DATEOFBIRTH', str(self.getChildVal(children)), None, 'LIKE', False)
                queryObj.category.append('year_added')
            elif self.lhs == 'NP':
                if self.rhs.endswith('NN NN'):
                    queryObj.buildQuery('LAMBDA', None, self.children[len(self.children)-1].getVal())
        elif 'PP' == self.lhs: #handle prepositions
            if self.rhs == 'IN NP':
                if 'year_added' not in queryObj.category:
                    cur_val = self.children[1].getVal()
                    if cur_val is not None:
                        queryObj.buildQuery('LAMBDA', None, cur_val)
                    if 'born' in queryObj.category:
                        queryObj.buildQuery('WHERE', 'ARTIST.PLACEOFBITH', '', None, 'LIKE', True)

        if self.lhs == 'NN':
            if (self.rhs == 'NNP POS' or self.rhs == 'NNPS') and self.children[1].getVal() != '\'':
                nnp_val = self.children[0].getVal()
                queryObj.updateLambda(nnp_val, ('\'' + self.children[1].getVal()), 'APPEND')
            elif self.rhs == 'album':
                queryObj.category.append('album')
            elif self.rhs == 'track':
                queryObj.category.append('track')
        elif self.lhs.startswith('VB'):
            if self.rhs == 'born':
                queryObj.buildQuery('TABLE', 'NAME', 'ARTIST')
                queryObj.buildQuery('WHERE', 'ARTIST.NAME', '', None, 'LIKE', True)
                queryObj.category.append('born')
                if 'when' in queryObj.category:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('TABLE', 'NAME', 'ARTIST')
                        queryObj.buildQuery('SELECT', 'ARTIST.DATEOFBIRTH', None)
            elif self.rhs in ['sing', 'sang']:
                queryObj.buildQuery('TABLE', 'NAME', 'ARTIST')
                queryObj.buildQuery('TABLE', 'NAME', 'ALBUM')
                queryObj.buildQuery('TABLE', 'NAME', 'TRACK')
                self.getJoin(queryObj, 'TRACK', 'ALBUM')
                self.getJoin(queryObj, 'ALBUM', 'ARTIST')
                if queryObj.queryType != queryForm.query_type_wh:
                    queryObj.buildQuery('WHERE', 'ARTIST.NAME', '', None, 'LIKE', True)
                else:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('SELECT', 'ARTIST.NAME', None)
                queryObj.buildQuery('WHERE', 'TRACK.NAME', '', None, 'LIKE', True)
            elif self.rhs == 'include':
                queryObj.buildQuery('TABLE', 'NAME', 'ALBUM')
                queryObj.buildQuery('TABLE', 'NAME', 'TRACK')
                self.getJoin(queryObj, 'TRACK', 'ALBUM')
                if queryObj.queryType != queryForm.query_type_wh:
                    queryObj.buildQuery('WHERE', 'ALBUM.NAME', '', None, 'LIKE', True)
                else:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('SELECT', 'ALBUM.NAME', None)
                queryObj.buildQuery('WHERE', 'TRACK.NAME', '', None, 'LIKE', True)

        return

    def transform_geo(self, parent, children, queryObj):
        #Constructs SQL query components based on transitions rather than the leaves
        if self.lhs.startswith('W'):
            queryObj.setQueryTypeWh()
        elif self.lhs == 'SQ' and self.rhs.startswith('VB'):
            queryObj.setQueryTypeYN()
            if queryObj.isEmpty() and queryObj.queryType != queryForm.query_type_wh:
                queryObj.buildQuery('SELECT', '*', None)

        if self.lhs.startswith('NNP'):
            if len(children) == 1 and children[0].getType() == self.type_const:
                queryObj.buildQuery('LAMBDA', None, self.getChildVal(children))
        elif self.lhs in ['NNP', 'NNPS', 'NN', 'CD', 'POS']:
            self.setVal(self.getChildVal(children))

        if self.lhs == 'WRB' or (self.lhs == 'NN' and self.rhs.lower().startswith('capital')):
            queryObj.buildQuery('TABLE', 'NAME', 'CAPITALS')
            queryObj.buildQuery('TABLE', 'NAME', 'COUNTRIES')
            queryObj.buildQuery('TABLE', 'NAME', 'CITIES')
            self.getJoin(queryObj, 'CAPITALS', 'COUNTRIES')
            self.getJoin(queryObj, 'CAPITALS', 'CITIES')
            if queryObj.queryType != queryForm.query_type_wh:
                queryObj.buildQuery('WHERE', 'CITIES.NAME', '', None, 'LIKE', True)
                queryObj.buildQuery('WHERE', 'COUNTRIES.NAME', '', None, 'LIKE', True)
            else:
                if self.lhs == 'WRB':
                    if queryObj.isEmpty():
                        queryObj.buildQuery('SELECT', 'COUNTRIES.NAME', None)
                        queryObj.buildQuery('WHERE', 'CITIES.NAME', '', None, 'LIKE', True)
                else:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('SELECT', 'CITIES.NAME', None)
                        queryObj.buildQuery('WHERE', 'COUNTRIES.NAME', '', None, 'LIKE', True)

        if self.lhs == 'SQ' and self.rhs.endswith('NP ADVP NP'):
            queryObj.buildQuery('TABLE', 'NAME', 'COUNTRYCONTINENTS')
            queryObj.buildQuery('TABLE', 'NAME', 'COUNTRIES')
            queryObj.buildQuery('TABLE', 'NAME', 'CONTINENTS')
            self.getJoin(queryObj, 'COUNTRYCONTINENTS', 'COUNTRIES')
            self.getJoin(queryObj, 'COUNTRYCONTINENTS', 'CONTINENTS')
            queryObj.buildQuery('WHERE', 'COUNTRIES.NAME', '', None, 'LIKE', True)
            queryObj.buildQuery('WHERE', 'CONTINENTS.CONTINENT', '', None, 'LIKE', True)

    def transform_movie(self, parent, children, queryObj):
        #Recursive parsing of embedded subtrees
        if self.lhs == 'S' and parent != 'ROOT' and self.rhs.startswith('S'):
            queryObj.buildQuery('LAMBDA', None, self.getLeafValues(children))
        #Checks according to the verbs in the questions i.e. the leaves of the parse trees
        if ('NN' == self.lhs and self.rhs == 'director') or (self.lhs.startswith('V') and self.rhs.startswith('direct')):
            queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
            queryObj.buildQuery('TABLE', 'NAME', 'DIRECTOR')
            if 'best' not in queryObj.category:
                self.getJoin(queryObj, 'PERSON', 'DIRECTOR')
            if self.lhs.startswith('N'):
                queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                queryObj.category.append('Movie')
                if 'best' in queryObj.category:
                    queryObj.buildQuery('WHERE', 'OSCAR.TYPE', 'best-director', None, 'LIKE', False)
                    if 'which' in queryObj.category:
                        if queryObj.isEmpty():
                            queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                            queryObj.buildQuery('SELECT', 'PERSON.NAME', None)
            elif self.lhs.startswith('V'):
                queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
                self.getJoin(queryObj, 'MOVIE', 'DIRECTOR')
                if 'best' not in queryObj.category:
                    queryObj.buildQuery('WHERE', 'MOVIE.NAME', '', None, 'LIKE', True)
            if 'which' in queryObj.category:
                if queryObj.isEmpty():
                    queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                    queryObj.buildQuery('SELECT', 'PERSON.NAME', None)
                self.getJoin(queryObj, 'OSCAR', 'PERSON')
        elif 'NN' == self.lhs and self.rhs.startswith('act'):
            queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
            queryObj.buildQuery('TABLE', 'NAME', 'ACTOR')
            if self.lhs.startswith('N'):
                queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
            if 'best' not in queryObj.category:
                self.getJoin(queryObj, 'PERSON', 'ACTOR')
            if 'best' in queryObj.category or 'who' in queryObj.category or 'which' in queryObj.category:
                if 'support' in queryObj.category:
                    queryObj.buildQuery('WHERE', 'OSCAR.TYPE', 'best-supporting-' + self.rhs, None, 'LIKE', False)
                else:
                    queryObj.buildQuery('WHERE', 'OSCAR.TYPE', 'best-' + self.rhs, None, 'LIKE', False)
            if 'which' in queryObj.category:
                if queryObj.isEmpty():
                    queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                    queryObj.buildQuery('SELECT', 'PERSON.NAME', None)
        elif 'NN' == self.lhs and (self.rhs.startswith('movie') or self.rhs.startswith('film') or self.rhs.startswith('picture')):
            queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
            queryObj.buildQuery('TABLE', 'NAME', 'OSCAR')
            self.table = 'MOVIE'
            queryObj.category.append('Movie')
            if 'best' in queryObj.category:
                queryObj.buildQuery('WHERE', 'OSCAR.TYPE', 'best-picture', None, 'LIKE', False)
            if 'prep' not in queryObj.category:
                queryObj.buildQuery('WHERE', 'MOVIE.NAME', '', None, 'LIKE', True)
            if 'which' in queryObj.category:
                if queryObj.isEmpty():
                    queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
                    queryObj.buildQuery('SELECT', 'MOVIE.NAME', None)
                    self.getJoin(queryObj, 'MOVIE', 'OSCAR')
                queryObj.buildQuery('WHERE', 'OSCAR.TYPE', 'best-picture', None, 'LIKE', False)
        elif self.lhs.startswith('NNP'):
            if len(children) == 1 and children[0].getType() == self.type_const:
                queryObj.buildQuery('LAMBDA', None, self.getChildVal(children))
        elif 'IN' == self.lhs: #handle prepositions
            if 'with' == self.rhs.lower():
                queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                self.getJoin(queryObj, 'MOVIE', 'ACTOR')
                self.getJoin(queryObj, 'PERSON', 'ACTOR')
        elif 'PP' == self.lhs: #handle prepositions
            if self.rhs == 'IN NP':
                if 'year_added' not in queryObj.category:
                    cur_val = self.children[1].getVal()
                    if cur_val is not None:
                        queryObj.buildQuery('LAMBDA', None, cur_val)
                    if 'born' in queryObj.category:
                        queryObj.buildQuery('WHERE', 'PERSON.POB', '', None, 'LIKE', True)
                if 'year_added' not in queryObj.category and queryObj.queryType == queryForm.query_type_wh:
                    self.getJoin(queryObj, 'OSCAR', 'PERSON')
        elif self.lhs == 'VP' and self.rhs == 'VBD NP PP' and 'which' not in queryObj.category:
            queryObj.buildQuery('DELETE', 'WHERE', -2)
        #semantic transformation based on specific verbs
        elif self.lhs.startswith('VB'):
            if self.rhs == 'born':
                queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                queryObj.category.append('born')
                if 'when' in queryObj.category:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                        queryObj.buildQuery('SELECT', 'PERSON.DOB', None)
            elif self.rhs in ['win', 'won']:
                queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
                queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                queryObj.buildQuery('TABLE', 'NAME', 'OSCAR')
                queryObj.category.append('win')
                if 'Movie' not in queryObj.category:
                    self.getJoin(queryObj, 'OSCAR', 'PERSON')
                if 'when' in queryObj.category:
                    if queryObj.isEmpty():
                        queryObj.buildQuery('TABLE', 'NAME', 'OSCAR')
                        queryObj.buildQuery('SELECT', 'OSCAR.YEAR', None)
                    queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
            elif self.rhs.startswith('support'):
                queryObj.category.append('support')
            elif self.rhs.lower() == 'star':
                queryObj.buildQuery('TABLE', 'NAME', 'ACTOR')
                queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
                queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                self.getJoin(queryObj, 'MOVIE', 'ACTOR')
                self.getJoin(queryObj, 'PERSON', 'ACTOR')
                if 'adj' not in queryObj.category:
                    queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                queryObj.buildQuery('WHERE', 'MOVIE.NAME', '', None, 'LIKE', True)

        #Construct SQL query components based on LHS -> RHS transitions
        if self.lhs.startswith('W'):
            queryObj.setQueryTypeWh()
            if self.lhs == 'WP' or self.lhs.startswith('WD') or self.lhs.startswith('WR'):
                if self.lhs == 'WP':
                    queryObj.category.append('who')
                    if queryObj.isEmpty():
                        queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                        queryObj.buildQuery('SELECT', 'PERSON.NAME', None)
                elif self.lhs == 'WDT':
                    queryObj.category.append('which')
                elif self.lhs == 'WRB':
                    queryObj.category.append('when')
        elif self.lhs == 'SQ' and self.rhs.startswith('VB'):
            queryObj.setQueryTypeYN()
            if queryObj.isEmpty():
                queryObj.buildQuery('SELECT', '*', None)
                if 'WHERE' not in queryObj.queryComponents and queryForm.type_lambda in queryObj.queryComponents:
                    queryObj.queryComponents[queryForm.type_lambda].reverse()
                    queryObj.buildQuery('TABLE', 'NAME', 'DIRECTOR')
                    queryObj.buildQuery('TABLE', 'NAME', 'MOVIE')
                    queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                    self.getJoin(queryObj, 'MOVIE', 'DIRECTOR')
                    self.getJoin(queryObj, 'PERSON', 'DIRECTOR')
                    queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                    queryObj.buildQuery('WHERE', 'MOVIE.NAME', '', None, 'LIKE', True)
        elif self.lhs == 'S' and self.rhs.startswith('VP'):
            queryObj.setQueryTypeYN()
            if queryObj.isEmpty():
                queryObj.buildQuery('SELECT', '*', None)
        #Handle adjectives
        if self.lhs.startswith('JJ'):
            queryObj.category.append('adj')
            if self.rhs == 'best':
                queryObj.buildQuery('TABLE', 'NAME', 'OSCAR')
                self.table = 'OSCAR'
                queryObj.category.append('best')

            #Handle adjectives based on nationality
            elif self.rhs in ['American', 'Italian', 'French', 'British', 'German']:
                queryObj.buildQuery('TABLE', 'NAME', 'PERSON')
                if self.rhs == 'American':
                    queryVal = 'USA'
                elif self.rhs == 'Italian':
                    queryVal = 'Italy'
                elif self.rhs == 'French':
                    queryVal = 'France'
                elif self.rhs == 'British':
                    queryVal = 'UK'
                elif self.rhs == 'German':
                    queryVal = 'Germany'
                else:
                    queryVal = self.rhs
                queryObj.buildQuery('WHERE', 'PERSON.POB', queryVal, None, 'LIKE', False)

        #Handle constants such as proper nouns and numbers
        if self.lhs in ['NNP', 'NNPS', 'NN', 'CD', 'POS']:
            self.setVal(self.getChildVal(children))
        elif self.lhs == 'NP':
            if self.rhs in ['NNP', 'NN', 'CD', 'NNPS']:
                self.setVal(self.getChildVal(children))
                if self.rhs == 'CD':
                    #Add query for year
                    if 'Movie' in queryObj.category or 'Wh' in queryObj.category and 'born' not in queryObj.category or 'win' in queryObj.category:
                        queryObj.buildQuery('WHERE', 'OSCAR.YEAR', str(self.getChildVal(children)), None, '=', False)
                    else:
                        queryObj.buildQuery('WHERE', 'PERSON.DOB', str(self.getChildVal(children)), None, 'LIKE', False)
                    if 'win' in queryObj.category and queryObj.queryType != queryForm.query_type_wh:
                        queryObj.buildQuery('WHERE', 'PERSON.NAME', '', None, 'LIKE', True)
                    queryObj.category.append('year_added')
            elif (self.rhs == 'NNP POS' or self.rhs == 'NNPS') and self.children[1].getVal() != '\'':
                nnp_val = self.children[0].getVal()
                queryObj.updateLambda(nnp_val, ('\'' + self.children[1].getVal()), 'APPEND')
            else:
                if self.rhs == 'JJS NN':
                    self.getJoin(queryObj, self.children[0].table, self.children[1].table)

        if self.lhs.startswith('WH'):
            queryObj.setQueryTypeWh()
            queryObj.category.append('Wh')

    #Method to generate the joins for all the combinations of tables utilized in constructing the queries.
    def getJoin(self, queryObj, table1, table2):
        #Movies database
        if (table1, table2) == ('PERSON', 'DIRECTOR') or (table2, table1) == ('PERSON', 'DIRECTOR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'PERSON|ID', 'DIRECTOR|DIRECTOR_ID', 'EQUALS')
        elif (table1, table2) == ('MOVIE', 'OSCAR') or (table2, table1) == ('MOVIE', 'OSCAR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'MOVIE|ID', 'OSCAR|MOVIE_ID', 'EQUALS')
        elif (table1, table2) == ('PERSON', 'ACTOR') or (table2, table1) == ('PERSON', 'ACTOR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'PERSON|ID', 'ACTOR|ACTOR_ID', 'EQUALS')
        elif (table1, table2) == ('MOVIE', 'ACTOR') or (table2, table1) == ('MOVIE', 'ACTOR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'MOVIE|ID', 'ACTOR|MOVIE_ID', 'EQUALS')
        elif (table1, table2) == ('MOVIE', 'DIRECTOR') or (table2, table1) == ('MOVIE', 'DIRECTOR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'MOVIE|ID', 'DIRECTOR|MOVIE_ID', 'EQUALS')
        elif (table1, table2) == ('PERSON', 'OSCAR') or (table2, table1) == ('PERSON', 'OSCAR'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'PERSON|ID', 'OSCAR|PERSON_ID', 'EQUALS')

        #Geography database
        elif(table1, table2) == ('CAPITALS', 'COUNTRIES') or (table2, table1) == ('CAPITALS', 'COUNTRIES'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'CAPITALS|COUNTRYID', 'COUNTRIES|ID', 'EQUALS')
        elif (table1, table2) == ('CAPITALS', 'CITIES') or (table2, table1) == ('CAPITALS', 'CITIES'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'CAPITALS|CITYID', 'CITIES|ID', 'EQUALS')
        elif (table1, table2) == ('COUNTRYCONTINENTS', 'COUNTRIES') or (table2, table1) == ('COUNTRYCONTINENTS', 'COUNTRIES'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'COUNTRYCONTINENTS|COUNTRYID', 'COUNTRIES|ID', 'EQUALS')
        elif (table1, table2) == ('COUNTRYCONTINENTS', 'CONTINENTS') or (table2, table1) == ('COUNTRYCONTINENTS', 'CONTINENTS'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'COUNTRYCONTINENTS|CONTINENTID', 'CONTINENTS|ID', 'EQUALS')

        #Music database
        elif (table1, table2) == ('TRACK', 'ALBUM') or (table2, table1) == ('TRACK', 'ALBUM'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'TRACK|ALBUMID', 'ALBUM|ALBUMID', 'EQUALS')
        elif (table1, table2) == ('ARTIST', 'ALBUM') or (table2, table1) == ('ARTIST', 'ALBUM'):
            queryObj.buildQuery('JOIN', 'INNER JOIN', 'ARTIST|ID', 'ALBUM|ARTSITID', 'EQUALS')

        else:
            return None


    def getChildVal(self, child):
        if child is None:
            return None
        else:
            return child[0].getVal()

class custom_parse_handler:
    corenlp_host = 'http://localhost:9000' #CoreNLP server host
    main_categories = ['geography', 'music', 'movies'] #Categories utilized in the project
    
    def __init__(self, input_file, output_file, dbConnector):
        self.ip_file = input_file #Input statements
        self.op_file = output_file #Generated output streamed to this file apart from the command prompt

        self.parser = CoreNLPParser(url=self.corenlp_host) #Initializing the connection with CoreNLP parse
        self.testParserConnection()

        #Setting up the word2vec model
        corpusFilePath = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "tools" + os.path.sep + "word2vec"
        corpusFileName = "GoogleNews-vectors-negative300.bin"
        self.filePath = corpusFilePath  #file path
        self.fileName = corpusFilePath + os.path.sep + corpusFileName  #Constructing the full path for the file name
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
    
    def displayConstructedParseTree(self, parseTree, fileObj = None):
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
        #Special case: Statements associated with Geography are misclassified when beginning with "where is"
        if statement.lower().startswith('where is'):
            return 'geography'
        tokens = list(self.parser.tokenize(statement))
        filtered_words = [w for w in tokens if not w in self.stopWords]
        filtered_words_lower = [w.lower() for w in filtered_words]
        category_sum = {}
        for entry in self.main_categories:
            #Exclude the category 'geography' if the words related to 'birth' are present in the sentence
            if (entry != 'geography' and 'capital' not in filtered_words_lower) or (entry == 'geography' and not ('born' in filtered_words_lower or 'birth' in filtered_words_lower)):
                category_sum[entry] = 0
        for entry in filtered_words:
            category_sum = self.updatePredictedCategoryForWord(entry, category_sum)
        return self.getCategoryWithMaxVoting(category_sum)

    #Direct the output to the default output stream and an output file.
    def outputGenerator(self, statement, query, answer, opFileObj = None):
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

    #Process the parse tree to extract projections and perform translation into SQL queries
    def extractProjections(self, parseTree, queryObj, category):
        #Starts off the entire tree recursion process
        for entry in parseTree:
            #entry.pretty_print()
            self.processRecurse(None, entry, queryObj, category)

    #Recursively traverse the parse tree using DFS and generate transitions for each parent, child node-pair
    def processRecurse(self, parent, treeObj, queryObj, category):
        if type(treeObj) != nltk.tree.Tree: #leaf node
            transition_obj = transition(parent, treeObj, None, queryObj, category)
            return treeObj, transition_obj
        if "." == treeObj.label() or "DT" == treeObj.label(): #do not handle determiners or punctuation
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
        else: #Root of the tree is encountered
            transition_obj_fin = None
        return treeObj.label(), transition_obj_fin
        
    def parseInputFile(self): #Parse the statements in the input file sequentially and perform semantic tranformation
        ipFileObj = open(self.ip_file, "r")
        opFileObj = open(self.op_file, "w")
        try:
            for entry in ipFileObj:
                question = entry.strip()
                if not question.startswith('--'):
                    queryObj = queryForm()
                    parseTree = self.getParseTree(question) #Generate parse tree
                    category = self.assignCategory(question) #Assign probable category
                    self.extractProjections(parseTree, queryObj, category) #Extract the projections and generate the query object
                    #queryObj.printComponents()
                    queryObj.constructQuery() #Construct the final query
                    results = self.dbConnector.getResults(queryObj, category) #Execute the query in the database and generate results
                    self.outputGenerator(question, queryObj.getQueryStr(), results, opFileObj)
        except Exception as e:
            print("Error while processing.")
        finally:
            ipFileObj.close()
            opFileObj.close()

def assignInputFileName(ipFileName):
    try:
        open(ipFileName, "r")
    except Exception:
        ipFileName = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + ipFileName
    finally:
        return ipFileName

def main():
    input_file = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "input.txt"
    if len(sys.argv) > 1:
        input_file = assignInputFileName(sys.argv[1])
    output_file = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "query_output.txt"
    dbConnector = sqlConnector()
    try:
        parse_obj = custom_parse_handler(input_file, output_file, dbConnector)
        parse_obj.parseInputFile()
    except Exception as e:
         #handle error
         print(e)
    finally:
        dbConnector.endConnection()

if __name__ == '__main__':
    main()