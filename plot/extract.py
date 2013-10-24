#!/usr/bin/python
import sys
import csv
import os.path
from operator import itemgetter

import re
import matplotlib as mplt
#mplt.use('pgf')
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
    
# TODO: imporve legend and use relative numbers instead of absolute
def these2a(df):


    print (df[df['category'] == 'Error'])[['problem', 'expected', 'status']]

    df['config'] = df['config'].apply(describe_config)
    df = df[ df['expected'] != 'Open' ]    

    bla  = df[['problem', 'config', 'category', 'expected', 'status','realtime']]
    cor = df[['domain', 'config', 'category']]

    df['category'] = cor['category']    
    a = cor.groupby(['config','category'])['category'].count()
    b = a.unstack('config')
    print b
    plot = b.plot(kind='bar')

    style_barchart(plot)

    plot.xaxis.grid(False)
    plot.yaxis.grid(True)
    plot.yaxis.set_zorder(3)
    plot.yaxis.linestyle = 'solid'


    plot.legend().title=""
    plot.grid(axis = 'y', color ='white', linestyle='-')

    return plot

def these2b(df, reference_conf):

    # select median of each problem
    aggregated = df.groupby(['config', 'problem'])['realtime'].median()
    


    reftime = aggregated[reference_conf]
    groups = reftime.apply(lambda x: "%d to %d seconds" % ((x//10)*10,((x//10)+1)*10))


    print groups[groups == '20 to 30 seconds']
    
    # reference_name = describe_config(reference_conf)



    for key in sys.argv[2:]:

        print reference_conf
        print key
 

        run = aggregated.ix[key]
        run = pd.DataFrame(run)
        
        print run


        run["ref.time"] = reftime
        run["ref.group"] = groups
        run["ref.delta"] = run['realtime'] - run['ref.time']

        run = run.dropna()
        run = run.sort("ref.delta")
        print run.values

        plot = run.boxplot(['ref.delta'], by='ref.group')        



#        series = group.reset_index()
#        series ['delta'] = seri['realtime'] - reference['realtime']
#        series ['group'] = reference['group']

#        plot.set_title("%s" % (describe_config(i)))

#    return plot

def these2bfiltered(df, ref):

    df = df[ df['category'] == 'Solved' ]
    these2b(df, ref)






def visualize_groups(df, config):

    df = df[(df['config'] == config) & ((df['category'] == "Timeout") |(df['category'] == "Solved") | (df['category'] == 'Unsolved'))]
# df['group'] = df['realtime'].apply(lambda x: x//1)
#    group = df.groupby(['])['group'].count()    

#   print group

  #  plot = group.hist()

    df['realtime'] = df['realtime']
    df.hist('realtime', by=df['category'])

    plt.show()


# plotted with remoterun/01 and remoterun/00
def movements(df):

    states = df.groupby(['config', 'problem'])['category'].mean()
    states =  states.unstack(level='config').reset_index().groupby([ sys.argv[2], sys.argv[1]])['problem'].count()
    s = states.unstack()
    s.plot(kind='bar')
    print s
    

def analyze_failed(df):

    states = df.groupby(['config', 'problem']).max()
    reference = states.xs(sys.argv[1])
    
    for key in sys.argv[2:]:
        run = states.xs(key)
        
        run['group'] = reference['realtime'].apply(lambda x: x//1)
        run['ref.category']  = reference['category']
        run =  run[run['ref.category'] == 'Solved']
        run['changed'] = (run['category'] == run['ref.category'])
        
        s = run.groupby(['group', 'changed'])['changed'].count()
        cats = run.groupby('group')['group'].count()
        #    s = s.mul(100, level='group').div(cats, level='group')
        s = s.unstack(level='changed')
        s.plot(kind='bar')

def categorize(entry):
    if entry['expected'] == entry['status']:
        category = 'Solved'
    elif entry['status'] == 'Timeout':
        category = 'Timeout'
    elif (entry['status'] == 'Unknown') or (entry['status'] == 'Error'):
        category =  'Unsolved'
    else:
        category = 'Error'
        
    return category






if __name__ == "__main__":

    colors = [
        "#E69F00", "#56B4E9", "#009E73", "#F0E442",
        "#0072B2", "#D55E00", "#CC79A7"
    ]

    dr = DataReader()
    dr.loadTptp('5.5.0')
    data = dr.read_all(sys.argv[1:])    
    df = pd.DataFrame(data)
    
    df['category'] = df.apply(categorize, axis=1)

#    these2b(df, sys.argv[1])
#    these2bfiltered(df, sys.argv[1])
#    these2a(df)
    pre1(df)
#    visualize_groups(df, sys.argv[1])
#    analyze_failed(df)


    plt.show()
    plt.savefig('file.pgf')
    

    
    


   # compare_runs(read_data(sys.argv[1:]))
        

#    plot_provers(metrics)
    #plot_mainloop_timer(metrics[0], relative = False)
    #plt.savefig('out.pdf')
   
        





            

    
 

