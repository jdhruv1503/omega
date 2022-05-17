from operator import length_hint
import subprocess
import gi
from cProfile import label

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], stdout=subprocess.PIPE)
output = result.stdout.decode('utf-8')

gtkset = Gtk.Settings.get_default()
gtkset.set_property("gtk-theme-name", output)
gtkset.set_property("gtk-application-prefer-dark-theme", True)


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

    print("issued command, ", 'sudo', 'undervolt', '--core', str(coreOffset), '--cache', str(cacheOffset), '--gpu', str(gpuOffset), '--temp', str(temp))

    shellArgs = ['sudo', 'undervolt', '--core', str(coreOffset), '--cache', str(cacheOffset), '--gpu', str(gpuOffset), '--temp', str(temp)]
    subprocess.run(shellArgs)


# GUI starts here

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Omega CPU Controller")

        # Offsets stack
        gridOffsets = Gtk.Grid()
        gridOffsets.set_border_width(20)

        self.label1 = Gtk.Label(label = "Core offset")
        self.label2 = Gtk.Label(label = "Cache offset")
        self.label3 = Gtk.Label(label = "GPU offset")
        self.label4 = Gtk.Label(label = "Temperature target")

        self.label5 = Gtk.Label(label = "  (in mV)")
        self.label6 = Gtk.Label(label = "  (in mV)")
        self.label7 = Gtk.Label(label = "  (in mV)")
        self.label8 = Gtk.Label(label = "  (in °C)")

        self.entry1 = Gtk.Scale.new_with_range(Gtk.Orientation(0), -250.0, 250.0, 5.0)
        self.entry2 = Gtk.Scale.new_with_range(Gtk.Orientation(0), -250.0, 250.0, 5.0)
        self.entry3 = Gtk.Scale.new_with_range(Gtk.Orientation(0), -250.0, 250.0, 5.0)
        self.entry4 = Gtk.Scale.new_with_range(Gtk.Orientation(0), 50.0, 100.0, 1.0)

        self.entry1.set_margin_left(25)
        self.entry2.set_margin_left(25)
        self.entry3.set_margin_left(25)
        self.entry4.set_margin_left(25)

        self.applyButton1 = Gtk.Button.new_with_label("Apply changes")
        self.applyButton1.connect("clicked", self.applyVoltages)
        self.applyButton1.set_border_width(10)

        gridOffsets.attach(self.label1, 0, 1, 1, 1)
        gridOffsets.attach(self.label2, 0, 2, 1, 1)
        gridOffsets.attach(self.label3, 0, 3, 1, 1)
        gridOffsets.attach(self.label4, 0, 4, 1, 1)

        gridOffsets.attach(self.entry1, 1, 1, 1, 1)
        gridOffsets.attach(self.entry2, 1, 2, 1, 1)
        gridOffsets.attach(self.entry3, 1, 3, 1, 1)
        gridOffsets.attach(self.entry4, 1, 4, 1, 1)

        gridOffsets.attach(self.label5, 2, 1, 1, 1)
        gridOffsets.attach(self.label6, 2, 2, 1, 1)
        gridOffsets.attach(self.label7, 2, 3, 1, 1)
        gridOffsets.attach(self.label8, 2, 4, 1, 1)

        gridOffsets.attach(self.applyButton1, 1, 5, 1, 1)

        self.updateVoltageSliders()

        # TODO Clocks stack

        # label5 = Gtk.Label(label = "Cache Offset")
        gridClocks = Gtk.Grid()
        gridClocks.set_border_width(20)
        # gridClocks.attach(label5, 0, 0, 1, 1)

        # TODO Settings

        gridSettings = Gtk.Grid()
        gridSettings.set_border_width(20)
        gridAbout = Gtk.Grid()

        # Main window and stacking

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(250)

        stack.add_titled(gridOffsets, "offsets", "Voltage Offsets")
        stack.add_titled(gridClocks, "clocks", "Clock Speeds")
        stack.add_titled(gridSettings, "settings", "Settings")
        stack.add_titled(gridAbout, "about", "About")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)

        self.mainGrid = Gtk.Grid()
        self.mainGrid.set_border_width(10)

        align = Gtk.Alignment(xscale=0, xalign=0)
        align.add(stack)

        self.mainGrid.attach(stack_switcher, 1, 0, 1, 1)
        self.mainGrid.attach(align, 1, 1, 1, 1)
        self.add(self.mainGrid)

    def applyVoltages(self, applyButton1):
        writeUndervolt(int(self.entry1.get_value()), int(self.entry2.get_value()), int(self.entry3.get_value()), int(self.entry4.get_value()))
        self.updateVoltageSliders()

    def updateVoltageSliders(self):

        offsets = readUndervolt()

        self.entry1.set_value(offsets[0])
        self.entry2.set_value(offsets[1])
        self.entry3.set_value(offsets[2])
        self.entry4.set_value(offsets[3])

win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()