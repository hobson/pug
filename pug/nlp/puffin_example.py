#test_puffin.py

from puffin_lsa import PuffinLSA
from examples import titles

lsa = PuffinLSA()
for txt in docs:
    lsa.parse(txt)

lsa.build()
lsa.printA()
lsa.calc()
lsa.printSVD()
