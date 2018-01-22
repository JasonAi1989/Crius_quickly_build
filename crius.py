import sys
import logging
import os

USAGE="crius <build> [Product name] [files name with full path]\n \
            -g [git commits id] : extract file names from the specific commit id\n \
            -p [patches name] : extract file names from the specific patch\n \
            -l [file including a file list] : extract file names from the specific file\n \
            -m [local verbose file] : use the local verbose file instead of default\n \
            -O [output dir] : default is CRIUS_OBJ\n \
crius extract\n \
            -g [git commits id] : extract file names from the specific commit id\n \
            -p [patches name] : extract file names from the specific patch\n \
            -o [output file name] : write the file names into the specific file\n \
crius update [Product name] : update or create build log for the specific product\n \
"

PRODUCTS=['SF-RP-S9M', 'SF-LC-S9M', 'SF-RP-P1S', 'SF-RP-P1L', 'SF-RP-P0', 'SF-TDM1001']
VERSION='Beta 1.0'

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
    pn='\nProducts: '
    for i in PRODUCTS:
        pn+=i+' '
    pn+='\n'
    print(pn)

def version():
    print(VERSION)

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
        if self.command == '--version' or self.command == '-v':
            version()
            sys.exit()
        elif self.command == '--help' or self.command == '-h':
            usage()
            sys.exit()
        elif self.command == 'extract' \
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

        self.opts={'-g':[], '-p':[], '-o':[], '-O':[], '-l':[], '-m':[], 'default':[]}
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
        if self.command == 'extract':
            return True

        return (self.productName in PRODUCTS)

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
        self.localMkv=''
        if len(args.opts['-m'])!=0:
            self.localMkv=args.opts['-m'][0]

    def run(self):
        if self.args.command in self.funcs:
            return self.funcs[self.args.command]()
        else:
            logging.error("the command %s doesn't match the method", self.command)
            return False

    def __build(self):
        if self.__mkvCheck() == False:
            answer=input('\n\nThere doesn\'t exist make verbose for product ' + \
                         self.args.productName + \
                         ', do you want to create it?(y/n)[y] ') or 'y'
            while True:
                if answer=='n' or answer=='N':
                    return True
                elif answer=='y' or answer=='Y':
                    break
                else:
                    answer=input('\nPlease input y or n ') or 'y'

            if self.__mkvCreate()==False:
                return False

        self.__extract()

        #pick up .c .cc files
        srcL=[]
        for f in self.fileList:
            if f[-2:] == '.c' or f[-3:] == '.cc':
                srcL.append(f)
                logging.info('c/c++:'+f)
        if len(srcL) == 0:
            logging.info('No c/c++ files')
            print('No c/c++ files')
            return True
        elif len(srcL) > 20:
            self.__dumpList(srcL)

            answer=input('\n\nThere are '+len(srcL)+' c/c++ files,'+ \
                ' are you sure to compile them all?(y/n)[n] ') or 'n'
            while True:
                if answer == 'n' or answer == 'N':
                    return True
                elif answer == 'y' or answer == 'Y':
                    break;
                else:
                    answer=input('\nPlease input y or n ') or 'n'

        #organize the src.obj,target into dict
        fields=dict()
        for f in srcL:
            path=os.path.dirname(f)
            if (path in fields.keys()) == False:
                logging.debug('create new field for path:'+path)
                fields[path] = dict()
                fields[path]['src']=list()
                fields[path]['obj']=dict()
                fields[path]['target']=dict()
            else:
                logging.debug('use old field for path:'+path)

            fields[path]['src'].append(f)

            f1=f.replace('.cc', '.o')
            f2=f.replace('.c', '.o')
            if f1 != f:
                f1=os.path.basename(f1)
                fields[path]['obj'][f1]='CC'
            elif f2 != f:
                f2=os.path.basename(f2)
                fields[path]['obj'][f2]='C'

        #analysis Makefile
        for k,v in fields.items():
            mk=k+'/Dir.mk'
            logging.info('Dir.mk:'+mk)
            if os.path.isfile(mk) == False:
                logging.info('no Dir.mk:'+mk)
                del fields[k]
                continue
            else:
                fields[k]['target']=self.__parseMK(mk)

        logging.info('fields:')
        logging.info(fields)

        # Grep make command from verbose build log
        objD=dict()
        targetD=dict()
        for _,v in fields.items():
            objD.update(v['obj'])
            targetD.update(v['target'])

        logging.info('obj dirt:')
        logging.info(objD)
        logging.info('target dir')
        logging.info(targetD)

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
            logging.debug('target:'+k+';ttype:'+v)
            cmd1='grep -A {0} \"{1}.*{2}\" {3} | grep -v \"{1}\" | grep -v \"genver\" | grep -v \"mkdir\"'
            cmd=cmd1.format(numLinesD[v], targetTypeD[v], k, self.__mkvFile())
            cmdL.append(cmd)

        self.__createScript(cmdL)
        self.__runScript()
        self.__deleteScript()
        self.__deployTarget(targetD)

        return True

    def __dumpList(self, l):
        for i in l:
            print(i)

    def __mkvFile(self):
        if self.localMkv and os.path.isfile(self.localMkv):
            return self.localMkv
        else:
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

        os.system(cmd)
        fd=open(self.flag, 'r')
        msg=fd.read().strip('\n')
        fd.close()
        os.remove(self.flag)
        logging.debug('read flag:'+msg)
        if msg != '1':
            logging.error('create build log failed for '+self.args.productName)
            self.__mkvDelete()
            print('\n\ncreate build log failed for '+self.args.productName)
            return False
        else:
            logging.info('create build log successfully for '+self.args.productName)
            print('create build log successfully for '+self.args.productName)
            return True

    def __mkvDelete(self):
        os.remove(self.__mkvFile())

    def __createScript(self, cmdL):
        if os.path.isfile(self.script):
            os.remove(self.script)

        fd=open(self.script, 'w', 7)
        fd.write('cd ipos/legacy/pkt/\n')
        fd.close()

        #write obj and target compile dependcy into file
        for cmd in cmdL:
            logging.info(cmd)
            print(cmd)
            os.system(cmd + '>>' + self.script)
            os.system('echo \'\n\' >>' + self.script)

        os.system('chmod +x '+self.script)

    def __runScript(self):
        os.system('./'+self.script)

    def __deleteScript(self):
        os.remove(self.script)

    def __deployTarget(self, targetD):
        print('=======successfully=======')
        fd=os.popen('cat .scratch | awk -F\':=\' \'{print $2}\'')
        string=fd.read()
        fd.close()
        originOutput=string.strip('\n')

        libPathD=dict()
        binPathD=dict()
        targetTypeD={'BIN':'Bin', 'LIB':'Lib'}
        for target,ttype in targetD.items():
            if ttype == 'LIB':
                pathD=libPathD
            else:
                pathD=binPathD

            obj='{0}/legacy/obj/{1}-linux-armv8/{2}/{3}'.format( \
                    originOutput, self.args.productName.lower(), \
                    targetTypeD[ttype], target)
            stage='{0}/{1}/stage/opt/ipos/{2}/{3}'.format( \
                    originOutput, self.args.productName, \
                    ttype.lower(), target)

            pathD[obj]=stage

        logging.info('lib path dict:')
        logging.info(libPathD)
        logging.info('bin path dict:')
        logging.info(binPathD)

        if os.path.exists(self.output):
            os.system('rm -rf '+self.output)
        os.system('mkdir '+self.output)

        if (not libPathD) and (not binPathD):
            print('Didn\'t find any target')
            return

        for obj,stage in libPathD.items():
            if os.path.isfile(obj) == False:
                print('Didn\'t generate the lib: ', obj)
                continue

            print('lib obj:'+obj)
            print('lib stage:'+stage)
            os.system('cp '+obj+' '+stage)
            os.system('cp '+obj+' '+self.output)

        for obj,stage in binPathD.items():
            if os.path.isfile(obj) == False:
                print('Didn\'t generate the bin: ', obj)
                continue

            print('bin obj: '+obj)
            print('bin stage: '+stage)
            os.system('md5sum '+obj+'| awk \'{print $1}\' >>'+obj)
            os.system('cp '+obj+' '+stage)
            os.system('cp '+obj+' '+self.output)

        print('\nWe\'ve updated targets in obj and stage dir.')
        print('Please find targets in dir:'+self.output)
        logging.info('We\'ve updated targets in obj and stage dir.\n' + \
                     'Please find targets in dir:'+self.output)

    def __parseMK(self, mkFile):
        if os.path.isfile(mkFile):
            cmd='grep -E \"LIB :=|LIB:=|BIN :=|BIN:=\" ' + mkFile
            logging.debug('run cmd:'+cmd)
            fd = os.popen(cmd)
            string = fd.read()
            fd.close()
            logging.debug('targets:'+string)
            lineL=string.replace(' ','').split('\n')
            while '' in lineL:
                lineL.remove('')

            logging.info('target result:')
            logging.info(lineL)

            target=dict()
            for i in lineL:
                if i.find('#') != -1:
                    continue

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
                'ipos/legacy/pkt/sw/se/xc/bsd/Dir.mk', \
              'forwarding/Dir.mk']
        logging.info('definition files:')
        logging.info(defL)

        for i in defL:
            cmd='cat '+i+' |grep '+fake+' | awk -F \'=\' \'{print $2}\''
            fd=os.popen(cmd)
            string=fd.read()
            fd.close()
            lib=os.path.basename(string).replace('.a', '.so.0.0').strip('\n')
            if lib != '':
                return lib

        return fake

    def __extract(self):
        self.fileList = self.args.opts['default']
        self.__extGit()
        self.__extPatch()
        self.__extFileList()

        self.fileList=list(set(self.fileList))

        logging.info('file list:')
        logging.info(self.fileList)
        print('file list:')
        self.__dumpList(self.fileList)

        outputL=self.args.opts['-o']
        if len(outputL)>0:
            for i in outputL:
                fd=open(i, 'w')
                for j in self.fileList:
                    fd.write(j+'\n')
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
