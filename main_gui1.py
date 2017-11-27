from appJar import *
import numpy
import matplotlib.pyplot as plt
import sys
import visa
import math
import time


class main_gui:
    def __init__(self):
        self.app = gui("RIGOL")
        self.file = open("data.txt", "w")
        rm = visa.ResourceManager()
        instruments = rm.list_resources()  # Get the list of device id
        usb_instru = list(filter(lambda x: 'USB' in x, instruments))  # Filter and list usb device
        print(usb_instru)

        # Assert numbers of usb device
        #assert len(usb_instru) == 2, 'Require connection from Rigol Oscilloscope and Function wave Generator'

        # Create connections and get ID character string of both instruments
        self.instru2 = rm.open_resource(usb_instru[1], timeout=5000, chunk_size=1024000)  # Set time out as 5000 milliseconds
        self.instru1 = rm.open_resource(usb_instru[0], timeout=5000, chunk_size=1024000)

        # self.instru1.write('OUTP ON')
        # self.instru1.write('FUNC SIN')
        print(usb_instru)

        self.funcdict = {'Sine': 'SIN', 'Square': 'SQUare', 'Ramp': 'RAMP', 'Pulse': 'PULSe', 'Noise': 'NOISe'}
        self.unit = {'uHz': 10**-6, 'mHz': 10**-3, 'Hz': 1, 'kHz': 10**3, 'MHz': 10**6, 'ns': 10**-9,
                     'us': 10**-6, 'ms': 10**-3, 's': 1}
        self.VoltUnit = {'mVpp': [10**-3, 'VPP'], 'Vpp': [1, 'VPP'], 'mVrms': [10**-3, 'VRMS'], 'Vrms': [1, 'VRMS']}

        self.app.startLabelFrame("Read")
        self.app.setSticky("w")
        self.app.setFont(20)

        self.app.addLabel("l1", "Volt: ", 0, 0)
        self.app.addLabel("volt1", None, 0, 1)
        self.app.addLabel("l2", "Freq: ", 1, 0)
        self.app.addLabel("freq1", None, 1, 1)
        self.app.addLabel("l3", "Volt2: ", 2, 0)
        self.app.addLabel("volt2", None, 2, 1)
        self.app.addButtons(["Read", "Calculate", "Resonance Freq"], [self.read, self.cal, self.res], 3, 0, 3)
        self.app.stopLabelFrame()

        self.app.startLabelFrame("Write")
        self.app.setSticky("w")
        self.app.setFont(20)

        self.app.addLabelOptionBox("Channel", ["CH1", "CH2"])
        self.app.addLabelOptionBox("Waveform", ["- Waveform -", "Sine", "Square",
                                          "Ramp", "Pulse", "Noise"])
        self.app.addLabelOptionBox("Freq/Per", ["Frequency", "Period"])
        self.app.addEntry("freqorper", 4, 0)
        self.app.setEntryDefault("freqorper", "Freq/Period")

        self.app.addOptionBox("unit", ["- Frequency -", "uHz", "mHz", "Hz", "kHz", "MHz",
                                       "- Period -", "ns", "us", "ms", "s"], row=4, column=1)

        self.app.addEntry("amplitude", 5, 0)
        self.app.setEntryDefault("amplitude", "Amplitude")
        self.app.addOptionBox("ampunit", ["- Unit -", "mVpp", "Vpp", "mVrms", "Vrms"], row=5, column=1)

        self.app.addEntry("offset")
        self.app.setEntryDefault("offset", "Offset")
        self.app.addOptionBox("offsetunit", ["- Unit -", "uVdc", "mVdc", "Vdc"], row=6, column=1)

        self.app.addEntry("duty")
        self.app.setEntryDefault("duty", "Duty Circle")

        self.app.addEntry("phase")
        self.app.setEntryDefault("phase", "Phase")

        self.app.addButtons(["Send", "Reset"], [self.submit, self.reset])

        self.app.stopLabelFrame()

    def run(self):
        self.app.go()

    def read(self, btn=None):
        self.volt = float(self.instru2.query(":MEASure:VRMS?"))
        self.period = float(self.instru2.query(':MEASure:PERiod?'))
        self.app.setLabel('volt1', self.volt)
        self.app.setLabel('freq1', self.freq)
        self.app.setLabel('volt2', self.volt3)

    def res(self, btn=None):
        induct = float(self.app.numberBox("Resonance Frequency", "Input inductance: "))
        capa = float(self.app.numberBox("Resonance Frequency", "Input Capasistance: "))
        result = 1/(2*math.pi*(math.sqrt(induct * capa * 10**-12)))
        self.app.infoBox("Result", result)
        self.setFreq(result)

    def cal(self, btn=None):
        i = 3000
        vrms = []
        times = []
        freq = self.freq
        # self.instru2.write(":CHAN1:SCAL {}".format(int(self.voltset+self.offset)/4))
        # time.sleep(0.5)
        # self.instru2.write(":CHAN2:SCAL {}".format(int(self.voltset + self.offset) / 4))
        freqscale = freq/100
        phase = []
        # Change TIMESCALE FOR EACH LOOP #########
        while i <= freq:
            self.instru2.write(':TIM:SCAL {}'.format(1 / (4 * i)))

            time.sleep(0.1)

            self.instru1.write('FREQ {}'.format(i))

            time.sleep(0.1)

            vpp = float(self.instru2.query(":MEASure:VPP? CHAN2"))

            vrms.append(vpp)
            times.append(i)

            time.sleep(0.1)

            deltaphase = float(self.instru2.query(":MEASure:RPH? CHAN1,CHAN2"))
            print(vpp, i, deltaphase)

            time.sleep(0.1)

            phase.append(deltaphase)

            self.instru1.write('FREQ {}'.format(i))
            self.file.write("Voltage: {} Freq: {} Delta-Phase: {}\n".format(vpp, i, deltaphase))
            i += freqscale


        print("vrms: {}".format(vrms))
        print("time: {}".format(times))
        print("phase: {}".format(phase))

        for i in range(len(phase)):
            if float(phase[i]) < 0:
                phase[i] = float(phase[i]) * -1
            # print(phase[i])

        del vrms[0]
        del times[0]
        del phase[0]

        self.plot1(times, vrms)
        self.plot2(times, phase)

    def reset(self, btn=None):
        self.instru1.write('OUTP OFF')
        self.instru1.write('OUTP:CH2 OFF')

    def changeChannel(self, getOption):
        print((getOption['Channel']), 'Cc')
        if getOption['Channel'] == 'CH1':
            self.instru1.write('OUTP ON')
            print('success')
        else:
            self.instru1.write('OUTP:{} ON'.format(getOption['Channel']))

    def changeFunc(self, getOption):
        self.instru1.write('FUNC {}'.format(self.funcdict[getOption['Waveform']]))

    def setFreq(self, freq):
        self.instru1.write('FREQ {}'.format(freq))

    def changeFreq(self, getEntry, getOption):
        if getOption['Freq/Per'] == 'Frequency':
            self.instru1.write('FREQ {}'.format(float(getEntry['freqorper'])*float((self.unit[getOption['unit']]))))
        elif getOption['Freq/Per'] == 'Period':
            self.instru1.write('FREQ {}'.format(1/(float(getEntry['freqorper']) * float((self.unit[getOption['unit']])))))

    def setVoltUnit(self, getOption):
        self.instru1.write('VOLT:UNIT {}'.format(getOption['ampunit'][1]))

    def setVolt(self, getEntry, getOption):
        self.instru1.write('VOLT {} {}'.format(float(getEntry['amplitude'])*float(self.VoltUnit[getOption['ampunit']][0]),
                                               self.VoltUnit[getOption['ampunit']][1]))

    def setOffset(self, getEntry):
        self.instru1.write('VOLT:OFFS {}'.format(float(getEntry['offset'])))

    def setDCYCle(self, getEntry):
        self.instru1.write('FUNCtion:SQUare:DCYCle {}'.format(float(getEntry['duty'])))

    def setPHASe(self, getEntry):
        self.instru1.write('PHASe {}'.format(float(getEntry['phase'])))

    def plot1(self, data, times):
        plt.figure(1)

        plt.subplot(211)
        plt.plot(data, times)
        plt.title("RLC Resonance")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Vpp (V)")
        plt.xscale("log")
        plt.show()

    def plot2(self, data, times):
        plt.figure(2)

        plt.subplot(212)
        plt.plot(data, times)
        plt.title("Phase Shift")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Phase (Degree)")
        plt.xscale("log")
        plt.show()


    def submit(self, btn=None):
        getOption = self.app.getAllOptionBoxes()
        getEntry = self.app.getAllEntries()
        self.getOption = getOption
        self.getEntry = getEntry
        # self.voltset = float(getEntry['amplitude']) * float(self.VoltUnit[getOption['ampunit']][0])
        # self.offset = float(getEntry['offset'])
        self.freq = float(getEntry['freqorper'])*float((self.unit[getOption['unit']]))
        self.volt2 = float(self.instru2.query(":MEASure:VRMS?"))
        self.app.setLabel("freq1", self.freq)
        self.app.setLabel("volt1", self.volt2)
        print(getOption)
        print(getEntry)
        print((self.app.getOptionBox("Waveform")))
        print(self.funcdict[getOption['Waveform']])

        self.changeChannel(getOption)
        # FUNC
        self.changeFunc(getOption)
        time.sleep(0.1)
        # Freq
        self.changeFreq(getEntry,getOption)
        time.sleep(0.1)
        # self.setOffset(getEntry)
        time.sleep(0.1)
        # self.setVolt(getEntry, getOption)

        # self.setDCYCle(getEntry)
        time.sleep(0.1)
        # self.setPHASe(getEntry)
        time.sleep(0.1)



if __name__ == '__main__':
    g = main_gui()
    g.run()
