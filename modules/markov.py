import sys
sys.dont_write_bytecode = True

import re, random, redis, cPickle

LOAD_ORDER = 60

redis_conn = redis.Redis()
chain_length = 2
max_words = 30
messages_to_generate = 5
separator = '\x01'
stop_word = '\x02'

pa = re.compile(r"(^\[.*\]\s\w*\:\s)")


def sanitize_message(message):
    return re.sub('[\"\']', '', message.lower())

def split_message(message):
    # split the incoming message into words, i.e. ['what', 'up', 'bro']
    words = message.split()

    # if the message is any shorter, it won't lead anywhere
    if len(words) > chain_length:

        # add some stop words onto the message
        # ['what', 'up', 'bro', '\x02']
        words.append(stop_word)

        # len(words) == 4, so range(4-2) == range(2) == 0, 1, meaning
        # we return the following slices: [0:3], [1:4]
        # or ['what', 'up', 'bro'], ['up', 'bro', '\x02']
        for i in range(len(words) - chain_length):
            yield words[i:i + chain_length + 1]

def generate_message(seed):
    key = seed
    #print "Starting key is %s" % key
    # keep a list of words we've seen
    gen_words = []

    # only follow the chain so far, up to <max words>
    for i in xrange(max_words):

        # split the key on the separator to extract the words -- the key
        # might look like "this\x01is" and split out into ['this', 'is']
        words = key.split(separator)

        # add the word to the list of words in our generated message
        gen_words.append(words[0])

        # get a new word that lives at this key -- if none are present we've
        # reached the end of the chain and can bail
        next_word = redis_conn.srandmember(key)
        #print make_key(key)
        #print "Next word: %s" % next_word
        if not next_word:
            break

        # create a new key combining the end of the old one and the next_word
        key = separator.join(words[1:] + [next_word])
        #print "new key is %s" % key

    return ' '.join(gen_words)

def generatefromoldmessages(channel):
    with open("/var/www/twitch/%s/chat/log.txt" % channel.replace('#','')) as rf:
        t = 'derp'
        while t != '':
            t = rf.readline()
            t = t.replace('\n','')

            message =  re.sub(pa, "", t)

            if len(message.split()) < chain_length: continue


            # split up the incoming message into chunks that are 1 word longer than
            # the size of the chain, e.g. ['what', 'up', 'bro'], ['up', 'bro', '\x02']
            for words in split_message(sanitize_message(message)):
                # grab everything but the last word
                key = separator.join(words[:-1])

                # add the last word to the set
                redis_conn.sadd(key, words[-1])


def addmessage(mes):
    if len(mes.split()) < chain_length: return

    for words in split_message(sanitize_message(mes)):
        key = separator.join(words[:-1])
        redis_conn.sadd(key, words[-1])


def markov(key=None):
    if key is None:
        key = redis_conn.randomkey()

    messages = []
    best_message = ''

    for i in range(messages_to_generate):
        generated = generate_message(seed=key)

        if len(generated) > len(best_message):
            best_message = generated
            messages.append(best_message)
            
    print "we have this: %s " % messages

    if len(messages) and len(messages[0].split()) > 1:
        return str(random.choice(messages[int(len(messages)*0.6):]))
    else:
        return "I got nothing."


def setup(bot):
    # I dunno if I need to do anything here
    pass

def alert(event):
    if event.etype == 'msg':
        if not event.data.startswith(('#','!')):
            addmessage(event.data)
