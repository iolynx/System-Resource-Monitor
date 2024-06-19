import pickle
import datetime as dt
import os


cwd = os.path.abspath(__file__)[:-20]
FilesToTrack = cwd + "\\ProcessHistory.txt"

def ReadHistory(FileName):
    DictOfProcess = {}
    with open(FilesToTrack, 'r') as f:
        DictOfProcess = eval(f.readline())
    if FileName in DictOfProcess.keys():
        print(DictOfProcess[FileName])
        return DictOfProcess[FileName]
    else:
        return []

def WriteHistory(FileName, Date):      #write directly in SecondsSinceEpoch (float)
    DictOfProcess = {}
    with open(FilesToTrack, 'r') as f:
        DictOfProcess = eval(f.readline())
    f = open(FilesToTrack,'w')
    if FileName in list(DictOfProcess.keys()):
        DictOfProcess[FileName] = DictOfProcess[FileName].append(Date)
    else:
        DictOfProcess[FileName] = [Date]
    f.write(str(DictOfProcess))
    f.close()