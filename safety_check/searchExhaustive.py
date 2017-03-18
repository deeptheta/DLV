#!/usr/bin/env python

"""
A data structure for organising search

author: Xiaowei Huang
"""

import numpy as np
import time
import os
import copy

from configuration import *
from regionSynth import initialiseRegion, initialiseRegions

class searchExhaustive:


    # used to store historical images, spans and numSpans
    # a pair (i,p) is used to represent the index i of the current 
    #  node and its parent node p
    # numDimsToMani records the number of features to be manipulated

    def __init__(self, image, k):
        self.images = {}
        self.spans = {}
        self.numSpans = {}
        self.numDimsToManis = {}
        self.steps = {}
        self.cost = {}
        
        # the layer currently working on 
        self.maxilayer = k 
        
        # a list of input elements that have been manipulated 
        # we try to avoid update these again
        self.manipulated = {}
        self.manipulated[(-1,-1)] = {}
        for i in range(-1,k+1):
            self.manipulated[(-1,-1)][i] = []
                    
        # initialisse
        self.images[(-1,-1)] = image
        self.visitedImages = []

        # a queue to be processed first in first out
        self.rk = []
        # the image that is currently processing
        self.crk = (-1,-1)
        
    def destructor(self): 
        self.images = {}
        self.spans = {}
        self.numSpans = {}
        self.numDimsToManis = {}
        self.steps = {}
        self.cost = {}
        self.manipulated = {}
        self.images[(-1,-1)] = []
        self.rk = []    
        self.visitedImages = []
    
        
    def emptyQueue(self):
        return len(self.rk) == 0 
                
    def size(self):
        return len(self.rk) 
                
    def getOneUnexplored(self):
        #print self.cost
        #print min(self.cost, key=self.cost.get)
        if len(self.rk) > 0: 
            return min(self.cost, key=self.cost.get)
        else: return (-1,-1)
        
    def addVisitedImage(self,image):
        self.visitedImages.append(image)
        
    def hasVisited(self,image):
        for image2 in self.visitedImages: 
            if np.array_equal(image,image2): return True
        return False
    
    def getInfo(self,index):
        return (copy.deepcopy(self.images[index]),self.spans[index],self.numSpans[index],self.numDimsToManis[index],self.steps[index])

    def addIntermediateNode(self,image,span,numSpan,cp,numDimsToMani,index):
        index = (index[0]+1,index[0])
        self.images[index] = image
        self.spans[index] = span
        self.numSpans[index] = numSpan
        self.numDimsToManis[index] = numDimsToMani
        return index
        
    def addImages(self,model,parentIndex,ims,manipulatedDims,stepsUpToNow):
        inds = [ i for (i,j) in self.images.keys() if j == -1 ]
        index = max(inds) + 1
        for (image,conf) in ims: 
            for (span,numSpan,nn) in initialiseRegions(model,image,self.manipulated[parentIndex][-1]):
                self.images[(index,-1)] = image
                self.spans[(index,-1)] = span
                self.numSpans[(index,-1)] = numSpan
                self.numDimsToManis[(index,-1)] = nn
                self.cost[(index,-1)] = conf
                self.steps[(index,-1)] = stepsUpToNow
                self.rk.append((index,-1))
                self.manipulated[(index,-1)] = {}
                # -1 for the historical manipulated dimensions up to now
                # 0 for the dimensions to be manipulated
                self.manipulated[(index,-1)][-1] = manipulatedDims
                self.manipulated[(index,-1)][0] = span.keys()
                for i in range(1,self.maxilayer+1):
                    self.manipulated[(index,-1)][i] = []
                index += 1            
            
        removeNum = len(self.rk) - maxQueueSize
        while removeNum > 0:  
            maxind = max(self.cost, key=self.cost.get)
            #print "%s--%s--%s"%(removeNum,maxind,len(self.rk))
            self.removeNode(maxind)
            #self.rk.remove(maxind)
            removeNum -= 1
            
        #print("0--%s--%s"%(sorted(self.rk),sorted(self.spans.keys())))
        newParentIndex = parentIndex
        i = 0 
        indices = copy.deepcopy(sorted(self.spans.keys()))
        for index2 in indices: 
            if index2[0] > i: 
                self.copyEntry((i,-1),index2)
                self.removeNode(index2)
                if index2 == parentIndex : newParentIndex = (i,-1)
            i += 1
        #print("1--%s--%s"%(sorted(self.rk),sorted(self.spans.keys())))        
        return newParentIndex


    # copy entry from index2 to index1
    def copyEntry(self,index1,index2):
        self.images[index1] = self.images[index2]
        self.spans[index1] = self.spans[index2]
        self.numSpans[index1] = self.numSpans[index2]
        self.numDimsToManis[index1] = self.numDimsToManis[index2]
        self.cost[index1] = self.cost[index2]
        self.steps[index1] = self.steps[index2]
        self.manipulated[index1] = self.manipulated[index2]
        self.rk.append(index1)
            
    def addManipulated(self,index,k,s):
        self.manipulated[index][k] = list(set(self.manipulated[index][k] + s))
            
    def removeProcessed(self,index):
        children = [ (k,p) for (k,p) in self.spans.keys() if p == index[0] ]
        for childIndex in children:  
            self.removeProcessed(childIndex)
        if index in self.rk: self.removeNode(index)
                
    def removeNode(self,index):
        self.images.pop(index,None)
        del self.spans[index]
        del self.numSpans[index]
        del self.numDimsToManis[index]
        self.cost.pop(index,None)
        self.steps.pop(index,None)
        self.rk.remove(index)
        self.manipulated.pop(index,None)
