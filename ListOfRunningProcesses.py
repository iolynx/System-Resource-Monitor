import psutil

def ListOfRunningProcesses(len):
    processes = psutil.process_iter(['pid', 'name', 'memory_info'])

    RunningProcesses = []
    i = 0
    for process in processes:
        cpu_usage = process.cpu_percent()
        RunningProcesses.append([str(process.info['pid']),process.info['name'],str(round(cpu_usage,1))+"%",process.info['memory_info'].vms])
        VirtualMemory = RunningProcesses[i][3]
        if VirtualMemory >= 1024**3:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024**3),1))+"GB"
        elif VirtualMemory >= 1024**2:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024**2),1))+"MB"
        elif VirtualMemory >= 1024:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024),1))+"KB"
        else:
            RunningProcesses[i][3]=str(round(VirtualMemory),1)+"Bytes"
        i+=1
        if i == len:
            break

    RunningProcesses.sort(key=lambda x: x[2], reverse=True)
    return RunningProcesses
