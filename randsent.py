#!/usr/bin/env python
"""
601.465/665 — Natural Language Processing
Assignment 1: Designing Context-Free Grammars

Assignment written by Jason Eisner
Modified by Kevin Duh
Re-modified by Alexandra DeLucia

Code template written by Alexandra DeLucia,
based on the submitted assignment with Keith Harrigian
and Carlos Aguirre Fall 2019
"""
import os
import sys
import random
import argparse

# Want to know what command-line arguments a program allows?
# Commonly you can ask by passing it the --help option, like this:
#     python randsent.py --help
# This is possible for any program that processes its command-line
# arguments using the argparse module, as we do below.
# 
# NOTE: When you use the Python argparse module, parse_args() is the
# traditional name for the function that you create to analyze the
# command line.  Parsing the command line is different from parsing a
# natural-language sentence.  It's easier.  But in both cases,
# "parsing" a string means identifying the elements of the string and
# the roles they play.

def parse_args():
    """
    Parse command-line arguments.

    Returns:
        args (an argparse.Namespace): Stores command-line attributes
    """
    # Initialize parser
    parser = argparse.ArgumentParser(description="Generate random sentences from a PCFG")
    # Grammar file (required argument)
    parser.add_argument(
        "-g",
        "--grammar-file", 
        type=str, required=True, 
        help="Path to grammar file",
    )
    # Start symbol of the grammar
    parser.add_argument(
        "-s",
        "--start-symbol", 
        type=str,
        help="Start symbol of the grammar",
        default="ROOT",
    )
    # Number of sentences
    parser.add_argument(
        "-n",
        "--number-of-sentences",
        type=int,
        help="Number of sentences to generate",
        default=1,
    )
    # Maximum number of nonterminal expansions when generating the sentence
    parser.add_argument(
        "-M",
        "--max-expansions",
        type=int,
        help="Max number of nonterminal expansions when generating the sentence",
        default=450,
    )
    # Print the derivation tree for each generated sentence
    parser.add_argument(
        "-t",
        "--tree",
        action="store_true",
        help="Print the derivation tree for each generated sentence",
        default=False,
    )

    return parser.parse_args()


class Grammar:
    lastRule = -1
    rules = {}
    lhsRules = {}
    rhsRules = {}
    lhsCount = {} 
    totalLhsCount = 0
    expansions = 1

    def __init__(self, grammar_file):
        """
        Context-Free Grammar (CFG) Sentence Generator

        Args:
            grammar_file (str): Path to a .gr grammar file
        
        Returns:
            self
        """
        # Parse the input grammar file
        self._load_rules_from_file(grammar_file)

    def _load_rules_from_file(self, grammar_file):
        """
        Read grammar file and store its rules in self.rules

        Args:
            grammar_file (str): Path to the raw grammar file 
            
        """
        line_num= 0

        for line in open(grammar_file, 'r'):
            line_num += 1
            line = line[:-1]   #remove blanklines 
            if line.find('#') != -1:
                line = line[:line.find('#')]
            line = line.strip()  

            if line == "":
                continue       #ignore comments

            f= line.split('\t')

            if len(f) < 3:
                raise ValueError("Error: empty rules are not allowed, unexpected line at line {} : {}".format(line_num, ' '.join(f)))

            (count,lhs,rhs) = (int(f[0]), f[1], f[2])

            rhs = rhs.split()
        
            for i in range(len(rhs)-1):
                if rhs[i].islower() or '?' in rhs[i]:           #add symbols except parentheses
                    if rhs[i+1].islower() or rhs[i+1] == '?':   #add more sympbols parentheses
                        rhs[i+1] = rhs[i] + ' ' + rhs[i+1]
                        rhs[i] =''

            while ('' in rhs):
                rhs.remove('') 

            rhs= tuple(rhs)
                
            self.lastRule += 1
            self.rules[self.lastRule] = (count, lhs, rhs, None)

            if lhs in self.lhsRules : self.lhsRules[lhs].append(self.lastRule)
            else: self.lhsRules[lhs] = [self.lastRule]

            if rhs in self.rhsRules: self.rhsRules[rhs].append(self.lastRule)
            else: self.rhsRules[rhs] = [self.lastRule]

            if lhs in self.lhsCount: self.lhsCount[lhs] += count
            else: self.lhsCount[lhs] = count

            self.totalLhsCount += count

        #add the probability to the rules dict
        for rule_number in range(0, self.lastRule + 1):
            if rule_number in self.rules:
                (count, lhs, rhs, logProb) = self.rules[rule_number]
                logProb = count / self.lhsCount[lhs]
                self.rules[rule_number] = (count, lhs, rhs, logProb)

            else:
                 raise ValueError("rule number %d not found" % rule_number)

    #pick a random rule 
    def pickOne(self, lhs):
        options = self.lhsRules[lhs]
        weights = []
        for i in options:
            (count, lhs, rhs, logProb) = self.rules[i]
            weights.append(logProb)
                    
        r = random.choices(options, weights, k=1)
        picked_rule= r[0]
        return picked_rule

    def genRules(self, ruleNum):
        (count, lhs, rhs, logProb) = self.rules[ruleNum]
        v= [lhs]
        for i in range(len(rhs)):
            if rhs[i] != '<u>':
                v.append(self.iterateRules(rhs[i]))
        return tuple(v)

    def iterateRules(self, t):
        if t not in self.lhsRules:
                return t
        elif self.expansions < self.max_expansions:
                self.expansions += 1
                return self.genRules(self.pickOne(t))
        else:
            return '...'

    def sentenceFormat(self, tree):
        sentence = [] 
        if isinstance(tree, tuple):
            for i in range(1, len(tree)):
                r= self.sentenceFormat(tree[i])
                sentence.extend(r)
        else:
            sentence = [tree]
    
        return sentence

    def generate(self, start_sym, derivation_tree = False):
        rule = self.pickOne(start_sym)
        genTree = self.genRules(rule)

        return genTree if derivation_tree else self.sentenceFormat(genTree)


    def sample(self, start_sym, derivation_tree, max_expansions):
        """
        Sample a random sentence from this grammar

        Args:
            derivation_tree (bool): if true, the returned string will represent 
                the tree (using bracket notation) that records how the sentence 
                was derived
                               
            max_expansions (int): max number of nonterminal expansions we allow
        
        Returns:
            str: the random sentence or its derivation tree
        """
        self.max_expansions = max_expansions
        cfg_sentence = self.generate(start_sym, derivation_tree)

        return cfg_sentence


####################
### Main Program
####################
def main():
    # Parse command-line options
    args = parse_args()

    # Initialize Grammar object
    grammar = Grammar(args.grammar_file)

    # Generate sentences
    for i in range(args.number_of_sentences):
        # Use Grammar object to generate sentence
        sentence = grammar.sample(
            start_sym = args.start_symbol, derivation_tree= args.tree, max_expansions=args.max_expansions
        )

        # Print the sentence with the specified format.
        # If it's a tree, we'll pipe the output through the prettyprint script.
        if args.tree:
            print(sentence)
            prettyprint_path = os.path.join(os.getcwd(), 'prettyprint')
            t = os.system(f"echo '{sentence}' | perl {prettyprint_path}")
        else:
            sentence = ' '.join(sentence)
            print(sentence)


if __name__ == "__main__":
    main()
