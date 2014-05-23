% title: Data Science with `pug`
% subtitle: PDX-Python
% subtitle: <i><small>January 28, 2014</small></i>
% author: <a href="https://hobson.github.io/pug">hobson.github.io/pug</a>
% thankyou: Thanks PDX-Python!
% thankyou_details: And the open source world...
% contact: <a href="http://python.org">Python</a>
% favicon: <img src="https://www.python.org/favicon.ico"/>
% contact: <a href="http://djangoproject.org">Django</a>
% contact: <a href="http://nltk.org">NLTK</a>
% contact: <a href="http://d3js.org">Mike Bostock</a>
% contact: <a href="http://pypi.python.org/pypi/pyodbc">pyODBC</a>

---
title: Survey
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
subtitle: ETL

* **E**xtract -- download, API, scrape
    - Scrapy
* **T**ransform -- shuffle columns, normalize
    - [pug](https://github.com/hobson) -- `manage.py dbstats`
    - `manage.py inspectdb`
* **L**oad -- `manage.py loaddata`
    - DBA (Database Administration)

<footer>e.g. Stanford Data Wrangler</footer>

---
title: Exploration

* EDA (Exploratory Data Analysis)
* Questions to Ask
    - Size (# of databases, tables, records)
    - Dimensions: # columns, any natural language
    - Connectedness: relationships, indexes, PKs
    - Types: ordinal, continuous, discrete, *bulk* (NL)

---
title: Exploration

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
subtitle: specifically LSI = Latent Semantic Indexing

* Count words (build an 'Occurrence Matrix
* Reduce dimensions (word vocabulary)
* Visualize the connections (graph)
* Visualize & sort the matrices
* *SVD on sparse matrix* <-- not shown here, but in `pug`

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

Do it yourself: [hobson.github.io/pug](http://hobson.github.io/pug)</a>

---
title: A More Interesting Example

    from nltk import download, ConditionalFreqDist
    download('inaugural')
    from nltk.corpus import inaugural

    cfd = ConditionalFreqDist(
            (target, fileid[:4])
            for fileid in inaugural.fileids()
            for w in inaugural.words(fileid)
            for target in ['america', 'citizen']
            if w.lower().startswith(target)) [1]

---
title: Frequency Distribution Over Time
subtitle: `cfd.plot()`
class: img-top-center

<img height=350 src=inaugural_cfd.png />

---
title: Which words are important
subtitle: Entropy

$\sum_{i=0}^n P(x_i) \log_b(P(x_i))$

    >>> from scipy.stats import entropy
    >>> entropy([.5, .5]) * log(2.)
    1.0
    >>> from pug.nlp import inaugural
    >>> inaugural.renyi_entropy([.5, .5], alpha=1)
    1.0

---
title: What Patterns Do You See?
subtitle: <a href="http://hobson.github.io/pug/pug/miner/static/occurrence_force_graph.html">hobson.github.io/pug</a>

* Outliers?
    * Documents and Words
    * George Washington... because of infrequent use of "the"

---
title: Curse of Dimensionality

* Difficult to untangle
    - Additional pop ups and highlighting of edges would help
    - Additional dimensions as size and shape of circles
    - What about short-circuiting the documents to see word-word connections?
* [view source](view-source:http://hobson.github.io/pug/pug/miner/static/occurrence_force_graph.html)
* Adjust charge, length, stiffness, friction -- balancing game...
    - Stability vs Structure
    - Beauty vs Complexity

---
title: Words Shared by Documents?

Multiply the frequencies a word is used in documents linked to it to get a "total" count:

**Document<-->Document** [graph](http://hobson.github.io/pug/pug/miner/static/doc_force_graph.html) or [matrix](http://hobson.github.io/pug/pug/miner/static/doc_cooccurrence.html)

$\mathbf O_{docs}=\mathbf O \mathbf O^T$

**Word<-->Word** [graph](http://hobson.github.io/pug/pug/miner/static/word_force_graph.html) or [matrix](http://hobson.github.io/pug/pug/miner/static/word_cooccurrence.html)

$\mathbf O_{words}=\mathbf O^T \mathbf O$

(for the examples given previously)

---
title: `pug` Modules

* crawler: django app for controlling wikiscrapy
* crawlnmine: django app for settings.py
* db: db_routers, explore, sqlserver
* miner: django app for db exploration
* nlp: classifier, `db_decision_tree`, db, mvlr, parse, util, re, wikiscrapy
           format numbers & dates, importing of "pivots" in spreadsheets

---
title: Thank You for the Education

* [Sharp Laboratories](sharplaboratories.com) -- John, Jeff, Phil, LiZhong
* [Building Energy](buildingenergy.com) -- Aleck, John, Steven
* [Squishy Media](squishymedia.com) -- Eric, Xian, Ben, Greg, Jesse

---
title: Resources

* [Coursera](coursera.org)
* [Udacity](udacity.com)
* [Programming Collective Intelligence](http://shop.oreilly.com/product/9780596529321.do)
* [Python for Data Analysis](http://shop.oreilly.com/product/0636920023784.do)
* [Building Machine Learning in Python](http://shop.oreilly.com/product/9781782161400.do)
* [Doing Data Science](http://shop.oreilly.com/product/0636920028529.do)
* [Norvig](norvig.com)

---
title: Contributors

* Hobson Lane <pugauthors@totalgood.com>
* LiZhong Zheng <lizhong@MIT.edu>
* Your Name Here ;) <pugauthors@totalgood.com>



