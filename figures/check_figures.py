"""Check that the consumed threshold schematic reproduces exactly."""
from pathlib import Path
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='rulepotential-figures-') as tmp:
        out=Path(tmp)
        subprocess.run([sys.executable,'-B',str(HERE/'draw_schematics.py'),'--output',str(out)],check=True,timeout=60)
        for name in ('overlay',):
            if (out/(name+'.pdf')).read_bytes() != (HERE/(name+'.pdf')).read_bytes():
                raise RuntimeError('Stale or nondeterministic figure: '+name)
    print('Consumed threshold schematic regenerates exactly.')
