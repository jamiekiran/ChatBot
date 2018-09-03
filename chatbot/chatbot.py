import sys
sys.path.append(r'C:\Users\Hi\Documents\AIML\github\chatbot')
from generatengrams import ngrammatch
from Contexts import *
import json
from Intents import *
import random
import os
import re
import time
from collections import Counter
import pandas as pd


def check_actions(current_intent, attributes, context):
    '''This function performs the action for the intent
    as mentioned in the intent config file'''
    #Final Action to be performed is invoked here. Bot prints the understood user query.
    if('cuisine' in attributes):
        restaurant_db = pd.read_csv('restaurantsdb.csv').values
        for x in restaurant_db:
            if(x[1] == attributes['cuisine'] and x[2] == attributes['region'] and x[3] == attributes['type']):
                print("Database Access: You have booked restaurant {} which is of {} cuisine in {} region".format(x[0], x[1],x[2],x[3]))
    else:
        print("You have bought {} of {} kg from {} market".format(attributes['veg_name'], attributes['quantity'],attributes['origin']))

    context = IntentComplete()
    return 'action: ' + current_intent.action, context

def check_required_params(current_intent, attributes, context):
    '''Collects attributes pertaining to the current intent'''
    
    #Bot querying the user to obtain required attributes for the intent to be complete
    if context.name != 'CannotIdentifyIntent':
        for para in current_intent.params:
            if para.required:
                if para.name not in attributes:
                    return random.choice(para.prompts), context
    elif context.name == 'CannotIdentifyIntent':
        return 'Cannot Identify Intent', context

    return None, context


def input_processor(user_input, context, attributes, intent):
    '''Entity extraction functions'''
    
    #Checking whether the user has inputed any attributes for any intent.
    attributes, cleaned_input = getattributes(user_input, context, attributes)
    
    return attributes, cleaned_input

def loadIntent(path, intent):
    #Loading the intent's parameters and the action to be performed.
    with open(path) as fil:
        dat = json.load(fil)
        intent = dat[intent]
        return Intent(intent['intentname'],intent['Parameters'], intent['actions'])

def intentIdentifier(clean_input, context,current_intent):
    #Identifying the intent to be performed with the help of ngram match
    clean_input = clean_input.lower()
    #ngram match algorithm which gives a score of how close the user input matches with each intents available.
    scores = ngrammatch(clean_input)
    #choosing here the intent with the highest score
    scores = sorted_by_second = sorted(scores, key=lambda tup: tup[1])

    if(current_intent==None):
        #primary keys for determining the action
        restaurant_keyword = ['restaurant', 'food court','cafe','hotel','dining room','canteen','eatery','hungry']
        vegetables_keyword = ['vegetables','vegetable','fruit','fruits','leafy']
        #with the help of a few straigtforward keywords from user input the intent is directly matched.
        for i in range(len(restaurant_keyword)):
            if(restaurant_keyword[i] in clean_input):
                return loadIntent('params/newparams.cfg', 'BookRestaurant')
        for i in range(len(vegetables_keyword)):
            if(vegetables_keyword[i] in clean_input):
                return loadIntent('params/newparams.cfg', 'BuyVegetables')
        else:
            #if no straigtforward keyword is found in userinput then ngramscore is used to decide up on the intent.
            if(scores[-1][1]>0.1):
                return loadIntent('params/newparams.cfg',scores[-1][0])
            else: 
                return None
    else:
        #If current intent is not none, stick with the ongoing intent
        return current_intent

def getattributes(uinput,context,attributes):
    '''This function marks the entities in user input, and updates
    the attributes dictionary'''
    #Making sure the intent is not complete inorder to check for attributes in user input.
    if context.name.startswith('IntentComplete'):
        return attributes, uinput
    else:
        #Loading the all possible attribute values from intities folder.
        files = os.listdir('./entities/')
        entities = {}
        for fil in files:
            lines = open('./entities/'+fil).readlines()
            for i, line in enumerate(lines):
                lines[i] = line[:-1]
            entities[fil[:-4]] = '|'.join(lines)

        #Extract entity from user input and update it in attributes dictionary.
        for entity in entities:
            for i in entities[entity].split('|'):
                if i.lower() in uinput.lower():
                    attributes[entity] = i
    
        #Replacing the entity values in userinput with placeholder value to later use it for ngrammatch
        for entity in entities:
                uinput = re.sub(entities[entity],r'$'+entity,uinput,flags=re.IGNORECASE)


    return attributes, uinput
    
class Session:
    def __init__(self, attributes=None):
        
        '''Initialise a default session'''
        #Contexts are to control dialogue flow    
        self.context = FirstGreeting()
        
        #Intent tracks the current state of dialogue
        self.current_intent = None
        
        #attributes hold the information collected over the conversation
        self.attributes = {}
        

    def reply(self, user_input):
        '''Generate response to user input'''
        #collecting attributes from user input
        self.attributes, clean_input = input_processor(user_input, self.context, self.attributes, self.current_intent)
        
        #Identified intent
        self.current_intent = intentIdentifier(clean_input, self.context, self.current_intent)
        
        if self.current_intent == None:
            self.context = CannotIdentifyIntent()
            
        #prompting the user for the required attributes to complete the intent 
        prompt, self.context = check_required_params(self.current_intent, self.attributes, self.context)

        if self.context.name=='CannotIdentifyIntent':
            self.context = FirstGreeting()
        
        #prompt being None means all parameters satisfied, perform the intent action
        if prompt is None:
            if self.context.name!='IntentComplete':
                prompt, self.context = check_actions(self.current_intent, self.attributes, self.context)
                
        #Resets the state after the Intent is complete
        if self.context.name=='IntentComplete':
            self.attributes = {}
            self.context = FirstGreeting()
            self.current_intent = None
        return prompt


session = Session()
print ('BOT: Hi! How may I assist you?')
time.sleep(.5)
while True:
    inp = input('User: ')
    if (inp == 'exit'):
        print('Thanks! Have a nice day')
        break
    prompt= session.reply(inp)
    print ('BOT:', prompt)