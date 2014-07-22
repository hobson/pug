Pycon 2014 Open Space Submission
--------------------------------

The power and utility of Python NLP (Natural Language Processing) algorithms can be greatly enhanced using javascript libraries such as D3.js to distribute processing power to web browsers.  Nonetheless, only small datasets (100's of documents with 1000's of words each) can be effectively processed. Here we show the power and limitations of this NLP architecture and potential breakthroughs in incremental SVD (singular value decomposition) algorithms that hold promise.


[Material previously-presented at a PDX-Python user-group meeting](http://hobson.github.io/pug/pug/docs/slidedeck-pdxpy/index.html#1)

Example Visualizations of US Presidential Inaugural Speeches and their 100 Highest Entropy Words

The co-occurrence matrices can be visulized as heat-maps and shuffled/sorted according to various criteria, like political party of the president for US innaugural speeces:
[Word Co-Occurrence Matrix Visualization and Sorting](http://hobson.github.io/pug/pug/miner/static/word_cooccurrence.html)
[Document Similarity Matrix Visualization and Sorting](http://hobson.github.io/pug/pug/miner/static/doc_cooccurrence.html)

Can you guess what will happen if you produce a force-directed graph that includes both words and documents? The strength of connections between nodes (their attraction) is their cooccurrence.
[Graph Clustering of Words and Documents](http://hobson.github.io/pug/pug/miner/static/occurrence_force_graph.html)

Can you guess the words that will be outliers (usage is independent of other words) in innaugural speeches?
[Word Co-Occurrence Graph Clustering](http://hobson.github.io/pug/pug/miner/static/word_force_graph.html)


Can you guess the presidential innaugural speeches that will be outliers when they are clustered according to word usage?
[Document Similarity Graph Clustering](http://hobson.github.io/pug/pug/miner/static/doc_force_graph.htm)