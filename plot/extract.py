#!/usr/bin/python
import sys
import csv
import os.path
from operator import itemgetter

import re
import matplotlib as mplt

if sys.argv[1] == "plot":
    mplt.use('pgf')

import matplotlib.pyplot as plt
import numpy as np
import itertools
import operator as op

import pandas as pd
import pprint

class DataReader:

    tptp = {}
    configs = []
    

    def loadTptp(self, version):
        filename = os.path.join('TPTP-v' + version, 'higherOrderStatus.csv')
        with open(filename, 'rb') as csvfile:
            
            tptp = {(line[0].split('/'))[-1] : line[1] for line in csv.reader(csvfile, skipinitialspace=True) }
            self.tptp[version] =  tptp

    def _describe_config(self, config):
        with open(os.path.join(config, 'config.sh')) as f:
            content = f.read()
            vregex = "^LEO_VERSION=(git|release)-(?P<leov>.+?)(-metrics)?$" 
            match = re.search(vregex, content, re.M)
            leoversion = match.group('leov')
            
            if not match:
                return "inavlid"
            
            if leoversion == "release":
                leoversion = "1.6"

            leoversion = leoversion.replace('-nm', ' modified ')
            
                
            foregex = "FO_PROVERS=\((?P<provers>.+)\)"
            match = re.search(foregex, content)

            if not match:
                foprover = "unkown subprover"
            else:
                regex = "\"([^\"]+)\""
                l = re.findall(regex, match.group('provers'))
                foprover = ', '.join(map(lambda s: s.lower(), l))

            if len(l) == 3:
                return "LEO %s (multiple provers)" % (leoversion)
            
            return "LEO %s (%s)" % (leoversion, foprover)


    
    def read(self, directory):
        filename = os.path.join(directory, 'summary.csv')
        configstr = self._describe_config(directory)
        
        if not configstr in self.configs:
            self.configs.append(configstr)

        with open(filename,'rb') as csvfile:
            reader = csv.DictReader(csvfile, skipinitialspace=True)
            lines = []

            for line in reader:
                line['domain'] = line['problem'][0:3]
    
                for name in ['timers', 'counters' ]:     

                    if not line[name]:
                        break

                    parser = float if name == 'timers' else int
                    objs = line[name].split('|')

                    for strobj in objs:
                        objname, value = strobj.split(':')
                        line[name + '.' + objname] = parser(value)
                        
                line['realtime'] = float(line['realtime'])
                line['usertime'] = float(line['usertime'])
                line['return'] = int(line['return'])
                del line['timers']
                del line['counters']

                # TODO: remove hadrcoded tcp version
                line['expected'] = self.tptp['5.5.0'][line['problem']]
                line['config']  = configstr

                lines.append(line)
            return lines

    def read_all(self, directories):

        ret = []
        
        for directory in directories:
            ret.extend(self.read(directory))
        
        return ret




def style_barchart(plot):
    plot.legend().title=""

    plot.xaxis.grid(False)
    plot.yaxis.grid(True)
    plot.yaxis.set_zorder(3)
    plot.yaxis.linestyle = 'solid'
    plot.grid(axis = 'y', color ='white', linestyle='-')    

def pre1(df):

    timers = {
        "timers.mainloop.calculus" : "execute calculus rules",
        "timers.mainloop.checktime" : "checkin time left",
        "timers.mainloop.lightes" : "compute lightest clause",
        "timers.mainloop.subpover" : "call subprover",
        "timers.mainloop.subsumed" : "check subsumtion",
        "timers.mainloop.updatesets" : "updating clause set"
        }

    df = df[ df['config'].isin(['LEO 1.6 (e-1.8)'])]

    # fix problem names for latex
    df['problem'] = df['problem'].apply(lambda s: s.replace("^", "\^{}"))
    td = df.groupby('problem')[timers.keys()].mean()
    td = td[ (td['timers.mainloop.subpover'] > 2) & (td['timers.mainloop.calculus'] > 2) ]
    td.rename(columns=timers, inplace=True)
    plot = td.tail(20).plot(kind='bar', stacked=True)
    plot.set_ylim([0, 45])
    style_barchart(plot)
    return


def pre2(df):

    # only applicaable configs
    df = df[ df['config'].isin(['LEO 1.6 (e-1.8)', 'LEO 1.6 (vampire-3.0)'])]

    domaincounts = df.groupby('domain')['domain'].count()

    df = df[ df['category'] == 'Solved']
    df = df[['config','domain']]

    g = df.groupby(['config', 'domain'])['domain'].count() 

    # create relative values
    g =  g.astype(float).div(domaincounts, level='domain')
    res =  g.unstack().transpose()
    plot = res.plot(kind='bar')

    plot.set_ylabel("ratio of solved problems")
    plot.set_xlabel("domains")
    plot.set_ylim([0,1.1])
    style_barchart(plot)
    return plot


def these2a(df):

    df = df[ df['expected'] != 'Open' ]
    cor = df[['domain', 'config', 'category']]
    a = cor.groupby(['config','category'])['category'].count()
    b = a.unstack('config')
    plot = b.plot(kind='bar')

    style_barchart(plot)
    return plot

def these2b(df, reference_conf, others):

    df = df[ (df['category'] == 'Solved') ]

    # select median of each problem
    aggregated = df.groupby(['config', 'problem'])['realtime'].median()
    reftime = aggregated[reference_conf]
    groups = reftime.apply(lambda x: "%d to %d seconds" % ((x//10)*10,((x//10)+1)*10))

    # reference_name = describe_config(reference_conf)
    for key in others:

        print "using %s as baseline for %s" % (reference_conf, key)

        run = aggregated.ix[key]
        run = pd.DataFrame(run)
        
        print run
        print reftime

        run["ref.time"] = reftime
        run["ref.group"] = groups
        run["ref.delta"] = run['realtime'] - run['ref.time']

        run = run.dropna()
        run = run.sort("ref.delta")

        plot = run.boxplot(['ref.delta'], by='ref.group')

        print "Total delta", run['ref.delta'].sum()

#        run['ref.deltafaktor'] = run['realtime'] / run['ref.time']
#        print run['ref.delta'].sum()
#        run[run['ref.delta'] <= 0].hist("ref.deltafaktor")


    return plot

def these4(df, configs):    
    df['problem'] = df['problem'].apply(lambda s: s.replace("^", "\^{}"))
    agg = df.groupby(['config','problem'])[['realtime', 'usertime', 'category']].max()


    ref = agg.ix[configs[0]]
    df  = agg.ix[configs[1]]

    data = pd.DataFrame({ configs[1] : df['usertime']})
    data[configs[0]] = ref['usertime']
    data = data[df['category'] == ref['category']]
    data.sort(configs[0]).plot(kind='scatter')
    
    print (data[configs[0]] - data[configs[1]]).sum()



def visualize_groups(df, config):

    df = df[(df['config'] == config) & ((df['category'] == "Timeout") |(df['category'] == "Solved") | (df['category'] == 'Unsolved'))]
    df['realtime'] = df['realtime']
    df.hist('realtime', by=df['category'])
    plt.show()


def movements(df, confs):
    df = df[ df['config'].isin(confs)]
    states = df.groupby(['config', 'problem'])['category'].max()
    states = states.unstack(level='config').reset_index().groupby(confs)['problem'].count()
    states = states.unstack(level=confs[0])
    print states
    return states.plot(kind='barh')

def analyze_failed(df,configs):

    states = df.groupby(['config', 'problem']).max()
    reference = states.xs(configs[0])
    
    for key in configs[1:]:
        run = states.xs(key)
        
        run['group'] = reference['realtime'].apply(lambda x: x//1)
        run['ref.category']  = reference['category']
        run =  run[run['ref.category'] == 'Solved']
        run['changed'] = (run['category'] == run['ref.category'])
        
        s = run.groupby(['group', 'changed'])['changed'].count()
        cats = run.groupby('group')['group'].count()
        #    s = s.mul(100, level='group').div(cats, level='group')
        s = s.unstack(level='changed')
        print s
        s.ix['True'].plot(kind='bar')

def categorize(entry):

    if entry['status'] == 'Timeout':
        category = 'Timeout'
    elif entry['expected'] == 'Unknown' or entry['expected'] == 'Open':
        if entry['status'] == 'Unknown':
            category = 'Unknown'
        elif entry['status'] == 'Error':
            category = 'Aborted'
        else:
            category = 'No proof'
    elif entry['status'] == 'Unknown' or entry['status'] == 'Error':
        category = 'Aborted'
    elif entry['expected'] == entry['status']:
        category = 'Solved'        
    else:
        category = 'Error'
        
    return category


def compare_metrics(df):

    timers = {
        "timers.mainloop.calculus" : "execute calculus rules",
        "timers.mainloop.checktime" : "checkin time left",
        "timers.mainloop.lightes" : "compute lightest clause",
        "timers.mainloop.subpover" : "call subprover",
        "timers.mainloop.subsumed" : "check subsumtion",
        "timers.mainloop.updatesets" : "updating clause set"
        }
    
    keys = timers.keys()
    keys.append('category')


    times = df[keys].groupby('category').sum()
    total = times.sum(axis=1)
    times = times.div(total, axis='index').drop('Timeout')
    

    times.rename(columns=timers, inplace=True)
    plot = times.plot(kind='bar', stacked=True)
    plot.set_ylim((0,1.1))
    plot.set_xlim((0,5))
    plot.legend(loc='right')

#    df['timers.mainloop.subpover'].hist()

def asd(df, configs):

    print df
    df['problem'] = df['problem'].apply(lambda s: s.replace("^", "\^{}"))
    agg = df.groupby(['config','problem'])[['realtime', 'usertime', 'category','timers.mainloop.subpover','counters.mainloop.entry']].max()


    ref = agg.ix[configs[0]]
    df  = agg.ix[configs[1]]

    data = pd.DataFrame({ "delta" : df['realtime']  - ref['realtime']  })
    data['timers.mainloop.subpover'] = ref['timers.mainloop.subpover']
    data['counters.mainloop.entry'] = ref['counters.mainloop.entry']
    data.sort('delta').plot(y='delta',x='counters.mainloop.entry')
    
#    print (data[configs[0]] - data[configs[1]]).sum()



    

if __name__ == "__main__":

    colors = [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442",
        "#0072B2", "#D55E00", "#CC79A7"
    ]
    
    if sys.argv[1] == "plot":
        candidates = sys.argv[2:]
    else:
        candidates = sys.argv[1:]

    dr = DataReader()
    dr.loadTptp('5.5.0')
    data = dr.read_all(candidates)
    print dr.configs
    df = pd.DataFrame(data)

    
    df['category'] = df.apply(categorize, axis=1)



#    these2a(df)
#    these2b(df, dr.configs[0], dr.configs[1:])

#    these3a(df)
#    these3b(df, dr.configs[0], dr.configs[1:])


#    pre1(df)
#    per2(df)
#    visualize_groups(df, sys.argv[1])
#    analyze_failed(df, dr.configs)
    movements(df, dr.configs)
#    compare_metrics(df)

#    these4(df, dr.configs)
#    asd(df, dr.configs)

    plt.show()
    plt.savefig('file.pgf')
   
        





            

    
 

