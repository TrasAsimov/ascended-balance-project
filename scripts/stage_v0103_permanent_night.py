"""Stage a recurring night event in the compiled v0.10 common source.

Requires DarkScript3 compilation and binary round-trip before packaging.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'work/pending_common.emevd.dcx.js'
OUT=ROOT/'work/v0103_common_night.emevd.dcx.js'

def main():
    raw=SRC.read_text(encoding='utf-8-sig')
    assert raw.count('    $InitializeEvent(0, 20007902);')==1
    assert '20007903' not in raw
    raw=raw.replace('    $InitializeEvent(0, 20007902);',
                    '    $InitializeEvent(0, 20007902);\n    $InitializeEvent(0, 20007903);')
    # Run in the player's own world only. The grace's time selection or an
    # ordinary time advance is corrected within two seconds after the original
    # starting-time event's flag 100, without replaying a one-shot event. The
    # flask flag 60000 did not reliably fire for the starter heart.
    raw+='''\n$Event(20007903, Restart, function() {
    DisableNetworkSync();
    EndIf(!PlayerIsInOwnWorld());
    WaitFor(EventFlag(100));
    SetCurrentTime(23, 45, 0, false, false, false, 0, 0, 0);
    FreezeTime(true);
    WaitFixedTimeSeconds(2);
    RestartEvent();
});
'''
    OUT.write_text(raw,encoding='utf-8',newline='\r\n')
    assert OUT.read_text().count('$InitializeEvent(0, 20007903)')==1
    print(OUT,OUT.stat().st_size)

if __name__=='__main__':main()
