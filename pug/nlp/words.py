

THESAURUS = {
    'date': ('datetime', 'time', 'date_time'),
    'time': ('datetime', 'date', 'date_time'),
    }

def synonyms(word):
    return THESAURUS.get(word.lower().strip(), [])