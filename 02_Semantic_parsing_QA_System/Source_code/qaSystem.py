# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 18:12:36 2019

@author: Sivaraman Lakshmipathy, Yatri Modi
"""

import os
import sys

from sqlConnector import sqlConnector
from customParseHandler import custom_parse_handler

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