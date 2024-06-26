import maya.cmds as mc
from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QAbstractItemView, QColorDialog, QSlider
from PySide2.QtGui import QColor, QPainter, QBrush
def GetCurrentFrame():
    return int(mc.currentTime(query=True))

class Ghost:
    def __init__(self):
        self.srcMeshes = set() # a set is a list that has unique elements.
        self.ghostGrp = "ghost_grp"
        self.frameAttr = "frame"
        self.srcAttr = "src"
        self.color = [0,0,0]
        self.transparencyRange = 100
        self.transparencyOffset = 0
        self.timeChangeJob = mc.scriptJob(e=["timeChanged", self.TimeChangedEvent])
        self.InitIfGhostGrpNotExist()

    def TimeChangedEvent(self):
        self.UpdateGhostTransparency()

    def OffsetGhostTransparency(self, value):
        self.transparencyOffset = value/100
        self.UpdateGhostTransparency()

    def UpdateGhostTransparency(self):
        currentFrame = GetCurrentFrame() 
        ghosts = mc.listRelatives(self.ghostGrp, c=True)
        if not ghosts:
            return
        
        for ghost in ghosts:
            ghostFrame = mc.getAttr(ghost + "." + self.frameAttr)
            ghostFrameDist = abs(ghostFrame - currentFrame) # the abs function gives you the absolute value of the argument.
            normalizedDist = ghostFrameDist / self.transparencyRange
            normalizedDist += self.transparencyOffset
            if normalizedDist > 1:
                normalizedDist = 1
            
            mat = self.GetMaterialNameForGhost(ghost)
            if mc.objExists(mat):
                mc.setAttr(mat + ".transparency", normalizedDist, normalizedDist, normalizedDist, type = "double3")
        
    def UpdateTransparencyRange(self, newRange):
        self.transparencyRange = newRange
        self.UpdateGhostTransparency()


    def UpdateGhostColors(self, color: QColor):
        ghosts = mc.listRelatives(self.ghostGrp, c=True)
        self.color[0] = color.redF()
        self.color[1] = color.greenF()
        self.color[2] = color.blueF()
        for ghost in ghosts:
            mat = self.GetMaterialNameForGhost(ghost)
            mc.setAttr(mat + ".color", color.redF(), color.greenF(), color.blueF(), type = "double3")

    def DeleteGhostAtCurrentFrame(self):
        currentFrame = GetCurrentFrame()
        ghosts = mc.listRelatives(self.ghostGrp, c=True) #gets all children of the ghost grp 
        for ghost in ghosts:
            ghostFrame = mc.getAttr(ghost + "." + self.frameAttr) # ask for the frame recorded for the ghost
            if ghostFrame == currentFrame: # if the ghost frame is the same as the current frame.
                self.DeleteGhost(ghost) # remove that ghost

    def DeleteAllGhosts(self):
        ghosts = mc.listRelatives(self.ghostGrp, c=True)
        for ghost in ghosts:
            self.DeleteGhost(ghost)

    def DeleteGhost(self, ghost):
        #delete the material
        mat = self.GetMaterialNameForGhost(ghost)
        if mc.objExists(mat):
            mc.delete(mat)
        
        #delete the shading engine
        sg = self.GetShadingEngineForGhost(ghost)
        if mc.objExists(sg):
            mc.delete(sg)
        
        #delete the ghost model
        if mc.objExists(ghost):
            mc.delete(ghost)

    def InitIfGhostGrpNotExist(self):
        if mc.objExists(self.ghostGrp):
            storedSrcMeshes = mc.getAttr(self.ghostGrp + "." + self.srcAttr)
            if storedSrcMeshes:
                self.srcMeshes = set(storedSrcMeshes.split(","))
            return
        
        mc.createNode("transform", n = self.ghostGrp)
        mc.addAttr(self.ghostGrp, ln = self.srcAttr, dt="string")

        
    def SetSelectedAsSrcMesh(self):
        selection = mc.ls(sl=True)
        self.srcMeshes.clear() # removes all elements in the set.
        for selected in selection:
            shapes = mc.listRelatives(selected, s=True) # find all shapes of the selected object
            for s in shapes:
                if mc.objectType(s) == "mesh": # the object is a mesh
                    self.srcMeshes.add(selected) # add the mesh to our set.

        mc.setAttr(self.ghostGrp + "." + self.srcAttr, ",".join(self.srcMeshes), type = "string")

    def AddGhost(self):
        for srcMesh in self.srcMeshes:
            currentFrame = GetCurrentFrame()
            ghostName = srcMesh + "_" + str(currentFrame)
            if mc.objExists(ghostName):
                mc.delete(ghostName)

            mc.duplicate(srcMesh, n = ghostName)
            mc.parent(ghostName, self.ghostGrp)
            mc.addAttr(ghostName, ln = self.frameAttr, dv = currentFrame)
            
            matName = self.GetMaterialNameForGhost(ghostName) # figure out the name for the material
            if not mc.objExists(matName): # check if material not exist
                mc.shadingNode("lambert", asShader = True, name = matName) # create the lambert material if not exists
            
            sgName = self.GetShadingEngineForGhost(ghostName) # fiture out the name of the shading engine
            if not mc.objExists(sgName): # check if the shading engine exists
                mc.sets(name = sgName, renderable = True, empty = True) # create the shading engine if not exists

            mc.connectAttr(matName + ".outColor", sgName + ".surfaceShader", force = True) # connet the material to the shading engine
            mc.sets(ghostName, edit=True, forceElement = sgName) # assign the material to ghost

            mc.setAttr(matName + ".color", self.color[0], self.color[1], self.color[2], type = "double3")

    def GetShadingEngineForGhost(self, ghost):
        return ghost + "_sg"
    
    def GetMaterialNameForGhost(self, ghost):
        return ghost + "_mat"

    def GoToNextGhost(self):
        frames = self.GetGhostFramesSorted() # find all the frames we have in ascending order
        if not frames: # if theres is no frames, there is no ghost, do nothing
            return

        currentFrame = GetCurrentFrame()        
        for frame in frames: #go through each frame
            if frame > currentFrame: #if we find one that is bigger than the current frame, it should be where we move time slider to.
                mc.currentTime(frame, e=True) # e means edit, we are editing the time slider to be at frame
                return
        
        mc.currentTime(frames[0], e=True) # found no frame bigger, go to the beginning

    def GoToPrevGhost(self):
        # to go backwards, you can use the frames.reverse(), it will reverse frames make it in decending order.
        frames = self.GetGhostFramesSorted()
        if not frames:
            return

        currentFrame = GetCurrentFrame()
        frames.reverse()
        for frame in frames:
            if frame < currentFrame:
                mc.currentTime(frame, e=True)
                return

        mc.currentTime(frames[0], e=True)


    def GetGhostFramesSorted(self):
        frames = set()
        ghosts = mc.listRelatives(self.ghostGrp, c=True)
        if not ghosts:
            return []
        
        for ghost in ghosts:
            frame = mc.getAttr(ghost + "." + self.frameAttr)
            frames.add(frame)

        frames = list(frames) # this converts frames to a list
        frames.sort() # this sorts the frames list to ascending order
        return frames # returns the sorted frames

class ColorPicker(QWidget):
    onColorChanged = Signal(QColor) # this adds a built in class member called onColorChanged.
    def __init__(self, width = 80, height = 20):
        super().__init__()
        self.setFixedSize(width, height)
        self.color = QColor()

    def mousePressEvent(self, event):
        color = QColorDialog().getColor(self.color) 
        self.color = color
        self.onColorChanged.emit(self.color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QBrush(self.color))
        painter.drawRect(0,0,self.width(), self.height())

class GhostWidget(QWidget):
    def __init__(self):
        super().__init__() # needed to call if you are inheriting from a parent class
        self.ghost = Ghost() # create a ghost to pass command to.
        self.setWindowTitle("Ghoster Poser V1.0") # set the title of the window
        self.masterLayout = QVBoxLayout() # creates a vertical layout         
        self.setLayout(self.masterLayout) # tells the window to use the vertical layout created in the previous line

        self.srcMeshList = QListWidget() # create a list to show stuff.
        self.srcMeshList.setSelectionMode(QAbstractItemView.ExtendedSelection) # allow multi-seleciton
        self.srcMeshList.itemSelectionChanged.connect(self.SrcMeshSelectionChanged)
        self.srcMeshList.addItems(self.ghost.srcMeshes)
        self.masterLayout.addWidget(self.srcMeshList) # this adds the list created previously to the layout.

        addSrcMeshBtn = QPushButton("Add Source Mesh")
        addSrcMeshBtn.clicked.connect(self.AddSrcMeshBtnClicked)
        self.masterLayout.addWidget(addSrcMeshBtn)

        self.ctrlLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.ctrlLayout)

        addGhostBtn = QPushButton("Add/Update")
        addGhostBtn.clicked.connect(self.ghost.AddGhost)
        self.ctrlLayout.addWidget(addGhostBtn)

        prevGhostBtn = QPushButton("Prev")
        prevGhostBtn.clicked.connect(self.ghost.GoToPrevGhost)
        self.ctrlLayout.addWidget(prevGhostBtn)

        nextGhostBtn = QPushButton("Next")
        nextGhostBtn.clicked.connect(self.ghost.GoToNextGhost)
        self.ctrlLayout.addWidget(nextGhostBtn)

        removeCurrentGhostBtn = QPushButton("Del")
        removeCurrentGhostBtn.clicked.connect(self.ghost.DeleteGhostAtCurrentFrame)
        self.ctrlLayout.addWidget(removeCurrentGhostBtn)       

        removeAllGhostBtn = QPushButton("Del All")
        removeAllGhostBtn.clicked.connect(self.ghost.DeleteAllGhosts)
        self.ctrlLayout.addWidget(removeAllGhostBtn)

        self.materialLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.materialLayout)
        colorPicker = ColorPicker()
        colorPicker.onColorChanged.connect(self.ghost.UpdateGhostColors)
        self.materialLayout.addWidget(colorPicker)                     

        self.transparencyRangeSlider = QSlider()
        self.transparencyRangeSlider.setOrientation(Qt.Horizontal)
        self.transparencyRangeSlider.valueChanged.connect(self.TransparencyValueChanged)
        self.transparencyRangeSlider.setMinimum(0)
        self.transparencyRangeSlider.setMaximum(200)
        self.materialLayout.addWidget(self.transparencyRangeSlider)

        self.transparencyOffset = QSlider()
        self.transparencyOffset.setOrientation(Qt.Horizontal)
        self.transparencyOffset.valueChanged.connect(self.ghost.OffsetGhostTransparency)
        self.transparencyOffset.setMinimum(0)
        self.transparencyOffset.setMaximum(100)
        self.masterLayout.addWidget(self.transparencyOffset)

    def TransparencyValueChanged(self, value):
        self.ghost.UpdateTransparencyRange(value)

    def SrcMeshSelectionChanged(self):
        mc.select(cl=True) # this deselect everything.
        for item in self.srcMeshList.selectedItems():
            mc.select(item.text(), add = True)

    def AddSrcMeshBtnClicked(self):
        self.ghost.SetSelectedAsSrcMesh() # asks ghost to populate it's srcMeshes with the current selection
        self.srcMeshList.clear() # this clears our list widget
        self.srcMeshList.addItems(self.ghost.srcMeshes) # this add the srcMeshes collected eariler to the list widget

ghostWidget = GhostWidget()
ghostWidget.show()