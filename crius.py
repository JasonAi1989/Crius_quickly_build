import sys
import logging
import os

USAGE="crius <build> [Product name] [files name with full path]\n \
            -g [git commits id] : extract file names from the specific commit id\n \
            -p [patches name] : extract file names from the specific patch\n \
            -l [file including a file list] : extract file names from the specific file\n \
            -O [output dir] : default is CRIUS_OBJ\n \
crius extract\n \
            -g [git commits id] : extract file names from the specific commit id\n \
            -p [patches name] : extract file names from the specific patch\n \
            -o [output file name] : write the file names into the specific file\n \
crius update [Product name] : update or create build log for the specific product\n \
\n \
Product Name:SF-RP-S9M SF-LC-S9M SF-RP-P1S SF-RP-P1L SF-RP-P0 SF-TDM1001\n"

def globalInit():
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    pass
def usage():
    print(USAGE)

def logCheck():
    return True
    pass
def bye():
    pass

class Args():
    def __init__(self, argList):
        index = 0
        if argList[index] == 'python3':
            index+=1

        self.scriptName = argList[index]
        index+=1

        self.command = argList[index]
        if self.command == 'extract' \
                or self.command == 'update' \
                or self.command == 'build':
            index+=1
        else:
            self.command = 'build'

        if self.command == 'extract':
            self.productName=''
        else:
            self.productName = argList[index]
            index+=1

        self.opts={'-g':[], '-p':[], '-o':[], '-O':[], '-l':[], 'default':[]}
        cur = self.opts['default']
        for i in range(index, len(argList)):
            if argList[i] in self.opts:
                cur = self.opts[argList[i]]
            else:
                cur.append(argList[i])

        #print args
        logging.info("Args:command-%s, product-%s, opts-%s", \
                     self.command, self.productName, self.opts)

    def isValid(self):
        #check product name
        if self.productName != 'SF-RP-S9M' \
                and self.productName != 'SF-LC-S9M' \
                and self.productName != 'SF-RP-P1S' \
                and self.productName != 'SF-RP-P1L' \
                and self.productName != 'SF-RP-P0' \
                and self.productName != 'SF-TDM1001':
            return False
        else:
            return True

class Executor():
    def __init__(self, args):
        self.args = args
        self.funcs={'build':self.__build, 'extract':self.__extract, 'update':self.__update}
        self.ws=os.getcwd()

    def run(self):
        if self.args.command in self.funcs:
            return self.funcs[self.args.command]()
        else:
            logging.error("the command %s doesn't match the method", self.command)
            return False

    def __build(self):
        self.__extract()
        #pick up .c .cc files
        srcL=[]
        for f in self.fileList:
            if f[-2:] == '.c' or f[-3:] == '.cc':
                srcL.append(f)
        fileds=dict()
        for f in srcL:
            path=os.path.dirname(f)
            if path in fileds.keys() == False:
                fileds[path] = dict()
                fileds[path]['src']=list()
                fileds[path]['obj']=dict()
                fileds[path]['target']=dict()

            fileds[path]['src'].append(f)

            f1=f.replace('.cc', '.o')
            f2=f.replace('.c', '.o')
            if f1 != f:
                fileds[path]['obj'][f1]='CC'
            elif f2 != f:
                fileds[path]['obj'][f2]='C'

        #analysis Makefile
        for k,v in fileds.items():
            mk=k+'/Dir.mk'
            if os.path.isfile(mk) == False:
                del fileds[k]
                continue
            else:
                fileds[k]['target']=self.__parseMK(mk)

        # Grep make command from verbose build log
        objD=dict()
        targetD=dict()
        for _,v in fileds.items():
            objD.update(v['obj'])
            targetD.update(v['target'])

        objTypeD={'CC':['LibCCObj (', 'BinCCObj ('], 'C':['LibCObj (', 'BinCObj (']}
        cmdL=[]
        for k,v in objD.items():
            cmd='grep \"'+k+'\" '+self.buildLog+ \
            ' | grep -A 1 \"'+objTypeD[v][0]+ \
            '\" | grep -v \"'+objTypeD[v][0]+'\"'
            cmdL.append(cmd)

            cmd='grep \"'+k+'\" '+self.buildLog+ \
            ' | grep -A 1 \"'+objTypeD[v][1]+ \
            '\" | grep -v \"'+objTypeD[v][1]+'\"'
            cmdL.append(cmd)

        targetTypeD={'LIB':'Lib (', 'BIN':'BIN ('}
        numLinesD={'LIB':6, 'BIN':4}
        for k,v in targetD.items():
            cmd='gerp -A '+numLinesD[v]+' \"'+targetTypeD[v]+ \
                '.*' + k + '\" ' + self.buildLog + \
                ' | grep -v \"' +targetTypeD[v]+ \
                ' |grep -v \"genver\" | grep -v \"mkdir\"'
            cmdL.append(cmd)

        dependcyL=[]
        for cmd in cmdL:
            fd=os.popen(cmd)
            depency=fd.read()
            fd.close()
            if len(depency) > 0:
                dependcyL.append(depency)

        if self.__createScript(dependcyL):
            fd=os.popen('./'+self.script)
            msg=fd.read()
            fd.close()
            logging.info(msg)

            fd=os.popen('rm -rf '+self.script)
            msg=fd.read()
            fd.close()
            logging.info(msg)


    def __createScript(self, dependcyL):
        pass

    def __parseMK(self, mkFile):
        if os.path.isfile(mkFile):
            cmd='gerp \"LIB :=\"|\"LIB:=\"|\"BIN :=\"|\"BIN:=\" ' + mkFile
            fd = os.popen(cmd)
            string = fd.read()
            fd.close()
            lineL=string.replace(' ','').split('\n')
            while '' in lineL:
                lineL.remove('')
            target=dict()
            for i in lineL:
                l=i.split(':=')
                if len(l)==2:
                    t=l[1]
                    if t[0:2] == '$(':
                        t=t.replace('$(', '').replace(')', '')
                        t=self.__getRealTarget(t)
                    target[t]=l[0]

            if len(target) == 0:
                logging.warning('no target find')

            return target

    #just for lib
    def __getRealTarget(self, fake):
        if self.args.productName == '':
            logging.error('miss product name for get real target')
            return fake

        defL=['build/products/'+self.args.productName+'/Make.mk', \
                'ipos/legacy/pkt/sw/se/xc/bsd/Dir.mk']
        for i in defL:
            cmd='cat '+i+' grep '+fake+' | awk -f\'=\' \'{print $2}\''
            fd=os.popen(cmd)
            string=fd.read()
            fd.close()
            lib=os.path.basename(string).replace('.a', '.so.0.0')
            if lib != '':
                return lib

        return fake

    def __extract(self):
        self.fileList = self.args.opts['default']
        self.__extGit()
        self.__extPatch()
        self.__extFileList()

        self.fileList=list(set(self.fileList))

        logging.info(self.fileList)
        print(self.fileList)

        outputL=self.args.opts['-o']
        if len(outputL)>0:
            for i in outputL:
                fd=open(i, 'w')
                for j in self.fileList:
                    fd.write(j)
                fd.close()

    def __update(self):
        pass

    def __extGit(self):
        l=self.args.opts['-g']
        for i in l:
            cmd='git diff ' + i + ' ' + i + '^ --stat'
            fd=os.popen(cmd)
            msgList=fd.read().split('\n')
            fd.close()
            for iterm in msgList:
                strList=iterm.lstrip().split()
                if len(strList)>0:
                    fn=strList[0]
                    if os.path.isfile(fn):
                        self.fileList.append(fn)

    def __extPatch(self):
        l=self.args.opts['-p']
        for i in l:
            if os.path.isfile(i) == False:
                continue

            cmd='sed -n \'/--- a\//p\' ' + i + ' | cut -b 7-'
            fd=os.popen(cmd)
            msgList=fd.read().split('\n')
            fd.close()
            for iterm in msgList:
                if os.path.isfile(iterm):
                    self.fileList.append(iterm)

    def __extFileList(self):
        l=self.args.opts['-l']
        for i in l:
            if os.path.isfile(i) == False:
                continue

            cmd='cat ' + i
            fd=os.popen(cmd)
            msgList=fd.read().split('\n')
            fd.close()
            for iterm in msgList:
                if os.path.isfile(iterm):
                    self.fileList.append(iterm)


if __name__ == '__main__':
    globalInit()
    logging.info("crius start args:%s", sys.argv)
    arg = Args(sys.argv)
    if arg.isValid()==False:
        usage()
        exit()

    execute = Executor(arg)
    if logCheck() == True:
        execute.run()
    else:
        bye()
