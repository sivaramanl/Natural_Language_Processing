README
------
<b>HMM Probability calculator</b>
<br><br>
Info:
<table>
  <tr>
    <td rowspan="2">Source code info:</td>
    <td>Python version:</td>
    <td>3.7.1</td>
  </tr>
  <tr>
    <td>Source code file:</td>
    <td>hmm_probability_calculator.py</td>
  </tr>
  <tr>
    <td colspan="3"></td>
  </tr>
  <tr>
    <td rowspan="2">Input files:</td>
    <td>POS_corpus.txt</td>
    <td>POS tagged corpus obtained using Stanford POS tagger.<br>
        Note: The POS tagged corpus can be obtained using Stanford POS tagger.</td>
  </tr>
  <tr>
    <td>testset.txt</td>
    <td>Test sentence to tag and find maximum probable tagging sequence.</td>
  </tr>
  <tr>
    <td colspan="3"></td>
  </tr>
  <tr>
    <td rowspan="3">Output files:</td>
    <td>lexical_prob.txt</td>
    <td>Contains the P(wi|ti) for all unique words in the input corpus.</td>
  </tr>
  <tr>
    <td>transition_prob.txt</td>
    <td>Contains all the tag transition probabilities for all possible tag transitions in the input corpus.</td>
  </tr>
  <tr>
    <td>testset_output.txt</td>
    <td>Contains all possible tagging combinations for the given test sentence based on the input corpus and the most probable tagging sequence based on the probility calculation.</td>
  </tr>
</table>
<br>
<b>Source code execution:</b>
<br>
Run the source code file using Python.
<br>
>> python hmm_probability_calculator.py
<br><br>
<b>Notes:</b>
<ol>
  <li>The tagged corpus in POS_corpus.txt will be utilized to tag the 'first' line in testset.txt</li>
  <li>The results will be displayed in the command prompt while detailed results will be written to lexical_prob.txt, transition_prob.txt and testset_output.txt</li>
  <li>The full stop is treated as the end tag (</s>).</li>
  <li>The program supports input corpus from Stanford POS tagger only.</li>
  <li>Only one line of text can be tagged as a test sentence. When multiple sentences are required to be tagged, kindly execute the source code multiple times.</li>
</ol>
