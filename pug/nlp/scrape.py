from scrapy.selector import Selector
from pug.nlp.util import make_int, make_float, make_us_postal_code

def get_tables(html, verbosity=0):
    """Extract a list of tables of python objects from HTML

    return a list of lists (tables) of lists (rows) of objects (cell values)

    Convert each text element to the most complete python object possible.
    >>> get_tables('<p>first table<table><thead><tr><th>H1</th><th>H2</th></tr></thead><tr><td>1</td><td>one</td></tr><tr><td>2</td><td>two</td></tr><tr><td>3</td><td>three</td></tr></table><p>malformed table<table><tr><tr><td>1</td><td>one</td></tr><tr><td>2</td><td>two</td></tr><tr><td>3</td><td>three</td></tr></table><p>empty table<table></table>')
    [[[u'H1', u'H2'], [1, u'one'], [2, u'two'], [3, u'three']],
    [[], [1, u'one'], [2, u'two'], [3, u'three']],
    []]
    """  
    dom = Selector(text=html)
    tables = dom.css('table')

    ans = []
    for table in tables:
        if verbosity > 2:
            print 'table={0}'.format(table)
        rows = table.css('tr')
        ans += [[]]
        for i, row in enumerate(rows):
            if verbosity > 2:
                print 'row {1}={0}'.format(row, i)
            values = row.css('th') or row.css('td')
            ans[-1] += [[]]
            for j, value in enumerate(values):
                s = value.css('::text').extract()
                if s:
                    s = s[0]
                if verbosity > 1:
                    print 'value({1},{2})={0}'.format(s, i, j)
                try:
                    s = float(s)
                except:
                    pass
                if isinstance(s, float):
                    try:
                        if int(s) == s:
                            s = int(s)
                    except:
                        pass
                if verbosity > 1:
                    print 'value({1},{2})={0}'.format(s, i, j)
                ans[-1][-1] += [s]
    return ans