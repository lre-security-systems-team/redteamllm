from graphviz import Digraph
import time

dot = Digraph()





dot.node('A')
prev = 'A'
while True:
    new = prev +'1'
    dot.node(new)
    dot.edge(prev,new)
    prev = new
    time.sleep(1)
    dot.render(quiet_view=True)

    