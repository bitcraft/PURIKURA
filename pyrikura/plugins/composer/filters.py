"""
these filters will always return a filename, not image class
do not import any imagemagick libraries (for now)
"""
import subprocess
import os


def execute(cmd):
    subprocess.call(cmd.split())


def colortone(filename, color, level, type=0, output=None):
    if output is None:
        output = filename

    if type == 0:
        negate = '-negate'
    else:
        negate = '-negate'

    cmd = 'convert {} \
           -set colorspace RGB \
           ( -clone 0 -fill {} -colorize 100% ) \
           ( -clone 0 -colorspace gray {} ) \
           -compose blend -define compose:args={},{} -composite {}'.format(
        filename, color, negate, level, 100 - level, output
    )

    execute(cmd)
    return output


def vignette(filename, w, h, color0='none', color1='black', ratio=1.5,
             output=None):

    if output is None:
        output = filename

    cmd = 'convert ( {} ) \
           ( -size {}x{} radial-gradient:{}-{} -gravity center \
           -crop {}x{}+0+0 +repage ) \
           -compose multiply -flatten {}'.format(
        filename, w, h, color0, color1, w, h, output
    )

    execute(cmd)
    return output


def toaster(filename, w, h, output=None):
    if output is None:
        output = filename

    #output = filename + '-toaster.miff'
    scratch = filename + 'scratch.miff'

    # colortone
    #scratch = colortone(filename, '#330000', 100, 0, output=scratch)
    #scratch = colortone(filename, '#220000', 100, 0, output=scratch)
    scratch = colortone(filename, '#110000', 105, 0, output=scratch)

    # contrast
    cmd = 'convert {} -modulate 180,115,100 -contrast {}'.format(
        scratch, scratch
    )

    execute(cmd)

    # vignette kungfu
    #scratch = vignette(scratch, w, h, 'none', 'LavenderBlush3')
    #scratch = vignette(scratch, w, h, '#FFD6C2', 'none')
    #scratch = vignette(scratch, w, h, '#E3C2B8', 'none')
    scratch = vignette(scratch, w, h, '#b3a298', 'none')

    execute('convert {} {}'.format(scratch, output))
    os.unlink(scratch)

    return output
