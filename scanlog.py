__author__ = 'Nick'

"""****************************************************** scanlog.py *************************************************

A log scanning program using multi-level generators and iterators
The separation of levels makes it easier to modify the program for
a different specification of log file and also makes it easier
to follow (not so heavily nested)

Present log format is a Genesys call log

Output is in a list and dictionary structure for easy translation into JSON, yaml or repr()

Log files as implemented are 3 levels deep (Events, Attributes, Members)

By modifying the attribute_list and event_list you can select out different data from logs
**********************************************************************************************************************
"""

import os
import re
import itertools
import fileinput

event_list = ('EventEstablished',)
# values are a tuple of attribute members we want to collect; key present means we want to find this attribute
attribute_list = {'AttributeConnId': None,
                          'AttributeOtherTrunk': None,
                          'AttributeExtensions': ('GCTI_Network_Timeslot',)}

logdir = r'C:\Users\Nick\PycharmProjects\scanlog\logs'
logfilename = ('5.log', '6.log', '8.log',)


def chainfiles():
    """chain log files together. Each file breaks off in the middle of a line"""
    filelist = [os.path.join(logdir, f) for f in logfilename]
    line_fragment = ''
    for line in fileinput.input(filelist):
        # detect incomplete last line at the end of a file
        if line[-1:] == '\n':
            # and combine with first line of next file
            yield line_fragment + line
            line_fragment = ''
        else:
            line_fragment = line
    yield line_fragment + line


def parse_line(s):
    """convert line like
       "attrib" "value"
        to a dict key-value pair"""
    kv = eval('(' + ','.join(s.split()) + ',)')
    return dict(Name=kv[0], Value=kv[1])


def levels():
    """the hierarchical level of a line in the log"""
    for line in chainfiles():
        # level 0: no tabs; level 1: 1 tab etc.
        level = len(re.match(r'^(\t*)', line).group(0))
        yield (level, line)

def event_header(levelled_line):
    """an event, but not checked to make sure it's one we're interested in"""
    level, text = levelled_line
    return level == 0 and text.startswith('@')

def chosen_event_header(levelled_line):
    """an event we're interested in"""
    if event_header(levelled_line):
        line = levelled_line[1]
        for i in event_list:
            if i in line:
                return True
    return False

def linelevel(levelled_line):
    # used by itertools.groupby to separate levels
    return levelled_line[0]

def filtered_events():
    loglines = levels()
    # skip header on first file
    leveltext = loglines.__next__()
    # cycle through chosen events
    while True:
        while not chosen_event_header(leveltext):
            leveltext = loglines.__next__()
        event_lines = []
        # grab wanted events for processing
        level, line = leveltext
        # skip @ sign
        event = line[1:]
        # NOTE: some entries contain spaces in their text, not just between timestamp and text
        # Uses Python 3.3 * syntax for stuffing tuples
        timestamp, *text = event.split()
        event = {'EventName': "".join(text),
                 'Timestamp': timestamp,
                 'Filename' : fileinput.filename(),
                 'lineno'   : fileinput.lineno()}
        # populate it with attributes and members
        leveltext = loglines.__next__()
        # gather raw lines
        # try block handles case of last event, where the iteration is exhausted by the while loop
        #
        try:
            while not event_header(leveltext):
                event_lines.append(leveltext)
                leveltext = loglines.__next__()
        except StopIteration:
            pass
        event.update({'Items': itertools.groupby(event_lines, linelevel)})
        yield event

def output():
    for event in filtered_events():
        # strip out level and get ready for filtering
        for level, event_items in event['Items']:
            # levels 1 and 2 both contain key-value pairs in the same format 'Key' 'Value'
            #print('Items', [i for l, i in event_items])
            current_group = [parse_line(i) for l, i in event_items]
            # process level 2 before level 1 because...?
            if level == 2:
                # get a (possibly empty) list of wanted member names from a (possibly non-existent) attribute
                # and keep only those members of the event that are on the list
                if not filtered_attributes:
                    # level 2 occurs before level 1 in an event. Something odd about this, but recover
                    filtered_attributes = [{'Name': 'Level2BeforeLevel1',
                                            'Value': (fileinput.filename(), fileinput.filelineno())}]
                parent = filtered_attributes[-1]['Name']
                members_wanted = attribute_list.get(parent)
                # handle members
                if members_wanted:
                    filtered_members = [r for r in current_group
                                        if r['Name'] in members_wanted]
                    if filtered_members:
                        # attach members to previous attribute
                        filtered_attributes[-1]['Members'] = filtered_members
            if level == 1:
                # handle attributes
                # note name of last attribute: this is the parent of any members in the next level 2 (member) group
                parent = current_group[-1]['Name']
                filtered_attributes = [r for r in current_group
                                       if r['Name'] in attribute_list]
        # commit changes to attributes of the current event including members of this attribute
        event.update({'Attributes': filtered_attributes})
        del event['Items']
        yield event

# for event in output(): print(event)


for k, g in itertools.groupby(output(), lambda ev: ev['Filename']):
    print (k, list(g))
