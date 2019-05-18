README
------
HMM Probability calculator
Python version:             3.7.1

Source code file:           hmm_probability_calculator.py

Input files:
POS_corpus.txt          -   POS tagged corpus obtained using Stanford POS tagger
                            Note: The POS tagged corpus can be obtained using Stanford POS tagger.
testset.txt             -   Test sentence to tag and find maximum probable tagging sequence

Output files:
lexical_prob.txt        -   Contains the P(wi|ti) for all unique words in the input corpus
transition_prob.txt     -   Contains all the tag transition probabilities for all possible tag transitions in the input corpus
testset_output.txt      -   Contains all possible tagging combinations for the given test sentence based on the input corpus and the most probable tagging sequence 
                            based on the probility calculation.
                            
1. Run the source code file using Python.
> python hmm_probability_calculator.py
2. The tagged corpus in POS_corpus.txt will be utilized to tag the 'first' line in testset.txt
The results will be displayed in the command prompt while detailed results will be written to lexical_prob.txt, transition_prob.txt and testset_output.txt
3. The full stop is treated as the end tag (</s>).

Notes:
1. The program supports input corpus from Stanford POS tagger only.
2. Only one line of text can be tagged as a test sentence. When multiple sentences are required to be tagged, kindly execute the source code multiple times.
