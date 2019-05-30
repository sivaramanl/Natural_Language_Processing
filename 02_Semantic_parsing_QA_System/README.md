Question Answering System utilizing semantic parsing
----------------------------------------------------

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
Info:
<table>
  <tr>
    <td rowspan="10">Pre requisites:</td>
    <td>Python packages</td>
    <td colspan="2">nltk, gensim, sqlite3</td>
  </tr>
  <tr>
    <td colspan="3"></td>
  </tr>
  <tr>
    <td rowspan="3">Corpus</td>
    <td>Name:</td>
    <td>GoogleNews-vectors-negative300.bin</td>
  </tr>
  <tr>
    <td>Source download link:</td>
    <td>https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM</td>
  </tr>
  <tr>
    <td>Instructions:</td>
    <td>Please download the same and extract it under "tools/word2vec" directory.</td>
  </tr>
  <tr>
    <td colspan="3"></td>
  </tr>
  <tr>
    <td rowspan="4">Parser</td>
    <td>Name:</td>
    <td>CoreNLP</td>
  </tr>
  <tr>
    <td>Source download link:</td>
    <td>https://stanfordnlp.github.io/CoreNLP</td>
  </tr>
  <tr>
    <td>Reference:</td>
    <td>https://github.com/nltk/nltk/wiki/Stanford-CoreNLP-API-in-NLTK</td>
  </tr>
  <tr>
    <td>Instructions:</td>
    <td>
      <ul>
        <li>The source code tries to connect to the CoreNLP server running at "http://localhost:9000".</li>
        <li>Please ensure that the CoreNLP server is available at this host URL.</li>
        <li>If the connection to CoreNLP fails, the execution will be terminated with an error message.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td colspan="4"></td>
  </tr>
  <tr>
    <td rowspan="7">Source code info:</td>
    <td>Python version:</td>
    <td colspan="2">3.7.1</td>
  </tr>
  <tr>
    <td colspan="3"></td>
  </tr>
  <tr>
    <td rowspan="5">Source code files:</td>
    <td><a href="https://github.com/sivaramanl/Natural_Language_Processing/blob/master/02_Semantic_parsing_QA_System/Source_code/sqlConnector.py">sqlConnector.py</a></td>
    <td>Contains the class that performs database operations.</td>
  </tr>
  <tr>
    <td><a href="https://github.com/sivaramanl/Natural_Language_Processing/blob/master/02_Semantic_parsing_QA_System/Source_code/queryForm.py">queryForm.py</a></td>
    <td>Contains the class to hold the query object being constructed for the translation of natural language queries into SQL queries.</td>
  </tr>
  <tr>
    <td><a href="https://github.com/sivaramanl/Natural_Language_Processing/blob/master/02_Semantic_parsing_QA_System/Source_code/transition.py">transition.py</a></td>
    <td>Contains the class to perform translation of parse tree tranisitions into SQL query components.</td>
  </tr>
  <tr>
    <td><a href="https://github.com/sivaramanl/Natural_Language_Processing/blob/master/02_Semantic_parsing_QA_System/Source_code/customParseHandler.py">customParseHandler.py</a></td>
    <td>Contains the class to categorize a natural language query into music/movie/geography and initiate the answering mechanism.</td>
  </tr>
  <tr>
    <td><a href="https://github.com/sivaramanl/Natural_Language_Processing/blob/master/02_Semantic_parsing_QA_System/Source_code/qaSystem.py">qaSystem.py</a></td>
    <td>Contains the wrapper to perform all the operations on the input file and generate the corresponding output file.</td>
  </tr>
  <tr>
    <td colspan="4"></td>
  </tr>
</table>

6. The execution expects an input file name as a command line parameter. If not provided, the input file name will be treated as "input.txt" by default.
7. On execution, the results will be available in two streams.
    a) Command line output.
    b) Written to "query_output.txt" file in the same directory as the source code.
-------------------
