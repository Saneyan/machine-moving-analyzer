# -*- coding: utf-8 -*-
#
#                       Machine Tracking Analyzer
#        Authored by TADOKORO Saneyuki <saneyan@gfunction.com>
# 

import re
import sys
import csv
import time
from datetime import datetime
from operator import itemgetter

# If you don't want to output logs, make debug 'False'.
#debug = True
debug = False

# Print debug message
def __(input):
    if debug is True: print(input)
    return input

def _(input):
    print(input)
    return input
    
def argv(args):
    __('Arguments: %s' % args)
    
    if len(args) != 3 or not re.search('^(id|date|all)$', args[1]) or not re.search('\.csv$', args[2]):
        heredoc()
        sys.exit(1)
        
    return { 'format': args[1], 'input': args[2] }
    
def heredoc():
    print '''
Machine Moving Analyzer
Usage:
    python analyze.py <format> <input_file>.csv

<format> should be 'id' for each ID, 'date' for each date or 'all' for all data.

If the <format> is 'id', all data are created in the 'by_id' directory.
For 'date' created in 'by_date' and for 'all' created in 'by_all' directory.
    
The input file must be CSV file containing 'ONDate', 'ONTime', 'OFFDate',
'OFFTime', 'endX' and 'endY' header and the data. This script outputs results as
a CSV file containing 'date', 'time', 'endX' and 'endY' header and the data.
'''

class CSVReader:
    
    acceptColumns = ['ONDate', 'ONTime', 'OFFDate', 'OFFTime', 'endX', 'endY', 'ID']
    
    reader = None
    header = None
    __fp = None
    
    def __init__(self, file):
        self.__file = file
    
    def __del__(self):
        if (self.__fp):
            self.__fp.close()
            __('Reader closes a file.')
        
    def __iter__(self):
        return self
        
    def next(self):
        if (not self.__fp):
            self.__fp = open(self.__file, 'rU')
            self.reader = csv.reader(self.__fp,)
            __('Reader opens a file.')
            
        n = next(self.reader)
        
        if (n is None):
            raise StopIteration
            
        if (not self.header):
            self.header = self.createColumnIndex(n)
            n = next(self.reader)
            
        r = {}
        
        for c in self.acceptColumns:
            r[c] = n[self.header[c]]
                
        return r

    def hasColumn(self, name):
        return name in self.acceptColumns
        
    # Create column index from header row
    def createColumnIndex(self, header):
    	c = {}
    	for i in range(0, len(header)):
    		if header[i] in self.acceptColumns:
    			c[header[i]] = i
    	return c

class CSVStore:
    
    writtenColumns = ['id', 'date', 'time', 'endX', 'endY']
    
    headerMarked = False
    lastList = None
    
    def __init__(self, file):
        self.__file = file
    
    def update(self, list):
        fp = open(self.__file, 'a')
        writer = csv.writer(fp, lineterminator = '\n')
        __('Writer opens a file.')
            
        if (self.headerMarked == False):
            writer.writerow(self.writtenColumns)
            self.headerMarked = True
            __('Writer marked the header.')
           
        
        #if (self.lastList is None or (self.lastList[1] != list[1] and self.lastList[2] != list[2])):
        writer.writerow(list)
        self.lastList = list
        fp.close()
        __('Writer closes a file.')

class CSVRepository:

    __cache = []
    __reader = None
    __store = None

    # Set CSV reading driver
    def setReader(self, reader):
        self.__cache = []
        self.__reader = reader

    # Set CSV writing driver
    def setStore(self, store):
        self.__store = store

    def findAll(self):
        self.__cacheData()
        result = []

        for data in self.__cache:
            result.append(data)

        return result

    def findAllUniqueBy(self, name):
        if not self.__reader.hasColumn(name):
            raise RuntimeError('There is no such a column \'%s\'' % name)

        self.__cacheData()
        result = []

        for data in self.__cache:
            if not data[name] in result:
                result.append(data[name])

        return result

    def findAllMatchedBy(self, name, value):
        if not self.__reader.hasColumn(name):
            raise RuntimeError('There is no such a column \'%s\'' % name)

        self.__cacheData()
        result = []

        for data in self.__cache:
            if data[name] == value:
                result.append(data)

        return result

    def add(self, data):
        if not self.__store:
            raise RuntimeError('Store is not set.')

        self.__store.update(data)

    def __cacheData(self):
        if self.__reader is None:
            raise RuntimeError('Reader is not set.')

        if len(self.__cache) == 0:
            for data in self.__reader:
                self.__cache.append(data)

class CSVModel:

    __repo = None

    def __init__(self, repo):
        self.__repo = repo
        self.__currentDate = None
        self.__currentData = None

    def getIds(self):
        return self.__repo.findAllUniqueBy('ID')

    def getData(self):
        return self.__repo.findAll()

    def getDataById(self, id):
        return self.__repo.findAllMatchedBy('ID', id)

    def update(self, data):
        currentDate = data[1] + data[2]

        if (self.__currentDate is None):
            self.__currentDate = currentDate
            self.__currentData = data
        elif (self.__currentDate != currentDate):
            self.__repo.add(self.__currentData)
            self.__currentDate = currentDate
            self.__currentData = data
        else:
            self.__currentData = data

class Resolver:

    __data = None
    __callback = None

    def __init__(self, data): 
        self.__data = data
    
    def resolve(self, callback):
        self.__callback = callback

        startTime = None
        endTime = None
        point = (None, None)
        
        for row in self.__data:
            __('-- start --')
            startTime = self.parseDate(row['ONDate'] + ' ' + row['ONTime'])
            
            if endTime is not None:
                self.fillDateOnStop(row['ID'], endTime, startTime, point)
            
            __('-- end --')
            endTime = self.parseDate(row['OFFDate'] + ' ' + row['OFFTime'])
            
            point = (row['endX'], row['endY'])
            
            __('-- fill --')
            self.fillDateOnMove(row['ID'], startTime, endTime, point)
            
            __('==> (x, y): (%s, %s)' % (row['endX'], row['endY']))
        
        self.update(row['ID'], endTime['start'] + 3599, point)
            
    # Parse date to second.
    #
    # If a machine have been moving in the following time:
    #
    # 00:01 (1s) |----------*====*-------| 01:00 (3600s)
    #                       ^
    #                    [target]
    #
    # [target]: 00:30 (1800s)
    # ==> To calculate begin time: [start] = [target] - [target] % 3600 + 1
    # ==> To calculate end time: [end] = [start] + 3599
    def parseDate(self, date):
        t = {}
        
        # Parse datetime to seconds
        x = t['time'] = int(time.mktime(time.strptime(date, '%Y/%m/%d %H:%M:%S')))
        # Calculate begin time
        y = t['start'] = x - x % 3600 + 1
        # Calculate end time
        t['end'] = y + 3599
        
        __(datetime.fromtimestamp(t['start']))
        __(datetime.fromtimestamp(t['end']))
        
        return t
    
    def fillDateOnStop(self, id, endTime, startTime, endPoint):
        previousEndTime = startTime['start'] - 1
        diff = previousEndTime - endTime['end']

        if diff >= 3600:
            for i in range(endTime['start'] - 1, previousEndTime, 3600):
                self.update(id, i, endPoint)
        else:
            self.update(id, endTime['start'] - 1, endPoint)

        self.update(id, previousEndTime, endPoint)
        
    def fillDateOnMove(self, id, startTime, endTime, endPoint):
        lastMovingTime = endTime['end'] - 1
        diff = lastMovingTime - startTime['start'];
        
        if diff >= 3600 * 2:
            for i in range(startTime['start'] + 3600, lastMovingTime, 3600):
                self.update(id, i - 1, (None, None))
        
    def update(self, id, second, endPoint):
        timestamp = datetime.fromtimestamp(second)
        self.__callback([
            id,
            timestamp.strftime('%Y/%m/%d'),
            timestamp.strftime('%H:%M:%S'),
            endPoint[0] or 'no answer',
            endPoint[1] or 'no answer'])

class Writer:
    def __init__(self):
        self.models = {}
        self.extension = '.csv'
        self.directory = ''

    def createModel(self, name):
        repo = CSVRepository()
        repo.setStore(CSVStore(self.directory + name + self.extension))
        self.models[name] = CSVModel(repo)

class IdWriter(Writer):
    def __init__(self):
        Writer.__init__(self)
        self.directory = 'by_id/'

    def update(self, data):
        name = data[0]

        if name not in self.models:
            self.createModel(name)

        model = self.models[name]
        model.update(data)

class DateWriter(Writer):
    def __init__(self):
        Writer.__init__(self)
        self.directory = 'by_date/'

    def update(self, data):
        name = data[1].replace('/', '_') + '_' + data[2].replace(':', '_')

        if name not in self.models:
            self.createModel(name)

        model = self.models[name]
        model.update(data)

class AllWriter(Writer):
    def __init__(self):
        Writer.__init__(self)
        self.directory = 'by_all/'
        self.createModel('all')

    def update(self, data):
        self.models['all'].update(data)

if (__name__ == '__main__'):
    param = argv(sys.argv)

    repo = CSVRepository()
    repo.setReader(CSVReader(param['input']))

    model = CSVModel(repo)

    __("Finding IDs...")

    ids = model.getIds()
    __("%d IDs are found: %s" % (len(ids), ids))

    __("Start resolving...")

    if param['format'] == 'id':
        idWriter = IdWriter()
        for id in ids:
            data = model.getDataById(id)
            Resolver(data).resolve(lambda data: idWriter.update(__(data)))
    elif param['format'] == 'date':
        dateWriter = DateWriter()
        for id in ids:
            data = model.getDataById(id)
            Resolver(data).resolve(lambda data: dateWriter.update(__(data)))
    elif param['format'] == 'all':
        allWriter = AllWriter()
        data = model.getData()
        Resolver(data).resolve(lambda data: allWriter.update(__(data)))

    __("Done!")

