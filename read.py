import matplotlib.pyplot as plt

f = open("data.txt", "r") #opens file with name of "test.txt"

freq = []
phase = []

for line in f:
    freq.append(line.split(" ")[3])
    phase.append(line.split(" ")[5][0:-1])

for i in range(len(phase)):
    if float(phase[i]) < 0:
        phase[i] = float(phase[i]) * -1
    print(phase[i])

del freq[0]
del phase[0]

print(freq)
print(len(phase))

plt.figure()
plt.title("Delta Phase")
plt.plot(freq, phase)

plt.show()
