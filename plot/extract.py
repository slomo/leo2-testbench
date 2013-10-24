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

    def loadTptp(self, version):
        filename = os.path.join('TPTP-v' + version, 'higherOrderStatus.csv')
        with open(filename, 'rb') as csvfile:
            
            tptp = {(line[0].split('/'))[-1] : line[1] for line in csv.reader(csvfile, skipinitialspace=True) }
            self.tptp[version] =  tptp
    
    def read(self, directory):
        filename = os.path.join(directory, 'summary.csv')
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
                line['config']  = directory

                lines.append(line)
            return lines

    def read_all(self, directories):

        ret = []
        
        for directory in directories:
            ret.extend(self.read(directory))
        
        return ret


        




def read_data(directories):

    tptp = {}
    with open('TPTP-v5.5.0/higherOrderStatus.csv', 'rb') as csvfile:
        tptp = { (line[0].split('/'))[-1] : line[1] for line in csv.reader(csvfile, skipinitialspace=True) }

    def line_handler(line):

        return line
    
    result = []

    for directory in directories:

        filename = os.path.join(directory, 'summary.csv')


    return result



def count_metrics(metrics):

    cats = {
        'never reached main loop' : 0,
        'no main loop completed' : 0,
        'several main loops' : 0,
    }

    for metric in metrics:

        if 'mainloop.entry' not in metric['counters']:
            cats['never reached main loop'] += 1
        elif 'mainloop.completed' in metric['counters']:
            cats['no main loop completed'] +=  1
        else:
            cats['several main loops'] += 1

    return cats


def categorize(datasets, key):

    for (config, dataset) in datasets:
        for row in dataset:
            if not row['problem'] in ret:
                ret[row['problem']] = []                
            
            row['config'] = config
            ret[row['problem']].append(row)
            
            




def plot_mainloop_timer(data, relative=False):

    colors = mplt.rcParams['axes.color_cycle']

    width=0.8
    timers = [
        'mainloop.checktime',
        'mainloop.subpover',
        'mainloop.lightes',
        'mainloop.subsumed',
        'mainloop.calculus',
        'mainloop.updatesets'
    ]

    labels = [
        'checking time left',
        'calling subprover',
        'computing lightes clause',
        'checking subsumtion',
        'performing resolution',
        'updating clauses sets'
        ]

    # filter all with at least one mainloop entry
    ps = [ d for d in data if 'mainloop.entry' in d['counters'] ]

    # compute total mainloop time
    for p in ps:
        p['total'] = sum([ p['timers'][t] if t in p['timers'] else 0 for t in timers ]) 

    if not relative:
        # sort by total time
        ps = sorted(ps, key=itemgetter('total'), reverse=True)

    offsets = [ 0 for i in range(len(ps)) ]
    entries = np.arange(len(ps))

    for j, timer in enumerate(timers):
        data = [ p['timers'][timer] if timer in p['timers'] else 0 for p in ps  ]

        if relative:
            data = [ p['timers'][timer]/p['total'] if timer in p['timers'] else 0 for p in ps  ]
            
        plt.bar(
            entries, data,
            label=labels[j], bottom=offsets,
            color=colors[(j+1) % len(colors)],
            width=width)
        
        offsets =  [ a + b for a,b in zip(offsets, data) ]


    ax = plt.gca()
    plt.xticks(entries + width/2.0, [ '$' + p['problem'] + '$'  for p in ps])

    plt.grid(False, axis='x')


    plt.legend()
    plt.xlabel("problem")
    plt.ylabel("accumulated time in s")
    return plt


def plot_provers(data):

    for i, dataset in enumerate(data):
        
        x = []
        y = []
        s = []

        for j, (domain, g) in enumerate(itertools.groupby(dataset, key=op.itemgetter('domain'))):
            row = list(g)

            count = len([ 1 for item in row if item['expected'] == item['status'] ])        

            x.append(j)
            y.append(i)
            s.append(count*count)
        
        scatter = plt.scatter(x, y, s=s, alpha=0.5 )
        scatter.set_color(colors[(i+1) % len(colors)])
    
        print(x,y,s)

    plt.show()


def compare_runs(sets):


    sets = [ 
        (legend, [ row['realtime'] for row in data])
        for legend, data in sets ]

    (orig, first) = sets[0]
    others = sets[1:]

    first = np.array(first)

    for i, (label,data) in enumerate(others):


       y = (np.array(data) - first)
       x = range(len(data))

       print max(y)
       print min(y)
       

       scatter = plt.scatter(x,y, label=label, marker='.')
       scatter.set_color(colors[(i+4) % len(colors)])
       
        
    plt.legend()
    plt.show()

def describe_config(config):
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

        if leoversion != "1.6" and len(l) == 3:
            return "LEO %s (multiple provers)" % (leoversion)

        return "LEO %s (%s)" % (leoversion, foprover)


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
    plot.xaxis.grid(False)
    plot.yaxis.grid(True)
    plot.yaxis.set_zorder(3)
    plot.yaxis.linestyle = 'solid'

    for line in plot.lines:
        print line.get_zorder()


    plot.legend().title=""
    labels = plot.get_xticklabels() 
    
    plot.grid(axis = 'y', color ='white', linestyle='-')


    plt.show()
    return plot

def pre1(df):

    domaincounts = df.groupby('domain')['domain'].count()

    df['config'] = df['config'].apply(describe_config)
    df = df[ df['category'] == 'Solved']
    df = df[['config','domain']]

    g = df.groupby(['config', 'domain'])['domain'].count() 

    g =  g.astype(float).div(domaincounts, level='domain')
    
    res =  g.unstack().transpose()


    plot = res.plot(kind='bar')
    plot.xaxis.grid(False)
    plot.legend().title=""
    plot.set_ylabel("ratio of solved problems")
    plot.set_xlabel("domains")
    plt.ylim(0,1.1)


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

#    metrics = read_data(sys.argv[1:])
#    fig, ax = plt.subplots()
#    ticks = []

#    for i, (cat, count) in enumerate(count_metrics(metrics).iteritems() ):
#        ticks.append(cat)
#        ax.bar(i+1, count, label=cat, color=colors[(i+1) % len(colors)])

#    ax.set_autoscalex_on(False)
#    ax.set_xlim([0.75,4])
#    ax.set_xticks([])
    
#    ax.legend()
    #rstyle(ax)

#    plt.show()
#    plt.close(5)

#    plt.clf()
 

#    plot_mainloop_timer(read_data([sys.
#argv[1]])[0])
    

   # {
   #     'methods-mainloop' : (plot_mainloop_timer, metrics, {'relative': False}),
   #     'methods-provers' : (plot_provers, None, None)
   # }


    dr = DataReader()
    dr.loadTptp('5.5.0')
    data = dr.read_all(sys.argv[1:])    
    df = pd.DataFrame(data)
    
    df['category'] = df.apply(categorize, axis=1)

#    these2b(df, sys.argv[1])
    these2bfiltered(df, sys.argv[1])
#    these2a(df)
#    pre1(df)
#    visualize_groups(df, sys.argv[1])

#    analyze_failed(df)


    plt.show()
    plt.savefig('file.pgf')
    

#    print cor.to_string()
#    print cor.groupby(['problem', 'config'])
    
    


   # compare_runs(read_data(sys.argv[1:]))
        

#    plot_provers(metrics)
    #plot_mainloop_timer(metrics[0], relative = False)
    #plt.savefig('out.pdf')
   
        





            

    
 

