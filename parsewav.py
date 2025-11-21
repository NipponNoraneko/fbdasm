#!/usr/bin/env python3

from enum import Enum
from sys import argv, exit, stderr
import wave

class WS(Enum):
    UNK  = -1
    LOW  = 0
    HIGH = 1
    END  = 2

def main():
    if len(argv) < 2:
        print("No file arg.", file=stderr)
        exit(2)
    elif len(argv) > 2:
        print("Too many args.", file=stderr)
        exit(2)
    fname = argv[1]
    fi = frameIter = WaveFrames(fname)
    print(f"sample size: {fi.sampw}")
    print(f"nchannels: {fi.nchan}")
    i = 0

    # Skip the first "high" transition (whether we get a low first or
    # not); it might have a wonky cycle length.
    gt = iter(genTransitions(fi))
    tt = next(gt)
    if tt[1] == WS.LOW:
        tt = next(gt)

    hunCycles = []
    maxHiLen = 0
    minHiLen = None
    # Read the next 100 cycles, to measure 
    gc = genCycles(gt, fi.freq)
    for cycle in gc:
        hunCycles.append(cycle)
        if minHiLen is None or minHiLen > cycle.highLen():
            minHiLen = cycle.highLen()
        if maxHiLen < cycle.highLen():
            maxHiLen = cycle.highLen()

        i += 1
        if i == 100: break
    if i != 100:
        print(f"ERROR: Did not get 100 cycles ({i}).", file=stderr)
        exit(1)
    print("Got (1 +) 100 cycles.")
    avgHiLen = sum([c.highLen() for c in hunCycles]) / 100
    avgCycLen = sum([c.cycleLen() for c in hunCycles]) / 100
    print(f"Average cycle length is {avgCycLen} ({fi.freq / avgCycLen} Hz)")
    try:
        idx = [
            c.highLen() > (avgHiLen * 1.5)
            or c.highLen() < (2 * avgHiLen / 3)
            for c in hunCycles
        ].index(True)

        print(f'cycle, idx {idx}, has "high" length'
              f' {hunCycles[idx].highLen() / avgHiLen} times'
              ' the average.', file=stderr)
        exit(1)
    except:
        pass

    Cycle.bitThreshold = avgHiLen * 1.5
    i += 1  # we count the skipped one now
    # Count how long the initial gap is
    for cycle in gc:
        if cycle.bit() is True: break
        i += 1
    print(f"Total gap size: {i} noughts")
    #        last frame      - second frame of gap    + fake first frame len
    gapLen = cycle.frames[2] - hunCycles[0].frames[0] + avgCycLen
    print(f"Total gap time: {gapLen / fi.freq} secs")

    i = 1 # (we just got one)
    # Count how many ones before we get a zero again
    for cycle in gc:
        if cycle.bit() is False: break
        i += 1
    print(f"Announce size: {i} oughts")

def p(arg):
        print(f" {arg}")

def genCycles(ti, freq):
    c = None

    for (fno, t) in ti:
        if t == WS.LOW:
            if c is not None:
                yield c.end(fno)
            c = Cycle(freq, fno)
        elif t == WS.HIGH:
            assert c is not None
            c.high(fno)
        elif c.isHigh():
            yield wc.end(fno)

_THRESHOLD = 0.05
def genTransitions(fi):
    state = WS.UNK

    for (fno, val) in fi:
        if state == WS.UNK:
            # Scan through the frames until there's one clearly above or
            # below the line. This doesn't count as a transition.
            if val > _THRESHOLD:
                state = WS.HIGH
            elif val < -_THRESHOLD:
                state = WS.LOW
        elif state == WS.HIGH:
            # Scan until we hit a low
            if val < -_THRESHOLD:
                state = WS.LOW
                yield (fno, WS.LOW)
        elif state == WS.LOW:
            # Scan until we hit a high
            if val > _THRESHOLD:
                state = WS.HIGH
                yield (fno, WS.HIGH)
    yield (fno, WS.END)

class Cycle:
    def __init__(self, freq, fno):
        self.freq = freq
        self.frames = [fno]

    def high(self, fno):
        assert len(self.frames) == 1
        self.frames.append(fno)
        return self

    def end(self, fno):
        assert len(self.frames) == 2
        self.frames.append(fno)
        return self

    def lowLen(self):
        assert len(self.frames) >= 2
        return self.frames[1] - self.frames[0]

    def highLen(self):
        assert len(self.frames) == 3
        return self.frames[2] - self.frames[1]

    def cycleLen(self):
        assert len(self.frames) == 3
        return self.frames[2] - self.frames[0]

    def cycleFreq(self):
        assert len(self.frames) == 3
        return self.freq / self.cycleLen(self)

    def bit(self):
        assert Cycle.bitThreshold is not None
        return self.highLen() >= Cycle.bitThreshold

class WaveFrames:
    def __init__(self, fname):
        w = self.wave = wave.open(fname, 'rb')
        self.sampw = w.getsampwidth()
        self.nchan = w.getnchannels()
        self.freq = w.getframerate()
        self.reset()

    def __iter__(self):
        #self.reset()
        return self

    def __next__(self):
        w = self.wave
        b = w.readframes(1)
        if len(b) == 0:
            raise StopIteration()
        return self.frameAsFloat(b)

    def reset(self):
        self.wave.rewind()
        self.fcnt = 0

    def frameAsFloat(self, b):
        assert len(b) == self.sampw * self.nchan
        sum = 0
        for i in range(0, len(b), self.sampw):
            factor = 1
            num = 0
            for j in range(i, (i + self.sampw)):
                val = b[j]
                val *= factor
                num += val
                factor *= 256
            sum += num
        ret = (sum // self.nchan)
        if self.sampw == 1:
            # unsigned
            ret -= 128
            ret /= 128
        else:
            # signed
            maxU = 2 ** (8 * self.sampw)
            maxS = 2 ** (8 * self.sampw - 1) - 1
            if ret > maxS:
                ret -= maxU
            ret /= (maxS + 1)
        fcnt = self.fcnt
        self.fcnt += 1
        return (fcnt, ret)

main()
