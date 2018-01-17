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

fd=os.popen('cd ~/ && pwd')
HPATH=fd.read().strip('\n')
fd.close()

CFGDIR=HPATH+'/.crius_quickly_build'
CFGFILE=CFGDIR+'/init.conf'
MKLOGDIR=CFGDIR+'/make_verbose'
LOGDIR=CFGDIR+'/log'

def globalInit():
    if os.path.exists(CFGDIR) == False:
        os.mkdir(CFGDIR)
        os.mkdir(MKLOGDIR)
        os.mkdir(LOGDIR)
    if os.path.isfile(CFGFILE) == False:
        initCfgFile()

    logging.basicConfig(filename=LOGDIR+'/current.log',level=logging.DEBUG)

def initCfgFile():
    pass
def loadCfgFile():
    pass

def usage():
    print(USAGE)

def buildProductVerbose(product):
    return MKLOGDIR + '/' + product + '.mkv'

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
        self.flag='.crius_flag'
        self.cfg = loadCfgFile()
        self.script='qb.sh'
        self.output='CRIUS_OUTPUT'
        if len(args.opts['-O'])!=0:
            self.output=args.opts['-O'][0]

    def run(self):
        if self.args.command in self.funcs:
            return self.funcs[self.args.command]()
        else:
            logging.error("the command %s doesn't match the method", self.command)
            return False

    def __build(self):
        if self.__mkvCheck() == False:
            if self.__mkvCreate()==False:
                return False

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
            cmd='grep \"'+k+'\" '+self.__mkvFile()+ \
            ' | grep -A 1 \"'+objTypeD[v][0]+ \
            '\" | grep -v \"'+objTypeD[v][0]+'\"'
            cmdL.append(cmd)

            cmd='grep \"'+k+'\" '+self.__mkvFile()+ \
            ' | grep -A 1 \"'+objTypeD[v][1]+ \
            '\" | grep -v \"'+objTypeD[v][1]+'\"'
            cmdL.append(cmd)

        targetTypeD={'LIB':'Lib (', 'BIN':'BIN ('}
        numLinesD={'LIB':6, 'BIN':4}
        for k,v in targetD.items():
            cmd='gerp -A '+numLinesD[v]+' \"'+targetTypeD[v]+ \
                '.*' + k + '\" ' + self.__mkvFile()+ \
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

        if self.__createScript(dependcyL, targetD):
            fd=os.popen('./'+self.script)
            msg=fd.read()
            fd.close()
            logging.info(msg)

            os.remove(self.script)
        return True

    def __mkvFile(self):
        return buildProductVerbose(self.args.productName)

    def __mkvCheck(self):
        return os.path.isfile(self.__mkvFile())

    def __mkvCreate(self):
        cmd='(make '+self.args.productName + ' VERBOSE=1 > '+ \
            self.__mkvFile() + \
            ' && echo \"1\" > ' + self.flag + \
            ') || echo \"0\" > ' + self.flag

        logging.info('run commnd:' + cmd)
        print('run commnd:' + cmd)

        fd = os.popen(cmd)
        fd.close()
        fd=open(self.flag, 'r')
        msg=fd.read()
        fd.close()
        os.remove(self.flag)
        if msg != '1':
            logging.error('create build log failed for '+self.args.productName)
            self.__mkvDelete()
            return False
        else:
            return True

    def __mkvDelete(self):
        os.remove(self.__mkvFile())

    def __createScript(self, dependcyL, targetD):
        if os.path.isfile(self.script):
            os.remove(self.script)

        fd=open(self.script, 'w')
        fd.write('cd ipos/legacy/pkt/\n')

        #write obj and target compile dependcy into file
        for i in dependcyL:
            fd.write(i)
            fd.write('\n')

        fd.write('cd -')

        opfd=os.popen('cat .scratch | awk -F\':=\' \'{print $2}\'')
        outputDir=opfd.read()
        opfd.close()
        fd.write('cd '+outputDir)

        for target,ttype in targetD.items():
            cmd='find -type f -name ' + target
            opfd=os.popen(cmd)
            paths=opfd.read()
            opfd.close()
            logging.info(paths)
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

        logging.info('file list:'+self.fileList)
        print('file list:'+self.fileList)

        outputL=self.args.opts['-o']
        if len(outputL)>0:
            for i in outputL:
                fd=open(i, 'w')
                for j in self.fileList:
                    fd.write(j)
                fd.close()
        return True

    def __update(self):
        if self.__mkvCheck() == True:
            self.__mkvDelete()

        if self.__mkvCreate()==False:
            return False
        else:
            return True

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
    execute.run()
    bye()
