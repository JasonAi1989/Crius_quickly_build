import sys


if __name__ == '__main__':
    globalInit()
    arg = Args(sys.argv)
    if productName != 'SF-RP-S9M' \
            and productName != 'SF-LC-S9M' \
            and productName != 'SF-RP-P1S' \
            and productName != 'SF-RP-P1L' \
            and productName != 'SF-RP-P0' \
            and productName != 'SF-TDM1001':
        usage()
        exit()

    if logCheck() == True:
        build()
    else:
        bye()



class Args():
    def __init__(self, argList):
        self.scriptName = argList[0]
        self.command = argList[1]
        if self.command != 'extract' and self.command != 'update':
            self.command = 'build'
            index = 1
        else:
            index = 2
        self.productName = argList[index]
        index+=1


