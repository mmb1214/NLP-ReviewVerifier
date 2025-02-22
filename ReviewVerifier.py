import nltk
import string
import random
import collections
import nltk.metrics
import pandas
from nltk.metrics.scores import (precision, recall, f_measure)
from pathlib import Path
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.linear_model import LogisticRegression
from nltk.corpus import opinion_lexicon
#nltk.download("punkt")
#nltk.download("stopwords")
nltk.download("opinion_lexicon")


# Reads each file in directory and adds to list that will be returned along w/ file #
def readFiles(filePath):
    files = []
    for file in filePath:
        current = open(file, 'r')
        text = current.read()
        current.close()
        files.append([text, int(''.join(char for char in file.name if char.isdigit()))])
    return files


# Reads ratings files
def readRatings(filePath):
    strList = []
    for file in filePath:
        current = open(file, 'r')
        text = current.read()
        current.close()
        strList.append(text)
    return strList


# Key function for list.sort() to sort files by file #
def takeFileNum(item):
    return item[1]


# Method for stemming a list
def lexStemmer(lexicon):
    stemmedLexicon = []
    for word in lexicon:
        stemmedLexicon.append(porter.stem(word))
    return stemmedLexicon


# Function case folds documents and remove punctuation
def removePunct(reviews):
    result = []
    for document in reviews:
        document = document.lower()
        document = "".join([char for char in document if char not in string.punctuation])
        result.append(document)
    return result


# Formats data for NLTK NB classifier
def formatForNB(reviews, tokens):
    result = []
    for x in reviews:
        doc_tokens = word_tokenize(x[0])
        dictionary = {}
        for t in tokens:
            dictionary[t] = t in doc_tokens
        newTup = (dictionary, x[1])
        result.append(newTup)
    return result


# Method that formats dataset for LR
def reformatForLR(notFormatted):
    reformatted = []
    for rev in notFormatted:
        bigList = [word_tokenize(rev[0]), rev[1], rev[2]]
        reformatted.append(bigList)
    return reformatted


# Given a review, returns list of features counts with class appended
def featureCount(x):
    frequencies = [0] * 12
    for w in x[0]:
        if w == "refund":
            frequencies[2] += 1
        elif w == "return":
            frequencies[2] += 1
        elif w in stemmedPosLex:
            frequencies[0] += 1
        elif w in stemmedNegLex:
            frequencies[1] += 1
    restrung = " ".join(x[0])
    reviewBigrams = list(nltk.bigrams(restrung.split()))
    for bigram in reviewBigrams:
        if (bigram[0] == 'dont' and bigram[1] == 'buy') or (bigram[0] == 'not' and bigram[1] == 'buy'):
            frequencies[4] += 1
        elif (bigram[0] == 'not') and bigram[1] == 'work':
            frequencies[5] += 1
        elif (bigram[0] == 'no') and bigram[1] == 'problem':
            frequencies[3] += 1
        elif (bigram[0] == 'not') and bigram[1] in stemmedPosLex:
            frequencies[6] += 1
        elif (bigram[0] == 'not') and bigram[1] in stemmedNegLex:
            frequencies[7] += 1
        elif (bigram[0] == 'veri' or 'realli') and bigram[1] in stemmedPosLex:
            frequencies[8] += 1
        elif (bigram[0] == 'veri' or 'realli') and bigram[1] in stemmedNegLex:
            frequencies[9] += 1
    if x[1] == 'pos':
        frequencies[-2] = 1
    elif x[1] == 'neg':
        frequencies[-2] = 0
    frequencies[-1] = x[2]
    return frequencies


# Lexicons for LR features:
print("formatting lexicons...")
print("please make sure 'opinion_lexicon' is downloaded")
porter = PorterStemmer()
nltkPosLex = opinion_lexicon.positive()
nltkNegLex = opinion_lexicon.negative()
posLex = ["".join(list_of_words) for list_of_words in nltkPosLex]
negLex = ["".join(list_of_words) for list_of_words in nltkNegLex]

stemmedPosLex = set(lexStemmer(posLex))
stemmedNegLex = set(lexStemmer(negLex))

# File paths for each labeled directory w/ only txt files selected
negFolder = Path('./neg/').rglob('*.txt')
posFolder = Path('./pos/').rglob('*.txt')
posRatingsPath = Path('./ratings/').rglob('positive.txt')
negRatingsPath = Path('./ratings/').rglob('negative.txt')

# Lists of every txt file in each folder
print("reading files...")
negFiles = [x for x in negFolder]
posFiles = [y for y in posFolder]
posRatingsFile = [pos for pos in posRatingsPath]
negRatingsFile = [neg for neg in negRatingsPath]

labeledPosReviews = readFiles(posFiles)
labeledNegReviews = readFiles(negFiles)
posRatings = readRatings(posRatingsFile)
negRatings = readRatings(negRatingsFile)
labeledPosReviews.sort(key=takeFileNum)
labeledNegReviews.sort(key=takeFileNum)
tempPosList = []
tempNegList = []
for review in labeledPosReviews:
    tempPosList.append(review[0])
for review in labeledNegReviews:
    tempNegList.append(review[0])
labeledPosReviews = tempPosList
labeledNegReviews = tempNegList


# Split ratings from each file into list w/ # and rating
print("preprocessing data...")
posRatingsSplit = posRatings[0].split("\n")
negRatingsSplit = negRatings[0].split("\n")
posSepRatings = []
negSepRatings = []
for rating in posRatingsSplit:
    posSepRatings.append(rating.split(" "))

for rating in negRatingsSplit:
    negSepRatings.append(rating.split(" "))

# Prefixes 'P' for positive, 'N' for negative to identify which directory it came from for later
for rating in posSepRatings:
    rating[0] = 'P' + rating[0]

for rating in negSepRatings:
    rating[0] = 'N' + rating[0]

# Case fold and remove punct.
posReviews = removePunct(labeledPosReviews)
negReviews = removePunct(labeledNegReviews)

# Remove stop words
labeledReviews = []
stopWords = stopwords.words()
for i, document in enumerate(posReviews):
    for word in document:
        if word not in stopWords:
            newDoc = " ".join(porter.stem(word))
    labeledReviews.append((document, "pos", posSepRatings[i]))

for i, document in enumerate(negReviews):
    for word in document:
        if word not in stopWords:
            newDoc = " ".join(porter.stem(word))
    labeledReviews.append((document, "neg", negSepRatings[i]))

# Randomizing and splitting data for training and testing, use same random value for ratings
random.shuffle(labeledReviews)
training = labeledReviews[0:(int)(len(labeledReviews)/2)]
testing = labeledReviews[(int)(len(labeledReviews)/2):]

# Generating tokens
trainTokens = set(word for words in training for word in word_tokenize(words[0]))
testTokens = set(word for words in testing for word in word_tokenize(words[0]))

# Tokenizing and formatting for NB
print("started formatting data for NB classifier...")
nbTrainData = formatForNB(training, trainTokens)
nbTestData = formatForNB(testing, testTokens)
print("finished formatting data for NB.")

# NB classifer training w/ training dataset
print("training NB classifier...")
classifier = nltk.NaiveBayesClassifier.train(nbTrainData)

# Most informative features from NB classifier
classifier.show_most_informative_features()

# Run NB classifer over testing dataset
print("testing NB classifier...")
truesets = collections.defaultdict(set)
classifiersets = collections.defaultdict(set)
nbPredictions = []
for i, (doc, label) in enumerate(nbTestData):
    truesets[label].add(i)
    observed = classifier.classify(doc)
    classifiersets[observed].add(i)
    nbPredictions.append(observed)

# Calculate positive/negative precision and recall
print("evaluating classifier...")
print(" ################################## NB Results: ################################## ")
pos_precision = precision(truesets['pos'], classifiersets['pos'])
neg_precision = precision(truesets["neg"], classifiersets["neg"])
pos_recall = recall(truesets['pos'], classifiersets['pos'])
neg_recall = recall(truesets["neg"], classifiersets["neg"])
pos_f = f_measure(truesets['pos'], classifiersets['pos'])
neg_f = f_measure(truesets["neg"], classifiersets["neg"])
print("Positive precision: ")
print(pos_precision)
print("Negative precision: ")
print(neg_precision)
print("Positive recall: ")
print(pos_recall)
print("Negative recall: ")
print(neg_recall)
print("Positive f-measure: ")
print(pos_f)
print("Negative f-measure: ")
print(neg_f)

# Feature table for LR
'''
Feature:    Definition:                         Initial weight:
f1          word ∈ pos. lexicon                 1
f2          word ∈ neg. lexicon                 -1
f3          contains "refund" or "return"       -5 (each adds to count)
f4          bigrams "no problem"                3
f5          bigrams "dont buy" or "not buy"     -3
f6          bigrams "not work"                  -3
f7          bigrams "not (positive word)"      -1
f8          bigrams "not (negative word)"      1
f9          bigrams "very (positive word)"     5
f10         bigrams "very (negative word)"     -5
'''

# Using the same split, reformat training and testing data for LR classifer
print("formatting data for LR...")
lrTraining = reformatForLR(training)
lrTesting = reformatForLR(testing)
#print(lrTesting)
print("finished formatting data for LR.")

print("counting features for LR classifier...")
formattedTraining = []
for review in lrTraining:
    formattedTraining.append(featureCount(review))

formattedTesting = []
for review in lrTesting:
    formattedTesting.append(featureCount(review))

# Turning data into DataFrames w/ labeled feature columns
print("building dataframes...")
trainFrame = pandas.DataFrame(formattedTraining, columns=['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'class', 'rating'])
testFrame = pandas.DataFrame(formattedTesting, columns=['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'class', 'rating'])

# Get doc. # w/ feature columns from dataframe
xTrain = trainFrame.iloc[:, 0:10]
xTest = testFrame.iloc[:, 0:10]

# Get doc. # w/ class tag from dataframe
yTrain = trainFrame.iloc[:, -2]
yTest = testFrame.iloc[:, -2]
uncutTestTruePos = testFrame.loc[testFrame['class'] == 1]
uncutTestTrueNeg = testFrame.loc[testFrame['class'] == 0]
testTruePos = uncutTestTruePos.iloc[:, 0:10]
testTrueNeg = uncutTestTrueNeg.iloc[:, 0:10]

# Train LR classifier on data
print("beginning logistic regression...")
logRegression = LogisticRegression(solver='sag', fit_intercept=True, class_weight='balanced', max_iter=1000)
# ? Potential class_weight=[1, -1, -5, 3, -3, -3, -1, 1, 5, -5]
logRegression.fit(xTrain, yTrain)
print("logistic regression training done.")

# Testing LR classifier
print("testing LR classifier...")
predictedFromTruePos = logRegression.predict(testTruePos)
predictedFromTrueNeg = logRegression.predict(testTrueNeg)
print("finished testing LR classifier.")

# Comparing LR predicted classes w/ true classes
truePositives = 0
falsePositives = 0
trueNegatives = 0
falseNegatives = 0

for result in predictedFromTruePos:
    if result == 0:
        falseNegatives += 1
    else:
        truePositives += 1

for result in predictedFromTrueNeg:
    if result == 0:
        trueNegatives += 1
    else:
        falsePositives += 1

# Count true/false positives and negatives; calculate precision, recall, and f-measure
print(" ################################## LR Results: ################################## ")
print("# of true positives: " + str(truePositives) + ", # of false positives: " +
      str(falsePositives) + ", # of true negatives: " + str(trueNegatives) +
      ", # of false negatives: " + str(falseNegatives))

lrPosPrec = truePositives / (truePositives + falsePositives)
lrNegPrec = trueNegatives / (trueNegatives + falseNegatives)
lrPosRecall = truePositives / (truePositives + falseNegatives)
lrNegRecall = trueNegatives / (trueNegatives + falsePositives)
lrPosF = (2 *(lrPosPrec * lrPosRecall)) / (lrPosPrec + lrPosRecall)
lrNegF = (2 *(lrNegPrec * lrNegRecall)) / (lrNegPrec + lrNegRecall)
print("Positive Precision: " + str(lrPosPrec))
print("Negative Precision: " + str(lrNegPrec))
print("Positive Recall: " + str(lrPosRecall))
print("Negative Recall: " + str(lrNegRecall))
print("Positive F-Measure: " + str(lrPosF))
print("Negative F-Measure: " + str(lrNegF))

# Identifying fake reviews through raw predictions from NB classifier and ratings
print("identifying fake reviews...")
truePosResults = []
trueNegResults = []
for result in predictedFromTruePos:
    truePosResults.append(result)

for result in predictedFromTrueNeg:
    trueNegResults.append(result)

rawResults = truePosResults + trueNegResults
actualRatings = uncutTestTruePos['rating'].tolist() + uncutTestTrueNeg['rating'].tolist()

lrFake = []
for i, rating in enumerate(actualRatings):
    if (float(rating[1]) > 3.0) and rawResults[i] == 0:
        lrFake.append(rating)
    elif (float(rating[1]) < 3.0) and rawResults[i] == 1:
        lrFake.append(rating)
print("Potentially fake reviews identified w/ LR:")
print(lrFake)
print("# of reviews identified as potentially fake:")
print(len(lrFake))
