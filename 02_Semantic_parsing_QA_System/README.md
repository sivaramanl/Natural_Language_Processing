README
------

Authors: 
<ul>
  <li>
      Sivaraman Lakshmipathy<br>https://github.com/sivaramanl
  </li>
  <li>
      Yatri Modi<br>https://github.com/yatri96
  </li>
</ul>
<hr>

Readme:
1. The source code is named "semantic_parsing_qa_system.py" and is developed in Python version Python 3.7.1 and hence please ensure the corresponding version is available to execute the source code.
2. The following package dependencies are to be fulfilled in order to execute the code.
    a) Package 'nltk'
    b) Package 'gensim'
    c) Package 'sqlite3'
3. Additionally, the word2vec model utilized in the source code is built using the "GoogleNews-vectors-negative300.bin" pre-trained vectors. 
Please download the same and extract it under "tools/word2vec" directory. 
The same can be downloaded from here: https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit
4. The NLP parser used in the source code is CoreNLP. 
The source code tries to connect to the CoreNLP server running at "http://localhost:9000". 
Please ensure that the CoreNLP server is available at this host URL.
If the connection to CoreNLP fails, the execution will be terminated with an error message.
5. The source code connects to SQLite databases to execute the queries formed from natural language queries.
Please download and extract the database files under "Sqlite.Db" directory.
If a connection cannot be established with the databases, the execution will be terminated with an error message.
6. The execution expects an input file name as a command line parameter. If not provided, the input file name will be treated as "input.txt" by default.
7. On execution, the results will be available in two streams.
    a) Command line output.
    b) Written to "query_output.txt" file in the same directory as the source code.
-------------------
