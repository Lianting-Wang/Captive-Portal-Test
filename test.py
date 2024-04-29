import time
from test_mininet import test_mininet

test_mininet()

with open('mininet_grade.txt', 'r') as file:
    print(file.read())