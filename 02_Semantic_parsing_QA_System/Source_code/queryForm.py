# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 18:12:36 2019

@author: Sivaraman Lakshmipathy, Yatri Modi
"""

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