import re
import os

string = ["mercury,venus\n","earth,mars\n","jupiter,saturn\n"]
out = map(lambda x: x.replace('\n',''), string)
out = map(lambda x: x.split(','), out)
print(list(out)[0][1])
