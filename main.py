import datetime
import multiprocessing
import sys
import psutil
import os
import pyqtgraph as pg
from collections import namedtuple
from PyQt5.QtCore import QProcess
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtChart import QChart, QPieSeries, QChartView
from PyQt5.QtCore import QObject, QThread, pyqtSignal


from PyQt5 import QtChart
from PyQt5.QtWidgets import *

# from ListOfRunningProcesses import ListOfRunningProcesses
from ProcessHistoryIO import *

from ui_main import Ui_MainWindow

cwd = os.path.abspath(__file__)[:-8]
FilesToTrack = cwd + "\\ProcessHistory.pkl"
print(FilesToTrack)


no_of_processes = 0

def ListOfRunningProcesses(len_, sortOptions=None):
    processes = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time'])
    global no_of_processes 
    boot_time = psutil.boot_time()
    sub = 2
    if sortOptions == "cpu":
        sub = 2
    elif sortOptions == "mem":
        sub = 3
    RunningProcesses = []
    i = 0
    j = 0
    for process in processes:
        j += 1
        # print(process.info["name"], end = ' ')
        if process.info["name"] == "svchost.exe" or process.info["name"] == "svchost":
            continue
        if process.info["create_time"] < boot_time:
            continue
        if process.info["name"] == None:
            continue
        RunningProcesses.append([str(process.info['pid']),process.info['name'], str(process.info['cpu_percent']) + "%",process.info['memory_info'].vms])
        VirtualMemory = RunningProcesses[i][3]
        if VirtualMemory >= 1024**3:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024**3),1))+"GB"
        elif VirtualMemory >= 1024**2:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024**2),1))+"MB"
        elif VirtualMemory >= 1024:
            RunningProcesses[i][3]=str(round(VirtualMemory/(1024),1))+"KB"
        else:
            RunningProcesses[i][3]=str(round(VirtualMemory),1)+"Bytes"
        # if i == len_:
        #     break

        i += 1
    RunningProcesses.sort(key=lambda x: x[sub], reverse=True)
    no_of_processes = j
    return RunningProcesses[:len_]

def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def get_processes_by_vmem(len):
    processes = {}
    i = 0
    boot_time = psutil.boot_time()
    others = 0
    for proc in psutil.process_iter():
        try:
            name = proc.name()
            pid = proc.pid
            mem_info = proc.memory_info()
            if name[-4:] == ".exe":
                name = name[:-4]
            if proc.create_time() < boot_time:
                continue
            if name in processes.keys():
                processes[name] += mem_info.vms
            else:
                processes[name] = mem_info.vms
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    processesList = [[key, value] for key, value in processes.items()]
    processesList.sort(key=lambda x: x[1], reverse=True)

    for proc in processesList:
        if i > len:
            others += proc[1]
        i += 1
    processesList = processesList[:len]
    processesList.append(["Others", others])

    processesList.sort(key=lambda x: x[1], reverse=True)
    return processesList


RunningProcess = []

class LORPWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        """Long-running task."""
        global RunningProcess
        RunningProcess = ListOfRunningProcesses(75)
        self.finished.emit()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setupUi(self)

        # PAGE 1
        self.btn_page_1.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.ResourceGraph))

        # PAGE 2
        self.btn_page_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.ProcessesView))

        # PAGE 3
        self.btn_page_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.FileHistory))

        #CPU VIEW PAGE
        self.cpuButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.CPUView))

        #MEMORY VIEW PAGE
        self.memoryButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.MemoryView))

        pg.setConfigOptions(antialias = True)

        global RunningProcess
        RunningProcess = ListOfRunningProcesses(75)
        RunningProcess = ListOfRunningProcesses(75)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.timeout.connect(self.update_CPUView)
        self.timer.timeout.connect(self.update_MemoryView)
        self.timer.timeout.connect(self.displayProcess)
        self.timer.start()

        # if self.stackedWidget.currentWidget() == self.ResourceGraph:
        self.times = [i for i in range(-59, 1)]
        self.CPU_usage = [0 for i in range(0, 60)]
        self.Memory_usage = [0 for i in range(0, 60)]
        self.Disk_usage = [0 for i in range(0, 60)]
        self.Network_usage = [0 for i in range(0, 60)]
        # self.GPU_usage = [0 for i in range(0, 61)]

        self.CPU_PlotWidget.setBackground("#0e0a11")
        self.CPU_PlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.CPU_PlotWidget.setLineWidth(1)  
        self.CPU_PlotWidget.showGrid(y=True)
        self.CPU_PlotWidget.setYRange(0, 100)

        self.Memory_PlotWidget.setBackground("#0e0a11")
        self.Memory_PlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.Memory_PlotWidget.setLineWidth(1)  
        self.Memory_PlotWidget.showGrid(y=True)
        self.Memory_PlotWidget.setYRange(0, 100)

        self.Disk_PlotWidget.setBackground("#0e0a11")
        self.Disk_PlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.Disk_PlotWidget.setLineWidth(1)  
        self.Disk_PlotWidget.showGrid(y=True)
        self.Disk_PlotWidget.setYRange(0, 100)

        self.Network_PlotWidget.setBackground("#0e0a11")
        self.Network_PlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.Network_PlotWidget.setLineWidth(1)  
        self.Network_PlotWidget.showGrid(y=True)
        self.Network_PlotWidget.setYRange(0, 35)

        self.CPU_MainPlotWidget.setBackground("#0e0a11")
        self.CPU_MainPlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.CPU_MainPlotWidget.setLineWidth(1)  
        self.CPU_MainPlotWidget.showGrid(y=True)
        self.CPU_MainPlotWidget.setYRange(0, 100)

        self.Memory_MainPlotWidget.setBackground("#0e0a11")
        self.Memory_MainPlotWidget.setFrameStyle(QFrame.StyledPanel | QFrame.Plain) 
        self.Memory_MainPlotWidget.setLineWidth(1)  
        self.Memory_MainPlotWidget.showGrid(y=True)
        self.Memory_MainPlotWidget.setYRange(0, 100)


        self.CPULine = self.CPU_PlotWidget.plot(self.times, self.CPU_usage, brush = (142, 132, 188, 255), fillLevel = 0)
        self.MemoryLine = self.Memory_PlotWidget.plot(self.times, self.CPU_usage, brush = (142, 132, 188, 255),fillLevel = 0)
        self.DiskLine = self.Disk_PlotWidget.plot(self.times, self.CPU_usage,brush = (142, 132, 188, 255), fillLevel = 0)
        self.NetworkLine = self.Network_PlotWidget.plot(self.times, self.CPU_usage, brush = (142, 132, 188, 255),fillLevel = 0)
        self.CPUMainLine = self.CPU_MainPlotWidget.plot(self.times, self.CPU_usage, brush = (142, 132, 188, 255),fillLevel = 0)
        self.MemoryMainLine = self.Memory_MainPlotWidget.plot(self.times, self.Memory_usage, brush = (142, 132, 188, 255),fillLevel = 0)


        self.fileAddress.setStyleSheet("QLineEdit{background:rgb(25, 19, 31)}")
        # self.openfeButton.setStyleSheet("QPushButton{background:rgb(25, 19, 31)}")

        
        '''
        memoryUsage = ListOfRunningProcesses(5, "memory")
        memory_usage = []
        for memu in memoryUsage:
            memory_usage.append([memu[1], memu[2]])
        '''

        memory_usage = get_processes_by_vmem(10)

        self.series = QPieSeries()
        for item in memory_usage:
            self.series.append(item[0], item[1])


        i = 0
        for chart_slice in self.series.slices():
            chart_slice.setLabelVisible()
            # chart_slice.hovered.connect(lambda:self.explode(chart_slice))
            chart_slice.setLabel(memory_usage[i][0] + " " + str(round(100 * chart_slice.percentage(), 1)) + "%")
            chart_slice.setLabelBrush(QBrush(Qt.white))
            i += 1

        self.chart = QChart()
        self.chart.setTitle("Process Memory Consumption")
        self.chart.legend().setVisible(True)
        self.chart.zoom(0.5)


        self.chart.addSeries(self.series)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setBackgroundBrush(QBrush(QColor("transparent")))
        self.Memory_QChart = QChartView(self.chart)
        self.Memory_QChart.setRenderHint(QtGui.QPainter.Antialiasing)
        self.Memory_QChart.update()
        self.Memory_ChartContainer.setContentsMargins(0, 0, 0, 0)
        lay = QtWidgets.QHBoxLayout(self.Memory_ChartContainer)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Memory_QChart)

        self.show()

    def displayProcess(self):
        self.thread = QThread(self)
        self.worker = LORPWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.setProcessLabels())
        self.thread.start()

    def setProcessLabels(self):
        pid=""
        name=""
        cpu=""
        memory=""
        global RunningProcess
        for i in RunningProcess:
            if i[1]:
                if i[0] == "0" or i[0] == 0 or i[1] == "SystemIdleProcess":
                    continue
                pid+=i[0]+"\n\n"
                if i[1][-4:] == ".exe":
                    name+=i[1][:-4]+"\n\n"
                else:
                    name+=i[1]+"\n\n"
                cpu+=i[2]+"\n\n"
                memory+=i[3]+"\n\n"
        self.pidLabel.setText(pid)
        self.nameLabel.setText(name)
        self.cpuLabel.setText(cpu)
        self.MemoryLabel.setText(memory)
    

    def openfeButtonclicked(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Choose a File to View History...", "", "All Files (*)", options = options)
        if filename:
            print(filename)
            self.fileAddress.setText(filename)
            filenamesmall = list(filename.split("/"))[-1]
            self.forfileLabel.setText("for file <font color=PURPLE> <big>" + filenamesmall + "</big> </font>")
            filename = filename.replace('/', '\\')

            history = ReadHistory(filename)
            histring = ""
            for i in history:
                histring = datetime.datetime.fromtimestamp(i).strftime("%m-%d-%y @ %H:%M:%S") + "\n" + histring
            if history == []:
                lastAccess = os.path.getatime(filename)
                WriteHistory(filename, lastAccess)
                history = [datetime.datetime.fromtimestamp(lastAccess).strftime("%m-%d-%y @ %H:%M:%S")]
                histring = history[0]

            print(histring)
            
            self.fileHistoryLabel.setText(histring)
    
    def explode(self, chart_slice):
        boom = chart_slice.isExploded()
        chart_slice.setExploded(True)

    def update_CPUView(self):
        self.UtilizationLabel.setText("Utilization: <big><font color=PURPLE>"+str(psutil.cpu_percent())+"%</font></big>")
        self.SpeedLabel.setText("Speed: <big><font color=PURPLE>"+str(round(psutil.cpu_freq()[0]/1000,3))+"</font>GHz</big>")
        self.ProcessesLabel.setText("Processes: <big><font color=PURPLE>"+str(no_of_processes) + "</font></big>")
        self.ThreadsLabel.setText("Threads: <big><font color=PURPLE>"+ str(int(no_of_processes * 11.69)) + "</font></big>")
        boot_time_timestamp = psutil.boot_time()
        boot_time = datetime.datetime.fromtimestamp(boot_time_timestamp)
        current_time = datetime.datetime.now()
        u = (current_time - boot_time)
        if u.days != 0:
            k = strfdelta(u, "{days}:{hours}:{minutes}:{seconds}")
        else:
            k = strfdelta(u, "{hours}:{minutes}:{seconds}")

        self.UptimeLabel.setText("Uptime: <font color=PURPLE> <big>" + k + "</big></font>")
        self.CoresLabel.setText("Cores: "+str(multiprocessing.cpu_count()))
        self.BaseLabel.setText("Base: "+str(round(psutil.cpu_freq()[1]/1000,3))+"GHz")
        self.MaximumLabel.setText("Maximum: "+str(round(psutil.cpu_freq()[2]/1000,3))+"GHz")
        self.CPUMainLine.setData(self.times, self.CPU_usage)

    def update_MemoryView(self):
        self.MemoryMainLine.setData(self.times, self.Memory_usage)
        mem=psutil.virtual_memory()
        if mem.available > 1024**3:
           avail = str(round(mem.available/(1024**3),1))  + "GB"
        else:
            avail = str(round(mem.available / (1024**2), 1))+ "MB"
        self.AvailableValueLabel.setText("<font color=PURPLE>" + str(avail) + "</font>")
        self.InUseValueLabel.setText("<font color=PURPLE> " + str(round((mem.total-mem.available)/(1024**3),1))+"GB</font>")

    def update_MemoryViewChart(self):
        memory_usage = get_processes_by_vmem(5)
        
        self.chart.removeAllSeries()
        self.series = QPieSeries()
        for item in memory_usage:
            self.series.append(item[0], item[1])

        self.chart.addSeries(self.series)
        self.Memory_QChart.update()

    def update_plot(self):
        self.CPU_usage = self.CPU_usage[1:]
        self.Memory_usage = self.Memory_usage[1:] 
        self.Disk_usage = self.Disk_usage[1:] 
        self.Network_usage = self.Network_usage[1:] 

        cpu = min(100, psutil.cpu_percent() * 1)
        self.CPU_usage.append(cpu)
        self.CPU_UsageLabel.setText(str(cpu) + "%")

        memory = psutil.virtual_memory()[2]
        self.Memory_usage.append(memory)
        self.Memory_UsageLabel.setText(str(memory) + "%")

        (a, b, c, disk) = psutil.disk_usage('/')
        self.Disk_usage.append(disk)
        self.Memory_UsageLabel.setText(str(memory) + "%")

        (sent, received, a, b, c, d, e, f) = psutil.net_io_counters()
        network = (sent + received) / 400000000
        self.Network_usage.append(network)
        self.Network_UsageLabel.setText(str(round(network, 0)) + " mbps")


        self.CPULine.setData(self.times, self.CPU_usage)
        self.MemoryLine.setData(self.times, self.Memory_usage)
        self.NetworkLine.setData(self.times, self.Network_usage)
        self.DiskLine.setData(self.times, self.Disk_usage)


if __name__ == "__main__":
    

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())