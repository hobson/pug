% title: Data Science with `pug`
% subtitle: PDX-Python January 2014
% author: <a href="https://github.com/hobsonlane">Hobson Lane</a>
% thankyou: Thanks PDX-Python!
% thankyou_details: And all these open source contributors...
% contact: <a href="http://djangoproject.org">Django</a>
% contact: <a href="http://python.org">Python</a>
% contact: <a href="http://pypi.python.org/pypi/pyodbc">pyODBC</a>
% favicon: <img src="https://www.python.org/favicon.ico"/>

---
title: Audience Survey
build_lists: true

* Who has done Data Science?
    - Stats, ML, NLP?
        + optimization, controls, classification, prediction
    - DBs or ORMs?
        + `postgres`, `mysql`, `neo4j`, `sqlite`, `django`
* Data Science using Python?
    - R, Matlab, Octave?
* NLP (Natural Language Processing) using Python?
    - `nltk`, `scrapy`, `numpy`, `collections.Counter`

---
title: Data

* Acquisition (ETL)
* Exploration (EDA)

---
title: Data Acquisition

* ETL
    * **E**xtract -- download, API, scrape
        - Scrapy
    * **T**ransform -- shuffle columns, normalize
        - [pug](https://github.com/hobsonlane) -- `manage.py dbstats`
        - `manage.py inspectdb`
    * **L**oad -- `manage.py loaddata`
        - DBA (Database Administration)
* Stanford Data Wrangler

---
title: Exploration: Ask

* EDA (Exploratory Data Analysis)
* Questions to Ask (most DBs will tell you)
    - Size (# of databases, tables, records)
    - Dimensions: # columns, any natural language
    - Connectedness: relationships, indexes, PKs
    - Types: ordinal, continuous, discrete, *bulk* (NL)

---
title: Exploration: Calculate

* Things to calculate
    - Standard deviation, entropy
    - Min/Max
    - Correlation coefficients (mutual information)

[scikit-learn](http://scikit-learn.org) has an excellent [flow chart](http://scikit-learn.org/stable/tutorial/machine_learning_map/index.html)

---
title: Science

* Model (hypothesis)
    - `scikit` has a lot of excellent models
    - `pug` has very few
* Test
    - Configure the model
    - Tune
    - Cross-sample validation
    - **repeat**
* Share -- Visualization

---
title: Let's Do NLP

* Count words (build an 'Occurrence Matrix
* Reduce dimensions (word vocabulary)
* Visualize the connections (graph)
* Visualize & sort the matrices
* *SVD on sparse matrix*

#LSI = Latent Semantic Indexing

---
title: Count Word Occurrences

<pre class="prettyprint" data-lang="python">
    from pug.nlp.classifier import get_words

    docs = ['Explicit is better than implicit.',
            'Simple is better than complex.',
            'Flat is better than nested.',
           ]
    O_sparse = [Counter(get_words(d)) for d in docs]
    print O_sparse
</pre>

    [Counter({'better': 1, 'explicit': 1, 'than': 1, 'implicit': 1}), 
     Counter({'simple': 1, 'better': 1, 'complex': 1, 'than': 1}), 
     Counter({'better': 1, 'flat': 1, 'than': 1, 'nested': 1})]

---
title: Total Counts

<pre class="prettyprint" data-lang="python">
    from collections import Counter

    total = Counter()
    for c in O_sparse:
        total += c
    print total
</pre>

    Counter({'than': 3, 'better': 3, 'flat': 1, 'simple': 1, 'explicit': 1,
             'complex': 1, 'nested': 1, 'implicit': 1})

* Not very interesting

---
title: Occurrence Matrix

<pre class="prettyprint" data-lang="python">
    from tabulate import tabulate
    words, O = list(total), []
    for counts in O_sparse:
        O += [[0] * len(words)]
        for word, count in counts.iteritems():
            j = words.index(word)
            O[-1][j] += count
    print tabulate(O)
</pre>

    flat simple explicit than better complex nested implicit
    ---- ------ -------- ---- ------ ------- ------ --------
     0     0     1        1    1      0       0      1
     0     1     0        1    1      1       0      0
     1     0     0        1    1      0       1      0

---
title: Graph Visualization with D3

* Our word occurrence matrix shows connections
    - word1 <--0--> doc1
    - word2 <--3--> doc1
    - ...
* This is a directed graph
    - source: word
    - target: document
    - value: frequency (number of occurrences)


---
title: Introducing `pug`

<pre class="prettyprint" data-lang="bash">
    $ git clone git@github.com:hobsonlane/pug.git
    $ cd pug/pug/miner/static
    $ python server.py &
    $ firefox http://localhost:8001/occurrence_force_graph.html
</pre>

Do it yourself: [hobsonlane.github.io/pug](http://hobsonlane.github.io/pug)</a>

---
title: What Patterns Do You See?

* Outliers?
    * Documents and Words
    * George Washington... because of infrequent use of "the"

[hobsonlane.github.io/pug](http://hobsonlane.github.io/pug/pug/miner/static/occurrence_force_graph.html)

---
title: Curse of Dimensionality

* Difficult to untangle
    - Additional pop ups and highlighting of edges would help
    - Additional dimensions as size and shape of circles
    - What about short-circuiting the documents to see word-word connections?
* [view source](view-source:http://hobsonlane.github.io/pug/pug/miner/static/occurrence_force_graph.html)"
* Adjust charge, length, stiffness, friction -- balancing game...
    - Stability vs Structure
    - Beauty vs Complexity

---


---
title: `pug` Files

* bin -- command-line tools, .bashrc, and other config files
* nlp/db -- interacting with databases and migrating data
* nlp/util -- , DBs
* nlp

---
title: `pug` Modules

pug
├── crawler -- django app for wikiscrapy
├── crawlnmine -- django app for settings.py
├── db -- db_routers, explore, sqlserver
├── miner -- django app for db exploration
└── nlp -- classifier, `db_decision_tree`, db, mvlr, parse, util, re
           format numbers & dates, importing of "pivots" in spreadsheets
    ├── wikiscrapy


