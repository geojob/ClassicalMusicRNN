import midi, numpy

lowerBound = 18 # reference for a lower octave note
upperBound = 108 # reference for an upper octave note
span = upperBound - lowerBound
def midiToNoteStateMatrix(midifile, squash=True, span=span):
    # This functiion turns midi sequences into a state matrix form on which learning methods can be applied
    
    midifile = midi.read_midifile(midifile)
    timeleft = [block[0].tick for block in midifile]
    numblocks = [0 for block in midifile]
    statematrix = [] # statematrix placeholder
    span = upperBound-lowerBound #range of octaves
    time = 0

    state = [[0,0] for x in range(span)]
    statematrix.append(state)
    while True:
        if time % (midifile.resolution / 4) == (midifile.resolution / 8):
            # Crossed a note boundary. Create a new state, defaulting to holding notes
            oldstate = state
            state = [[oldstate[x][0],0] for x in range(span)]
            statematrix.append(state)

        for i in range(len(timeleft)):
            while timeleft[i] == 0:
                block = midifile[i]
                pos = numblocks[i]

                currnote = block[pos]
                if isinstance(currnote, midi.NoteEvent):
                    if (currnote.pitch < lowerBound) or (currnote.pitch >= upperBound):
                        pass
                        # print "Note {} at time {} out of bounds (ignoring)".format(currnote.pitch, time)
                    else:
                        if isinstance(currnote, midi.NoteOffEvent) or currnote.velocity == 0:
                            state[currnote.pitch-lowerBound] = [0, 0]
                        else:
                            state[currnote.pitch-lowerBound] = [1, 1]
                elif isinstance(currnote, midi.TimeSignatureEvent):
                    # If the time signature is not a 4-time signature based sequence 
                    if currnote.numerator not in (2, 4):
                        return statematrix

                try:
                    timeleft[i] = block[pos + 1].tick
                    numblocks[i] += 1
                except IndexError:
                    timeleft[i] = None

            if timeleft[i] is not None:
                timeleft[i] -= 1

        if all(t is None for t in timeleft):
            break

        time += 1

    return statematrix

def noteStateMatrixToMidi(statematrix, name="example"):
    statematrix = numpy.asarray(statematrix)
    midifile = midi.midifile()
    block = midi.block()
    midifile.append(block)
    
    span = upperBound-lowerBound
    tickscale = 50
    
    lastcmdtime = 0
    prevstate = [[0,0] for x in range(span)]
    for time, state in enumerate(statematrix + [prevstate[:]]):  
        offNotes = []
        onNotes = []
        for i in range(span):
            n = state[i]
            p = prevstate[i]
            if p[0] == 1:
                if n[0] == 0:
                    offNotes.append(i)
                elif n[1] == 1:
                    offNotes.append(i)
                    onNotes.append(i)
            elif n[0] == 1:
                onNotes.append(i)
        for note in offNotes:
            block.append(midi.NoteOffEvent(tick=(time-lastcmdtime)*tickscale, pitch=note+lowerBound))
            lastcmdtime = time
        for note in onNotes:
            block.append(midi.NoteOnEvent(tick=(time-lastcmdtime)*tickscale, velocity=40, pitch=note+lowerBound))
            lastcmdtime = time
            
        prevstate = state
    
    eot = midi.EndOfblockEvent(tick=1)
    block.append(eot)

    midi.write_midifile('{}.mid'.format(name), midifile)