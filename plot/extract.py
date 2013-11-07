#!/usr/bin/python
import sys
import csv
import os.path
import inspect
from operator import itemgetter

import re
import matplotlib as mplt
from matplotlib import cm
mplt.use('pgf')

import matplotlib.pyplot as plt
from matplotlib import colors
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

#    plot.yaxis.set_zorder(3)
#    plot.grid(axis = 'y', color ='white', linestyle='-')
    plot.yaxis.linestyle = 'solid'


    
    return plot


def mainloop(df):

    timers = {
        "timers.mainloop.calculus" : "execute calculus rules",
        "timers.mainloop.checktime" : "checkin time left",
        "timers.mainloop.lightes" : "compute lightest clause",
        "timers.mainloop.subpover" : "call subprover",
        "timers.mainloop.subsumed" : "check subsumtion",
        "timers.mainloop.updatesets" : "updating clause set"
        }

    # fix problem names for latex
    df['problem'] = df['problem'].apply(lambda s: s.replace("^", "\^{}"))
    td = df.groupby('problem')[timers.keys()].mean()
    td = td[ (td['timers.mainloop.subpover'] > 2) & (td['timers.mainloop.calculus'] > 2) ]
    td.rename(columns=timers, inplace=True)
    plot = td.tail(20).plot(kind='bar', stacked=True)
    plot.set_ylim([0, 45])
    plot.xaxis.set_label_text("")
    style_barchart(plot)
    return plot


def pre3(df):

    print mplt.rcParams['axes.color_cycle']
    colorsn = mplt.rcParams['axes.color_cycle'][0:1]
    colorsn = colorsn + mplt.rcParams['axes.color_cycle'][3:4]
    altmap = colors.ListedColormap(colorsn)

    domaincounts = df.groupby('domain')['domain'].count()

    df = df[ df['category'] == 'Solved']
    df = df[['config','domain']]

    g = df.groupby(['config', 'domain'])['domain'].count() 

    # create relative values
    g =  g.astype(float).div(domaincounts, level='domain')
    res =  g.unstack().transpose()
    plot = res.plot(kind='bar', colormap=altmap)

    plot.set_ylabel("ratio of solved problems")
    plot.set_xlabel("domains")
    plot.set_ylim([0,1.1])
    style_barchart(plot)
    return plot


def counts(df):

    df = df[ df['expected'] != 'Open' ]
    cor = df[['domain', 'config', 'category']]
    a = cor.groupby(['config','category'])['category'].count()
    b = a.unstack('config')
    error =  pd.DataFrame({ 'category': ['Error'], 'LEO 1.6 (e-1.8)': [0]}).groupby('category').max()

    b = b.append(error)
   
    plot = b.plot(kind='bar')

    style_barchart(plot)
    return plot

def timedelta(df, configs):

    reference_conf, others = configs[0], configs[1:]
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
        
        run["ref.time"] = reftime
        run["ref.group"] = groups
        run["ref.delta"] = run['realtime'] - run['ref.time']

        run = run.dropna()
        run = run.sort("ref.delta")

        plot = run.boxplot(['ref.delta'], by='ref.group')

        print "Total delta", run['ref.delta'].sum()

        plot.xaxis.grid(False)
        plot.set_title("")
        plot.xaxis.set_label_text("time used by %s" % reference_conf)
        plot.yaxis.set_label_text("difference in s")
        plt.suptitle("")

#        run['ref.deltafaktor'] = run['realtime'] / run['ref.time']
#        print run['ref.delta'].sum()
#        run[run['ref.delta'] <= 0].hist("ref.deltafaktor")
    return plot

def thesis2a(df):
    return counts(df)

def thesis2b(df, configs):
    return timedelta(df, configs)

def thesis3a(df):
    return counts(df)

def thesis3b(df, configs):
    return timedelta(df, configs)

def pre2(df):
    colorsn = mplt.rcParams['axes.color_cycle'][0:1]
    colorsn = colorsn + mplt.rcParams['axes.color_cycle'][3:4]
    altmap = colors.ListedColormap(colorsn)

    df = df[ df['expected'] != 'Open' ]
    cor = df[['domain', 'config', 'category']]
    a = cor.groupby(['config','category'])['category'].count()
    b = a.unstack('config')
    plot = b.plot(kind='bar', colormap=altmap)

    style_barchart(plot)
    return plot


    

def thesis4(df, configs):    
    df['problem'] = df['problem'].apply(lambda s: s.replace("^", "\^{}"))

    agg = df.groupby(['config','problem'])[['realtime', 'usertime', 'category']].max()


    ref = agg.ix[configs[0]]
    df  = agg.ix[configs[1]]

    data = pd.DataFrame({ configs[1] : df['usertime']})
    data[configs[0]] = ref['usertime']
    data = data[df['category'] == ref['category']]
    data = data.sort(configs[0])
    data[configs].plot()

    print (data[configs[0]] - data[configs[1]]).sum()



def groupdistribution(df):
    df['category'] = df.category.apply(lambda x: " Solved" if x == "Solved" else "Others")  
    df.hist('realtime', by=df['category'])
    plt.show()


def movements(df, confs):
    df = df[ df['config'].isin(confs)]
    states = df.groupby(['config', 'problem'])['category'].max()
    states = states.unstack(level='config').reset_index().groupby(confs)['problem'].count()
    states = states.unstack(level=confs[0])    
    
    import matplotlib.sankey as sankey

    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

    axes = [ax1, ax2, ax3, ax4]
    cats = [ "Aborted", "Solved", "Timeout",  "Unknown"]

    states = states.fillna(0)
    print states

    for ax, cat in zip(axes,cats):

        data = states.ix[cat]
        values = []
        lables = []
        oris = []
        bla = -1

        for (index, val) in data.iteritems():
            lables.append(index)
            values.append(val)
            if index == cat:
                bla=1
                oris.append(0)
            else:
                oris.append(bla)


        lables.append('')
        values.append(-data.sum())
        oris.append(0)

        sankey.Sankey(ax=ax).add(
            flows = values,
            orientations = oris,
            trunklength = 1000,
            pathlengths = [ 500 ] * 5
            ).finish()
        

def analyse_failed(df,configs):

    states = df.groupby(['config', 'problem']).max()
    reference = states.xs(configs[0])
    
    for key in configs[1:]:
        run = states.xs(key)
        
        run['group'] = reference['realtime'].apply(lambda x: "%2d - %2d s" % ((x//5)*5, ((x//5) + 1)*5))
        run['ref.category'] = reference['category']
        run =  run[run['ref.category'] == 'Solved']
        run['changed'] = (run['category'] != run['ref.category'])
        
        f, (ax1, ax2) = plt.subplots(2)

        s = run.groupby(['group', 'changed'])['changed'].count()
        u = run.groupby(['expected', 'changed'])['changed'].count()
        cats = run.groupby('group')['group'].count()
        t = s.mul(1.0, level='group').div(cats, level='group')

        u = u.unstack(level='changed')
        t = t.unstack(level='changed')
        


        altmap = colors.ListedColormap(mplt.rcParams['axes.color_cycle'][1:])


        p2 = style_barchart(t[True].plot(kind='bar', ax=ax1, rot=0))


        br = run.groupby('expected')['expected'].count()
        u['Total'] = br 
        u = u[True].div(br)
        p3 = style_barchart(u.plot(kind='bar', ax=ax2, colormap=altmap, rot=0))

        p2.legend().set_visible(False)
        p3.legend().set_visible(False)

        p2.xaxis.set_label_text("")        
        p3.xaxis.set_label_text("")

        p2.set_ylim([0,1.1])
        p3.set_ylim([0,0.5])

        p2.set_title("by execution time")
        p3.set_title("by expected result")
        
        


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


def summainloop(df):

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

    return style_barchart(plot)

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
    plot = data.sort('delta').plot(y='delta',x='counters.mainloop.entry')


#    print (data[configs[0]] - data[configs[1]]).sum()



    

if __name__ == "__main__":
    
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

    
    def plot(function, configs, show=False):
        plot_df = df[ df['config'].isin(configs)]

        if len(inspect.getargspec(function).args) == 2:
            function(plot_df, configs)
        else:
            function(plot_df)

        if show:
            plt.show()

        plt.savefig("%s.pgf" % function.__name__)
        plt.clf()


    plot(mainloop,          ['LEO 1.6 (e-1.8)'])
    plot(pre2,              ['LEO 1.6 (e-1.8)', 'LEO 1.6 (vampire-3.0)'])
    plot(pre3,              ['LEO 1.6 (e-1.8)', 'LEO 1.6 (vampire-3.0)'])
    plot(thesis2a,          ['LEO 1.6 (e-1.8)', 'LEO m6 (e-1.8)'])
    plot(thesis2b,          ['LEO 1.6 (e-1.8)', 'LEO m6 (e-1.8)'])
    plot(thesis3a,          ['LEO 1.6 (e-1.8)', 'LEO m6 (e-1.8)', 'LEO m6 (multiple provers)' ])
    plot(thesis3b,          ['LEO m6 (e-1.8)', 'LEO m6 (multiple provers)'])
    plot(groupdistribution, ['LEO m6 (e-1.8)'])
    plot(thesis4,           ['LEO m6 (multiple provers)', 'LEO m6 modified  (multiple provers)'])
    plot(analyse_failed,    ['LEO 1.6 (e-1.8)', 'LEO m6 (e-1.8)'])
    plot(summainloop,       ['LEO 1.6 (e-1.8)'])


#    analyze_failed(df, dr.configs)
#    compare_metrics(df)


#    asd(df, dr.configs)

   
        





            

    
 

