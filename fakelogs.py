__author__ = 'Nick'

# generates logs for testing scanlog.py

import random
letters = 'abcdefghijklmnopqrstuvwxyz'
numbers = '0123456789'
import time
import sys

wanted_attributes = ('AttributeConnId', 'AttributeOtherTrunk', 'AttributeExtensions',)
wanted_members = ('GCTI_Network_Timeslot',)

def random_letters():
    return "".join([random.choice(letters) for r in range(20)])

def random_numerals():
    return "".join([random.choice(numbers) for r in range(8)])

def chance(percent):
    return random.randint(0,1000)/10.0 < percent

def log_keyval(level, k, v):
    return

sys.stdout = open(r'C:\Users\Nick\PycharmProjects\complangpython\logs\test\8.log', 'w')

for n in range(100):
    print ('@' + time.strftime('%H:%M:%S', time.localtime()) + ' ' + random_letters() +
           ('EventEstablished' if random.randint(1,1000) < 7 else ''))

    for s in range(5, random.randint(5,50)):
        next_plant = random.choice(wanted_attributes)
        nonsense = random_letters()
        # level 1 (attributes) both key and value are single-quoted, sep by space
        print('\t\'' + "Attribute" + (nonsense if chance(percent=95.0) else next_plant) +
              '\' \'' + random_numerals() + '\'')
        # level 2 (members of attributes)
        members = {}
        for s in range(3,random.randint(0, 15)):
            name = "Member" + random_letters()
            if next_plant == 'AttributeExtensions':
                if chance(percent=5.0):
                    name = 'GCTI_Network_Timeslot'
            value = random_numerals()
            members.update({name: value})
            # both key and value are single-quoted, sep by space
        for k, v in members.items():
            print('\t\t\'{0}\' \'{1}\''.format(k, v))

