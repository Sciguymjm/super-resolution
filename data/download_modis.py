from subprocess import Popen, PIPE

year = "2017"
month = "03"
day = "06"

username = "mmage"
password = "ue3AaxCIb23I"

p = Popen(["Daac2Disk_win.exe", "--shortname", "MCD43B3", "--versionid", "005",
           "--begin", "{0}-{1}-{2}".format(year, month, day), "--end", "{0}-{1}-{2}".format(year, month, day),
           "--outputdir", "modis", "--tile", "28", "29", "4", "5"], stdin=PIPE)
stdout = p.communicate("y\n" + username + "\n" + password + "\n")
print stdout
