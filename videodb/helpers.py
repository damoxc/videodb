"""
Collection of functions to help formatting content in templates
"""

def fduration(seconds):
    """
    Formats a string to show time in a human readable form

    :param seconds: the number of seconds
    :type seconds: int
    :returns: a formatted time string, will return '' if seconds == 0
    :rtype: string

    **Usage**

    >>> ftime(23011)
    '6h 23m'

    """
    if not seconds:
        seconds = 0

    if seconds == 0:
        return "0"

    if seconds < 60:
        return '00:%02d' % (seconds)

    minutes = seconds / 60
    seconds = seconds % 60
    if minutes < 60:
        return '%02d:%02d' % (minutes, seconds)

    hours = minutes / 60
    minutes = minutes % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    if fsize_b is None:
        fsize_b = 0

    if fsize_b < 1024:
        return "%.1f B" % fsize_b
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def ftags(tags):
    return '[%s]' % ','.join(['"%s"' % t.strip() for t in tags])