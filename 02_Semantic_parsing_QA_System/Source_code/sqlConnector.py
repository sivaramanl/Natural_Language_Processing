# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 18:12:36 2019

@author: Sivaraman Lakshmipathy, Yatri Modi
"""

import os
import sys
import sqlite3

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