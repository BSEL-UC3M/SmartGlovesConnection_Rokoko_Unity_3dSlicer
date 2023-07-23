import os
import numpy as np
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# ARUCO_TRACKING
#

class ARUCO_TRACKING(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ARUCO_TRACKING"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ARUCO_TRACKING">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

    # Additional initialization step after application startup is complete
    slicer.app.connect("startupCompleted()", registerSampleData)

#
# Register sample data sets in Sample Data module
#

def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # ARUCO_TRACKING1
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='ARUCO_TRACKING',
    sampleName='ARUCO_TRACKING1',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'ARUCO_TRACKING1.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='ARUCO_TRACKING1.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='ARUCO_TRACKING1'
  )

  # ARUCO_TRACKING2
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='ARUCO_TRACKING',
    sampleName='ARUCO_TRACKING2',
    thumbnailFileName=os.path.join(iconsPath, 'ARUCO_TRACKING2.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='ARUCO_TRACKING2.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='ARUCO_TRACKING2'
  )

#
# ARUCO_TRACKINGWidget
#

class ARUCO_TRACKINGWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/ARUCO_TRACKING.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = ARUCO_TRACKINGLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

    # Buttons
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

    # LOAD SCENE 
    self.DeliveryTrainingSpontaneousSetupPath_scene = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Data/aruco_tracking/'
    try:
        #slicer.util.loadScene(self.DeliveryTrainingSpontaneousSetupPath_scene + '2_HAND_GOOD_WITH_METACARPAL.mrml')
        #scene_file = self.DeliveryTrainingSpontaneousSetupPath_scene + 'rokoko_hands_3_fingers.mrml'
        scene_file = self.DeliveryTrainingSpontaneousSetupPath_scene + 'aruco_tracking.mrml'
        slicer.util.loadScene(scene_file)
    
        
    except:
        print('Failed to load the scene file')

    mother_reference = slicer.util.getNode("Marker2ToTracker")
    mother_model = slicer.util.getNode("MotherModel")
    mother_model.SetAndObserveTransformNodeID(mother_reference.GetID())
    

    
    
    
    rhand_posterior = slicer.util.getNode("Marker4ToTracker")
    rhand_anterior = slicer.util.getNode("Marker6ToTracker")
    lhand_posterior = slicer.util.getNode("Marker3ToTracker")
    lhand_anterior = slicer.util.getNode("Marker5ToTracker")
    RightHand_T = slicer.util.getNode("RightHand_T")
    LeftHand_T = slicer.util.getNode("LeftHand_T")
    axis_change_multiplication = slicer.util.getNode("axis_change_multiplication")
    
    registro_izquierdo = slicer.util.getNode("registro_izquierdo")
    registro_derecho = slicer.util.getNode("registro derecho")
    
    matrix_registro = registro_derecho.GetMatrixTransformToParent()
   
    matrix_registro_derecho = np.zeros((4,4))
    matrix_registro_derecho[0,3] = matrix_registro.GetElement(0, 3)
    matrix_registro_derecho[1,3] = matrix_registro.GetElement(1, 3)
    matrix_registro_derecho[2,3] = matrix_registro.GetElement(2, 3)
    matrix_registro_derecho[0,2] = matrix_registro.GetElement(0, 2)
    matrix_registro_derecho[1,2] = matrix_registro.GetElement(1, 2)
    matrix_registro_derecho[2,2] = matrix_registro.GetElement(2, 2)
    matrix_registro_derecho[0,1] = matrix_registro.GetElement(0, 1)
    matrix_registro_derecho[1,1] = matrix_registro.GetElement(1, 1)
    matrix_registro_derecho[2,1] = matrix_registro.GetElement(2, 1)
    matrix_registro_derecho[0,0] = matrix_registro.GetElement(0, 0)
    matrix_registro_derecho[1,0] = matrix_registro.GetElement(1, 0)
    matrix_registro_derecho[2,0] = matrix_registro.GetElement(2, 0)
    
    matrix_registro_izquierdo = registro_izquierdo.GetMatrixTransformToParent()
   
    matrix_registro_izq = np.zeros((4,4))
    matrix_registro_izq[0,3] = matrix_registro_izquierdo.GetElement(0, 3)
    matrix_registro_izq[1,3] = matrix_registro_izquierdo.GetElement(1, 3)
    matrix_registro_izq[2,3] = matrix_registro_izquierdo.GetElement(2, 3)
    matrix_registro_izq[0,2] = matrix_registro_izquierdo.GetElement(0, 2)
    matrix_registro_izq[1,2] = matrix_registro_izquierdo.GetElement(1, 2)
    matrix_registro_izq[2,2] = matrix_registro_izquierdo.GetElement(2, 2)
    matrix_registro_izq[0,1] = matrix_registro_izquierdo.GetElement(0, 1)
    matrix_registro_izq[1,1] = matrix_registro_izquierdo.GetElement(1, 1)
    matrix_registro_izq[2,1] = matrix_registro_izquierdo.GetElement(2, 1)
    matrix_registro_izq[0,0] = matrix_registro_izquierdo.GetElement(0, 0)
    matrix_registro_izq[1,0] = matrix_registro_izquierdo.GetElement(1, 0)
    matrix_registro_izq[2,0] = matrix_registro_izquierdo.GetElement(2, 0)
    # self.calibrationFile = 
    #Metodos de la clase detectora de los marcadores Aruco
    def CalibrationParams(self):
        """
        Funcion que permite obtener los parametros caracteristicos de la camara tras
        su correspondiente calibracion mediante el uso de un tablero de ajedrez.
        :return: Matriz y parametros de distrorsion de la camara
        """
        try:
            with open(str(self.calibrationFile)+"/data/ParametrosCalibracion.yml", "r", encoding="utf8") as infile:
                InformacionCamara = yaml.full_load(infile)
            # Camera matrix
            mtx = np.zeros(shape=(3, 3))
            for i in range(3):
                mtx[i] = InformacionCamara[0]["MatrizCamara"][i]
            # Distorsion parameters of the camera
            dist = np.array([InformacionCamara[1]["Distorsion"][0]])
            return mtx, dist
        except:
            print("ERROR. No se han podido obtener los parametros de la camara")
            mtx = np.zeros(shape=(3, 3))
            dist=[0,0,0,0,0]
            return mtx,dist

    # Back and foreward 
    def right_hand_posterior(caller, eventId):
        # Convert to millimeters (scale the translation components by 10)
        matrix = rhand_posterior.GetMatrixTransformToParent()
        
        matrix_rhand_posterior = np.zeros((4,4))
        matrix_rhand_posterior[0,3] = matrix.GetElement(0, 3)
        matrix_rhand_posterior[1,3] = matrix.GetElement(1, 3)
        matrix_rhand_posterior[2,3] = matrix.GetElement(2, 3)
        matrix_rhand_posterior[0,2] = matrix.GetElement(0, 2)
        matrix_rhand_posterior[1,2] = matrix.GetElement(1, 2)
        matrix_rhand_posterior[2,2] = matrix.GetElement(2, 2)
        matrix_rhand_posterior[0,1] = matrix.GetElement(0, 1)
        matrix_rhand_posterior[1,1] = matrix.GetElement(1, 1)
        matrix_rhand_posterior[2,1] = matrix.GetElement(2, 1)
        matrix_rhand_posterior[0,0] = matrix.GetElement(0, 0)
        matrix_rhand_posterior[1,0] = matrix.GetElement(1, 0)
        matrix_rhand_posterior[2,0] = matrix.GetElement(2, 0)
        
        
        
        relative_rhand_posterior_matrix = np.linalg.inv(matrix_registro_derecho) @ matrix_rhand_posterior

        
        # rhand_posterior.SetMatrixTransformToParent(matrix)
        # print(rhand_posterior.GetMatrixTransformToParent())
        # relative_matrix= vtk.vtkGeneralTransform()
        
        # rhand_posterior.GetTransformBetweenNodes(registro_derecho , None, relative_matrix)
        # print(rhand_posterior)
        
        # relative_rhand_posterior_matrix = (np.linalg.inv(registro_derecho.GetMatrixTransformToParent()) @ rhand_posterior.GetMatrixTransformToParent())
        # print(relative_rhand_posterior_matrix)
        
        RightHand_T.SetAndObserveTransformNodeID(relative_rhand_posterior_matrix.GetID())
        
    
    def right_hand_anterior(caller, eventId):
        # matrix = rhand_anterior.GetMatrixTransformToParent()
        # matrix.SetElement(0, 3, matrix.GetElement(0, 3) / 1)
        # matrix.SetElement(1, 3, matrix.GetElement(1, 3) / 1)
        # matrix.SetElement(2, 3, matrix.GetElement(2, 3) / 1)
        matrix_a = rhand_anterior.GetMatrixTransformToParent()
        
        matrix_rhand_anterior = np.zeros((4,4))
        matrix_rhand_anterior[0,3] = matrix_a.GetElement(0, 3)
        matrix_rhand_anterior[1,3] = matrix_a.GetElement(1, 3)
        matrix_rhand_anterior[2,3] = matrix_a.GetElement(2, 3)
        matrix_rhand_anterior[0,2] = matrix_a.GetElement(0, 2)
        matrix_rhand_anterior[1,2] = matrix_a.GetElement(1, 2)
        matrix_rhand_anterior[2,2] = matrix_a.GetElement(2, 2)
        matrix_rhand_anterior[0,1] = matrix_a.GetElement(0, 1)
        matrix_rhand_anterior[1,1] = matrix_a.GetElement(1, 1)
        matrix_rhand_anterior[2,1] = matrix_a.GetElement(2, 1)
        matrix_rhand_anterior[0,0] = matrix_a.GetElement(0, 0)
        matrix_rhand_anterior[1,0] = matrix_a.GetElement(1, 0)
        matrix_rhand_anterior[2,0] = matrix_a.GetElement(2, 0)
        
        
        
        relative_rhand_anterior_matrix = np.linalg.inv(matrix_registro_derecho) @ matrix_rhand_anterior
        
        # rhand_anterior.SetMatrixTransformToParent(matrix)
        RightHand_T.SetAndObserveTransformNodeID(relative_rhand_anterior_matrix.GetID())
    
    def left_hand_posterior(caller, eventId):
        # matrix = lhand_posterior.GetMatrixTransformToParent()
        # matrix.SetElement(0, 3, matrix.GetElement(0, 3) / 1)
        # matrix.SetElement(1, 3, matrix.GetElement(1, 3) / 1)
        # matrix.SetElement(2, 3, matrix.GetElement(2, 3) / 1)
        matrix_lp = lhand_posterior.GetMatrixTransformToParent()
        
        matrix_lhand_posterior = np.zeros((4,4))
        matrix_lhand_posterior[0,3] = matrix_lp.GetElement(0, 3)
        matrix_lhand_posterior[1,3] = matrix_lp.GetElement(1, 3)
        matrix_lhand_posterior[2,3] = matrix_lp.GetElement(2, 3)
        matrix_lhand_posterior[0,2] = matrix_lp.GetElement(0, 2)
        matrix_lhand_posterior[1,2] = matrix_lp.GetElement(1, 2)
        matrix_lhand_posterior[2,2] = matrix_lp.GetElement(2, 2)
        matrix_lhand_posterior[0,1] = matrix_lp.GetElement(0, 1)
        matrix_lhand_posterior[1,1] = matrix_lp.GetElement(1, 1)
        matrix_lhand_posterior[2,1] = matrix_lp.GetElement(2, 1)
        matrix_lhand_posterior[0,0] = matrix_lp.GetElement(0, 0)
        matrix_lhand_posterior[1,0] = matrix_lp.GetElement(1, 0)
        matrix_lhand_posterior[2,0] = matrix_lp.GetElement(2, 0)
        
        relative_lhand_posterior_matrix = np.linalg.inv(matrix_registro_izq) @ matrix_lhand_posterior
        
        # lhand_posterior.SetMatrixTransformToParent(matrix)
        LeftHand_T.SetAndObserveTransformNodeID(relative_lhand_posterior_matrix.GetID())
        lhand_posterior.SetAndObserveTransformNodeID(axis_change_multiplication.GetID())
    
    def left_hand_anterior(caller, eventId):
        # matrix = lhand_anterior.GetMatrixTransformToParent()
        # matrix.SetElement(0, 3, matrix.GetElement(0, 3) / 1)
        # matrix.SetElement(1, 3, matrix.GetElement(1, 3) / 1)
        # matrix.SetElement(2, 3, matrix.GetElement(2, 3) / 1)
        matrix_la = lhand_anterior.GetMatrixTransformToParent()
        
        matrix_lhand_anterior = np.zeros((4,4))
        matrix_lhand_anterior[0,3] = matrix_la.GetElement(0, 3)
        matrix_lhand_anterior[1,3] = matrix_la.GetElement(1, 3)
        matrix_lhand_anterior[2,3] = matrix_la.GetElement(2, 3)
        matrix_lhand_anterior[0,2] = matrix_la.GetElement(0, 2)
        matrix_lhand_anterior[1,2] = matrix_la.GetElement(1, 2)
        matrix_lhand_anterior[2,2] = matrix_la.GetElement(2, 2)
        matrix_lhand_anterior[0,1] = matrix_la.GetElement(0, 1)
        matrix_lhand_anterior[1,1] = matrix_la.GetElement(1, 1)
        matrix_lhand_anterior[2,1] = matrix_la.GetElement(2, 1)
        matrix_lhand_anterior[0,0] = matrix_la.GetElement(0, 0)
        matrix_lhand_anterior[1,0] = matrix_la.GetElement(1, 0)
        matrix_lhand_anterior[2,0] = matrix_la.GetElement(2, 0)
        
        relative_lhand_anterior_matrix = np.linalg.inv(matrix_registro_izq) @ matrix_lhand_anterior
        
        # lhand_anterior.SetMatrixTransformToParent(matrix)
        LeftHand_T.SetAndObserveTransformNodeID(relative_lhand_anterior_matrix.GetID())
        lhand_anterior.SetAndObserveTransformNodeID(axis_change_multiplication.GetID())

    # Add an observer to the node's ModifiedEvent
    rhand_posterior.AddObserver('ModifiedEvent', right_hand_posterior)
    rhand_anterior.AddObserver('ModifiedEvent', right_hand_anterior)
 
    lhand_posterior.AddObserver('ModifiedEvent', left_hand_posterior)
    lhand_anterior.AddObserver('ModifiedEvent', left_hand_anterior)

    # Change from cm to mm. 
    
    # Transform relative to initial position

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference("InputVolume"):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
    self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
    self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
      self.ui.applyButton.toolTip = "Compute output volume"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input and output volume nodes"
      self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
    self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
    self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
    self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)

  def onApplyButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    try:

      # Compute output
      self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
        self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

      # Compute inverted output (if needed)
      if self.ui.invertedOutputSelector.currentNode():
        # If additional output volume is selected then result with inverted threshold is written there
        self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
          self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()


#
# ARUCO_TRACKINGLogic
#

class ARUCO_TRACKINGLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))

#
# ARUCO_TRACKINGTest
#

class ARUCO_TRACKINGTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ARUCO_TRACKING1()

  def test_ARUCO_TRACKING1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('ARUCO_TRACKING1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = ARUCO_TRACKINGLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
