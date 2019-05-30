# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 18:12:36 2019

@author: Sivaraman Lakshmipathy, Yatri Modi
"""

from queryForm import queryForm

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