import os
import sys

pluginInitPath = os.path.abspath(__file__)
pluginDir = os.path.dirname(pluginInitPath)
srcDir = os.path.join(pluginDir, "src")
vendorDir = os.path.join(pluginDir, "vendor")
unrealDir = os.path.join(pluginDir, "vendor", "unreal")

def AddDirToPath(dir):
    if dir not in sys.path:
        sys.path.append(dir)

AddDirToPath(pluginDir)
AddDirToPath(srcDir)
AddDirToPath(vendorDir)
AddDirToPath(unrealDir)
