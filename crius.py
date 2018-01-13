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

    def __extract(self):
        self.fileList = self.args.opts['default']
        self.__extGit()
        self.__extPatch()
        self.__extFileList()

        print(self.fileList)

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
