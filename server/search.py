#assuming database is filled, and somebody is searching for a song by lyrics
#query database with the lyrics the user input, based on search algorithm
#return song names that match

import re
import regex
import gc
import sys
import copy
import nltk
import math
import bson
import pickle
import os.path

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

from collections import defaultdict
from array import array
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from functools import reduce
from pymongo import MongoClient
from os import path

class Search:

    def __init__(self):
        self.index = defaultdict(list)    #the inverted index {'word': [[1,[0,2]],[2,[3,4]],[3,[2,7]]]}
        self.stop_words = set(stopwords.words('english'))   #stopwords set (and, the, a, an etc)
        self.lemmatizer = WordNetLemmatizer()   #initiating the lemmatizer. Eg:- car/cars will be reduced to car
        self.client = MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
        self.db = self.client["MusicDataset"]
        self.songIndex = self.db["index"]
        self.songInfo = self.db["songInfo"]
        self.numSongs = 0
        self.tf=defaultdict(list)          #term frequencies of terms in documents
        self.df=defaultdict(int)           #document frequencies of terms in the corpus
        self.idf=defaultdict(float)        #inverse document frequencies of terms in the corpus

    #----------------------------------------------------------------------------------------------------------------------
    #Creating Inverted index code starts ----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------------------

    def parseSongsFromDB(self):
        ''' returns the id, title, lyrics etc of the entire collection '''
        #collFile=open("testCollection.dat",'r', encoding="utf8") #replace with mongoDB call to fetch all songs
        #skip call if index already exists in DB
        print("Reading songs from MongoDB")
        songs=[]
        for song in self.songInfo.find():
            d={}
            d['id']=song['_id']
            d['title']=song['title']
            d['lyrics']=song['lyrics']
            d['artist']=song['artist']
            d['album']=song['album']
            songs.append(d)
            
        return songs        #[{'id':1, 'title':'What I've Done', 'lyrics':'....', etc.},{},..]
    
    def getWords(self, data):
        '''data preprocessing-convert to lower case, remove non-alphanumeric chars, remove stopwords, lemmatize'''
        data = data.lower()
        data = re.sub(r'[^a-z0-9 ]',' ',data) #put spaces instead of non-alphanumeric characters
        data_tokens = word_tokenize(data)   # splitting given data in individual words
        data = [w for w in data_tokens if not w in self.stop_words]     # filtering out stopwords
        data = [self.lemmatizer.lemmatize(w) for w in data]     #lemmatization
        return data
    
    def writeIndexToDB(self):
        '''write the inverted index to the MongoDB'''
        f=open("indexFile.txt", 'w')
        print(self.numSongs,file=f)
        self.numSongs=float(self.numSongs)
        for term in self.index.keys():
            postinglist=[]
            for p in self.index[term]:
                docID=p[0]
                positions=p[1]
                postinglist.append(':'.join([str(docID) ,','.join(map(str,positions))]))
            #print data
            postingData=';'.join(postinglist)
            tfData=','.join(map(str,self.tf[term]))
            idfData='%.4f' % (self.numSongs/self.df[term])
            print('|'.join((term, postingData, tfData, idfData)),file=f)   
        f.close()
        #self.songIndex.insert(self.index)
        #self.songIndex.remove( { } )
        #for term in self.index.keys():
        #    item = {}
        #    item[term] = bson.Binary(pickle.dumps(self.index[term], protocol=2))
        #    self.songIndex.insert_one(item)

    def readIndex(self):
        #read main index
        f=open("indexFile.txt", 'r');
        #first read the number of documents
        self.numSongs=int(f.readline().rstrip())
        for line in f:
            line=line.rstrip()
            term, postings, tf, idf = line.split('|')    #term='termID', postings='docID1:pos1,pos2;docID2:pos1,pos2'
            postings=postings.split(';')        #postings=['docId1:pos1,pos2','docID2:pos1,pos2']
            postings=[x.split(':') for x in postings] #postings=[['docId1', 'pos1,pos2'], ['docID2', 'pos1,pos2']]
            postings=[ [str(x[0]), map(int, x[1].split(','))] for x in postings ]   #final postings list  
            self.index[term]=postings
            #read term frequencies
            tf=tf.split(',')
            self.tf[term]=list(map(float, tf))
            #read inverse document frequency
            self.idf[term]=float(idf)
        f.close()


    def createIndex(self):
        '''Creates the inverted index - mapping from words(of song data) to song element. Given a search query (single/multi word), 
        it will return the song entries associated with that query'''

        if path.exists("indexFile.txt"):
            print("Index exists, reading existing index.")
            self.readIndex()
        else:
            print("Index doesn't exist, creating it.")

            songDictArray = self.parseSongsFromDB()  #mongoDB API call to load all song entries in the dictionary

            for songDict in songDictArray:
                #garbage collection
                gc.disable()

                if songDict != {}:
                    songId = str(songDict['id'])
                    songData ='\n'.join((songDict['title'],songDict['lyrics'],songDict['artist'],songDict['album']))
                    songTokenize = self.getWords(songData)

                    self.numSongs += 1

                    #build index for the current song element
                    songItem = {}
                    for position, word in enumerate(songTokenize):
                        try:
                            songItem[word][1].append(position)
                        except:
                            songItem[word]=[songId, array('I',[position])]  #{"word":[id, [pos list]]}
                    
                    #normalize the document vector
                    norm=0
                    for word, index in songItem.items():
                        norm+=len(index[1])**2      #length of pos list squared for every word
                    norm=math.sqrt(norm)
                    
                    #calculate the tf and df weights
                    for word, index in songItem.items():
                        self.tf[word].append(round((len(index[1])/norm),4))     #list of tfs for every word (in dfs where it occurs)
                        self.df[word]+=1
                
                    #merge the current song item to the main index
                    for word, index in songItem.items():
                        self.index[word].append(index)

                gc.enable()
            
            #storing idf data
            for term in self.index.keys():
                self.idf[term] = round((self.numSongs/self.df[term]),4)         #idf calculated for every word in index

            #store the index back to mongo db
            self.writeIndexToDB()
            print("Index saved to Disk")
    
    #----------------------------------------------------------------------------------------------------------------------
    #Querying Inverted index code starts ----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------------------

    def dotProduct(self, vec1, vec2):
        if len(vec1)!=len(vec2):
            return 0
        return sum([ x*y for x,y in zip(vec1,vec2) ])
    
    def getPostings(self, terms):
        #all terms in the list are guaranteed to be in the index
        return [ self.index[term] for term in terms ]
    
    def getSongsFromPostings(self, postings):
        #no empty list in postings
        return [ [x[0] for x in p] for p in postings ]

    def intersectLists(self,lists):
        if len(lists)==0:
            return []
        #start intersecting from the smaller list
        lists.sort(key=len)
        return list(reduce(lambda x,y: set(x)&set(y),lists))
    
    def rankSongResults(self, terms, songIds):
        #term at a time evaluation
        songVectors=defaultdict(lambda: [0]*len(terms))     #{"songId":[list of the length of no. of query terms]}
                                                            # - dict length is total matching songIds
        queryVector=[0]*len(terms)              #list of the length of no. of query terms
        for termIndex, term in enumerate(terms):
            if term not in self.index:
                continue
            
            queryVector[termIndex]=self.idf[term]
            
            for songIndex, (songId, postings) in enumerate(self.index[term]):
                if songId in songIds:
                    songVectors[songId][termIndex]=self.tf[term][songIndex]
     
        #calculate the score of each song
        #queryVectorDim - 1 x terms (idf values)
        #songvectorDim - N_SongIds x terms (tf values for each songId)
        songScores=[ [self.dotProduct(curSongVec, queryVector), songId] for songId, curSongVec in songVectors.items() ]
        songScores.sort(reverse=True)
        rankedSongResults=[x[1] for x in songScores]
        return rankedSongResults        #returning songIds in descending order of ranking scores


    def owq(self,q):
        '''One Word Query'''
        originalQuery=q
        q=self.getWords(q)
        if len(q)==0:
            print('Invalid query')
            return []
        elif len(q)>1:
            return self.ftq(originalQuery)
        
        #q contains only 1 term 
        term=q[0]
        if term not in self.index:
            print('Query returned no match')
            return []
        else:
            p=self.index[term]
            p=[x[0] for x in p]
            return self.rankSongResults(q, p)
    
    def ftq(self,q):
        """Free Text Query"""
        q=self.getWords(q)
        if len(q)==0:
            print('Invalid query')
            return []
        
        li=set()
        for term in q:
            try:
                p=self.index[term]
                p=[x[0] for x in p]
                li=li|set(p)
            except:
                #term not in index
                pass
        
        if not li:
            print('Query returned no match')
            return []
        
        li=list(li)
        #li.sort()
        return self.rankSongResults(q, li)
    
    def pq(self,q):
        '''Phrase Query'''
        originalQuery=q
        q=self.getWords(q)
        if len(q)==0:
            print('Invalid query')
            return []
        elif len(q)==1:
            return self.owq(originalQuery)

        phraseSongResults=self.pqSongs(q)
        return self.rankSongResults(q, phraseSongResults)     
        
    def pqSongs(self, q):
        """ here q is not the query, it is the list of terms """
        #first find matching docs
        for term in q:
            if term not in self.index:
                #if any one term doesn't appear in the index, then unsuccessful match
                print('Query returned no match')
                return []
        
        postings=self.getPostings(q)    #all the terms in q are in the index
        songs=self.getSongsFromPostings(postings)
        #songs are the song items that contain every term in the query
        songs=self.intersectLists(songs)
        #postings are the postings list of the terms in the documents docs only
        for i in range(len(postings)):
            postings[i]=[x for x in postings[i] if x[0] in songs]
        
        #check whether the term ordering in the docs is like in the phrase query
        
        #subtract i from the ith terms location in the docs
        postings=copy.deepcopy(postings)    #this is important since we are going to modify the postings list
        
        for i in range(len(postings)):
            for j in range(len(postings[i])):
                postings[i][j][1]=[x-i for x in postings[i][j][1]]
        
        #intersect the locations
        result=[]
        for i in range(len(postings[0])):
            li=self.intersectLists( [x[i][1] for x in postings] )
            if li==[]:
                continue
            else:
                result.append(postings[0][i][0])    #append the docid to the result
        
        return result
    
    def queryType(self,q):
        if '"' in q:
            return 'PQ'                 #Phrased Query - "What I have done" (match all query words in order)
        elif len(q.split()) > 1:
            return 'FTQ'                #Free Test Query - What done (match any of the query words)
        else:
            return 'OWQ'                #One word Query - What (single word match)
    
    def queryIndex(self,query):
        qt=self.queryType(query)
        if qt=='OWQ':
            return self.owq(query)
        elif qt=='FTQ':
            return self.ftq(query)
        elif qt=='PQ':
            return self.pq(query)
        return


if __name__=="__main__":
    #http://www.ardendertat.com/2011/05/30/how-to-implement-a-search-engine-part-1-create-index/
    #http://www.ardendertat.com/2011/05/31/how-to-implement-a-search-engine-part-2-query-index/
    #http://www.ardendertat.com/2011/07/17/how-to-implement-a-search-engine-part-3-ranking-tf-idf/
    print("Loading Index...Please wait")
    obj=Search()
    obj.createIndex()
    print("Index loaded successfully")
    while True:
        print("Enter search query")
        q=sys.stdin.readline()
        if q=='':
            break
        results = obj.queryIndex(q)
        if results:
            #display results
            print(results)
