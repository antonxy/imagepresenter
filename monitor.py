import platform

if platform.system() == 'Windows':
    import ctypes

    user = ctypes.windll.user32

    class RECT(ctypes.Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

        def dump(self):
            return map(int, (self.left, self.top, self.right, self.bottom))

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_ulong),
            ('rcMonitor', RECT),
            ('rcWork', RECT),
            ('dwFlags', ctypes.c_ulong)
        ]

    def _get_monitors():
        retval = []
        CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)

        def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
            r = lprcMonitor.contents
            #print "cb: %s %s %s %s %s %s %s %s" % (hMonitor, type(hMonitor), hdcMonitor, type(hdcMonitor), lprcMonitor, type(lprcMonitor), dwData, type(dwData))
            data = [hMonitor]
            data.append(r.dump())
            retval.append(data)
            return 1

        cbfunc = CBFUNC(cb)
        temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
        #print temp
        return retval

    def monitor_areas():
        retval = []
        monitors = _get_monitors()
        for hMonitor, extents in monitors:
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            mi.rcMonitor = RECT()
            mi.rcWork = RECT()
            res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
            dim = mi.rcMonitor.dump()
            so = (dim[2] - dim[0], dim[3] - dim[1], dim[0], dim[1])
            retval.append(so)
        return retval
elif platform.system() == 'Linux':
    import subprocess
    import re

    def monitor_areas():
        xout = subprocess.Popen(['xrandr'], stdout=subprocess.PIPE).communicate()[0]
        ms = re.finditer('([0-9]*)x([0-9]*)\+([0-9]*)\+([0-9]*)', xout)
        return [m.groups() for m in ms]
else:
    def monitor_areas():
        return []

if __name__ == '__main__':
    print monitor_areas()