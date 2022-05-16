import subprocess
import gi
from cProfile import label

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


# cpufrequtils command HOOK
# Reads current freqs data and puts it in a list.
def readFreqs():

    result = subprocess.run('cpufreq-info', stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    cpus = output.split("analyzing")
    cpus.pop(0)

    freqs = []
    i=0

    for cpu in cpus:
        freqs.append(dict())

        lines = cpu.split("\n")
        freqs[i]['governors'] = (lines[6].split(":")[::-1][0]).strip()
        freqs[i]['minFreq'] = lines[7].split("within")[::-1][0].split("and")[0].strip()
        freqs[i]['maxFreq'] = lines[7].split("within")[::-1][0].split("and")[1][:-1].strip()
        freqs[i]['governor'] = lines[8].split('"')[1]
        freqs[i]['currentFreq'] = lines[10].split("is")[1][:-1].strip()

        i=i+1
    
    return freqs


# Writes required freqs data.
def writeFreqs(minFreq, maxFreq, governor, cpuNo):

    shellArgs = ['sudo', 'cpufreq-set', '-d', str(minFreq)+"MHz", '-u', str(maxFreq)+"MHz", '-g', governor, '-c', str(cpuNo)]
    subprocess.run(shellArgs)


# UNDERVOLT BY goergewhevell HOOK
# READS Undervolt status using undervolt command in shell and returns relevant numbers in a list.
def readUndervolt():

    result = subprocess.run(['sudo', 'undervolt', '--read'], stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')

    undervoltInfo = dict()

    lines = output.split("\n")
    lines.pop(len(lines)-1)

    for line in lines:
        item = line.split(":")
        undervoltInfo[item[0]] = item[1]

    temp = 100 + int(undervoltInfo['temperature target'].split("(")[0])
    coreOffset = int(round(float(undervoltInfo['core'].split("m")[0])))
    cacheOffset = int(round(float(undervoltInfo['cache'].split("m")[0])))
    gpuOffset = int(round(float(undervoltInfo['gpu'].split("m")[0])))

    return [coreOffset, cacheOffset, gpuOffset, temp]


# WRITES Desired undervolt using undervolt command in shell.
def writeUndervolt(coreOffset, cacheOffset, gpuOffset, temp):

    shellArgs = ['sudo', 'undervolt', '--core', str(coreOffset), '--cache', str(cacheOffset), '--gpu', str(gpuOffset), '--temp', str(temp)]
    subprocess.run(shellArgs)


# GUI starts here

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="CPU Controller")
        self.set_border_width(20)

        # Offsets stack

        label1 = Gtk.Label(label = "Temperature Target")
        label2 = Gtk.Label(label = "Core Offset")
        label3 = Gtk.Label(label = "GPU Offset")
        label4 = Gtk.Label(label = "Cache Offset")

        gridOffsets = Gtk.Grid()
        gridOffsets.attach(label1, 0, 0, 1, 1)
        gridOffsets.attach(label2, 0, 1, 1, 1)
        gridOffsets.attach(label3, 0, 2, 1, 1)
        gridOffsets.attach(label4, 0, 3, 1, 1)

        # Clocks stack

        label5 = Gtk.Label(label = "Cache Offset")
        gridClocks = Gtk.Grid()
        gridClocks.attach(label5, 0, 0, 1, 1)

        # Main window and stacking

        grid = Gtk.Grid()
        self.add(grid)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(250)

        stack.add_titled(gridOffsets, "offsets", "Voltage Offsets")
        stack.add_titled(gridClocks, "clocks", "Clock Speeds")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        grid.attach(stack_switcher, 0, 0, 1, 1)
        grid.attach(stack, 0, 1, 1, 1)


win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()