import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time

#
# DeliveryTrainingSetup
#

class DeliveryTrainingSetup(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DeliveryTrainingSetup" # TODO make this more human readable by adding spaces
    self.parent.categories = ["DeliveryTraining"]
    self.parent.dependencies = []
    self.parent.contributors = ["Monica Garcia Sevilla (Universidad Carlos III de Madrid)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
Slicer module inserted in DeliveryTraining extension for registration and calibration of tools and mannequins.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Monica Garcia Sevilla from Universidad Carlos III de Madrid.
"""

#
# DeliveryTrainingSetupWidget
#

class DeliveryTrainingSetupWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Widget variables
    self.logic = DeliveryTrainingSetupLogic()
    self.nonLoadedModels = 0
    self.connect = True
    self.numberOfRealFiducials_forcepsLeft = 0
    self.numberOfRealFiducials_forcepsRight = 0
    self.numberOfRealFiducials_babyBody = 0
    self.numberOfRealFiducials_babyHead = 0
    self.numberOfRealFiducials_mother = 0
    self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/'
    self.DeliveryTrainingSetupPath_guides = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/Guides/'
    self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/RealSize/'
    self.DeliveryTrainingSetupPath_results = ""
    self.calibrationTime = 5 #seconds to calibrate
    self.pivotMode = 0
    self.spinMode = 1
    self.thresholdError = 1 # maximum error in mm


    #
    # Setup view
    #

    # show 3D View
    self.layoutManager= slicer.app.layoutManager()
    self.layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    # quit box and axis
    view = slicer.util.getNode('View1')
    view.SetBoxVisible(0)
    view.SetAxisLabelsVisible(0)


    #
    # LOADING
    #
    self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
    self.loadCollapsibleButton.text = "LOAD"
    self.layout.addWidget(self.loadCollapsibleButton)

    # Layout within the dummy collapsible button
    loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

    # # Select wether to load real size models or small ones for training
    # self.sizeSelection = qt.QHBoxLayout()
    # loadFormLayout.addRow(self.sizeSelection)

    # self.realRadioButton = qt.QRadioButton('REAL')
    # self.sizeSelection.addWidget(self.realRadioButton)
    # self.smallRadioButton = qt.QRadioButton('SMALL')
    # self.smallRadioButton.checked = True
    # self.sizeSelection.addWidget(self.smallRadioButton)

    # Select wether to load real size models or small ones for training
    self.testSelection = qt.QHBoxLayout()
    loadFormLayout.addRow(self.testSelection)
    self.testButtonGroup = qt.QButtonGroup()
    self.testButtonGroup.setExclusive(True)

    self.realRadioButton = qt.QRadioButton('REAL')
    self.testSelection.addWidget(self.realRadioButton)
    self.testButtonGroup.addButton(self.realRadioButton)
    self.realRadioButton.checked = True
    self.develRadioButton = qt.QRadioButton('DEVELOPMENT')
    self.develRadioButton.checked = False
    self.testSelection.addWidget(self.develRadioButton)
    self.testButtonGroup.addButton(self.develRadioButton)

    self.guideSelection = qt.QHBoxLayout()
    loadFormLayout.addRow(self.guideSelection)
    self.guideButtonGroup = qt.QButtonGroup()
    self.guideButtonGroup.setExclusive(True)

    self.guideRadioButton = qt.QRadioButton('WITH GUIDES')
    self.guideSelection.addWidget(self.guideRadioButton)
    self.guideButtonGroup.addButton(self.guideRadioButton)
    self.guideRadioButton.checked = True
    self.noGuideRadioButton = qt.QRadioButton('WITHOUT GUIDES')
    self.noGuideRadioButton.checked = False
    self.guideSelection.addWidget(self.noGuideRadioButton)
    self.guideButtonGroup.addButton(self.noGuideRadioButton)

    # Load models and other data
    self.loadDataButton = qt.QPushButton("Load Data")
    self.loadDataButton.enabled = True
    loadFormLayout.addRow(self.loadDataButton)  

    # Connection to PLUS
    self.connectToPlusButton = qt.QPushButton()
    self.connectToPlusButton.enabled = False
    self.connectToPlusButton.setText('Connect to Plus')
    loadFormLayout.addRow(self.connectToPlusButton)

    # Apply transforms
    self.applyTransformsButton = qt.QPushButton()
    self.applyTransformsButton.enabled = False
    self.applyTransformsButton.setText('Apply Transforms')
    loadFormLayout.addRow(self.applyTransformsButton)

    #
    # REGISTRATION
    #
    self.registrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.registrationCollapsibleButton.text = "REGISTRATION"
    self.registrationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.registrationCollapsibleButton)

    registrationFormLayout = qt.QFormLayout(self.registrationCollapsibleButton)

    # --- Forceps layout ---
    self.ForcepsGroupBox = ctk.ctkCollapsibleGroupBox()
    self.ForcepsGroupBox.setTitle("Forceps Registration")
    self.ForcepsGroupBox.collapsed = True
    registrationFormLayout.addRow(self.ForcepsGroupBox)
    ForcepsGroupBox_Layout = qt.QFormLayout(self.ForcepsGroupBox)
    self.ForcepsGroupBox.setStyleSheet("background-color: rgb(176,231,169);")


    # --- LEFT ---

    self.leftForcepsText = qt.QLabel('LEFT:')
    self.leftForcepsText.setStyleSheet("font-size: 12px; font-weight: bold;")
    ForcepsGroupBox_Layout.addRow(self.leftForcepsText)

    self.fiducialsPlacementLayout_forcepsLeft = qt.QHBoxLayout()
    ForcepsGroupBox_Layout.addRow(self.fiducialsPlacementLayout_forcepsLeft)


     # Create a Fiducials List and add fiducials
    self.placeRealFiducialsButton_forcepsLeft = qt.QPushButton("Place Real Fiducials")
    self.placeRealFiducialsButton_forcepsLeft.enabled = False
    self.fiducialsPlacementLayout_forcepsLeft.addWidget(self.placeRealFiducialsButton_forcepsLeft)

    # Remove Last Fiducial
    self.removeLastFiducialButton_forcepsLeft = qt.QPushButton("Remove Last Fiducial")
    self.removeLastFiducialButton_forcepsLeft.enabled = False
    self.fiducialsPlacementLayout_forcepsLeft.addWidget(self.removeLastFiducialButton_forcepsLeft)

    # Repeat Fiducials Placement
    self.repeatButton_forcepsLeft = qt.QPushButton("Repeat Fiducials Placement")
    self.repeatButton_forcepsLeft.enabled = False
    self.fiducialsPlacementLayout_forcepsLeft.addWidget(self.repeatButton_forcepsLeft)

    # Load existing transform
    self.loadTransformButton_forcepsLeft = qt.QPushButton("Load Existing Transform")
    self.loadTransformButton_forcepsLeft.enabled = True
    ForcepsGroupBox_Layout.addRow(self.loadTransformButton_forcepsLeft)

    # Configure registration parameters and get the resulting transformation
    self.registrationButton_forcepsLeft = qt.QPushButton("Registration")
    self.registrationButton_forcepsLeft.enabled = False
    ForcepsGroupBox_Layout.addRow(self.registrationButton_forcepsLeft)

    # RMSE after registration
    self.rmseText_forcepsLeft = qt.QLabel('-')
    self.QFormLayoutLabel_forcepsLeft = qt.QLabel('RMSE (mm): ')
    ForcepsGroupBox_Layout.addRow(self.QFormLayoutLabel_forcepsLeft, self.rmseText_forcepsLeft)

    # Apply registration to models and fiducials
    self.applyRegistrationButton_forcepsLeft = qt.QPushButton("Apply Registration")
    self.applyRegistrationButton_forcepsLeft.enabled = False
    ForcepsGroupBox_Layout.addRow(self.applyRegistrationButton_forcepsLeft)

    # Save Registration transform in folder
    self.saveRegistrationButton_forcepsLeft = qt.QPushButton("Save")
    self.saveRegistrationButton_forcepsLeft.enabled = False
    ForcepsGroupBox_Layout.addRow(self.saveRegistrationButton_forcepsLeft)

    hEmptyLayout = qt.QFormLayout()
    ForcepsGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    ForcepsGroupBox_Layout.addRow(hEmptyLayout)

    # --- RIGHT ---

    self.rightForcepsText = qt.QLabel('RIGHT:')
    self.rightForcepsText.setStyleSheet("font-size: 12px; font-weight: bold;")
    ForcepsGroupBox_Layout.addRow(self.rightForcepsText)

    self.fiducialsPlacementLayout_forcepsRight = qt.QHBoxLayout()
    ForcepsGroupBox_Layout.addRow(self.fiducialsPlacementLayout_forcepsRight)


     # Create a Fiducials List and add fiducials
    self.placeRealFiducialsButton_forcepsRight = qt.QPushButton("Place Real Fiducials")
    self.placeRealFiducialsButton_forcepsRight.enabled = False
    self.fiducialsPlacementLayout_forcepsRight.addWidget(self.placeRealFiducialsButton_forcepsRight)

    # Remove Last Fiducial
    self.removeLastFiducialButton_forcepsRight = qt.QPushButton("Remove Last Fiducial")
    self.removeLastFiducialButton_forcepsRight.enabled = False
    self.fiducialsPlacementLayout_forcepsRight.addWidget(self.removeLastFiducialButton_forcepsRight)

    # Repeat Fiducials Placement
    self.repeatButton_forcepsRight = qt.QPushButton("Repeat Fiducials Placement")
    self.repeatButton_forcepsRight.enabled = False
    self.fiducialsPlacementLayout_forcepsRight.addWidget(self.repeatButton_forcepsRight)

    # Load existing transform
    self.loadTransformButton_forcepsRight = qt.QPushButton("Load Existing Transform")
    self.loadTransformButton_forcepsRight.enabled = True
    ForcepsGroupBox_Layout.addRow(self.loadTransformButton_forcepsRight)

    # Configure registration parameters and get the resulting transformation
    self.registrationButton_forcepsRight = qt.QPushButton("Registration")
    self.registrationButton_forcepsRight.enabled = False
    ForcepsGroupBox_Layout.addRow(self.registrationButton_forcepsRight)

    # RMSE after registration
    self.rmseText_forcepsRight = qt.QLabel('-')
    self.QFormLayoutLabel_forcepsRight = qt.QLabel('RMSE (mm): ')
    ForcepsGroupBox_Layout.addRow(self.QFormLayoutLabel_forcepsRight, self.rmseText_forcepsRight)

    # Apply registration to models and fiducials
    self.applyRegistrationButton_forcepsRight = qt.QPushButton("Apply Registration")
    self.applyRegistrationButton_forcepsRight.enabled = False
    ForcepsGroupBox_Layout.addRow(self.applyRegistrationButton_forcepsRight)

    # Save Registration transform in folder
    self.saveRegistrationButton_forcepsRight = qt.QPushButton("Save")
    self.saveRegistrationButton_forcepsRight.enabled = False
    ForcepsGroupBox_Layout.addRow(self.saveRegistrationButton_forcepsRight)


    # --- Baby layout ---
    self.BabyGroupBox = ctk.ctkCollapsibleGroupBox()
    self.BabyGroupBox.setTitle("Baby Registration")
    self.BabyGroupBox.collapsed = True
    registrationFormLayout.addRow(self.BabyGroupBox)
    BabyGroupBox_Layout = qt.QFormLayout(self.BabyGroupBox)
    self.BabyGroupBox.setStyleSheet("background-color: rgb(153,217,234);")


    # --- HEAD ---

    self.babyHeadText = qt.QLabel('HEAD:')
    self.babyHeadText.setStyleSheet("font-size: 12px; font-weight: bold;")
    BabyGroupBox_Layout.addRow(self.babyHeadText)

    self.fiducialsPlacementLayout_babyHead = qt.QHBoxLayout()
    BabyGroupBox_Layout.addRow(self.fiducialsPlacementLayout_babyHead)


     # Create a Fiducials List and add fiducials
    self.placeRealFiducialsButton_babyHead = qt.QPushButton("Place Real Fiducials")
    self.placeRealFiducialsButton_babyHead.enabled = True
    self.fiducialsPlacementLayout_babyHead.addWidget(self.placeRealFiducialsButton_babyHead)

    # Remove Last Fiducial
    self.removeLastFiducialButton_babyHead = qt.QPushButton("Remove Last Fiducial")
    self.removeLastFiducialButton_babyHead.enabled = False
    self.fiducialsPlacementLayout_babyHead.addWidget(self.removeLastFiducialButton_babyHead)

    # Repeat Fiducials Placement
    self.repeatButton_babyHead = qt.QPushButton("Repeat Fiducials Placement")
    self.repeatButton_babyHead.enabled = False
    self.fiducialsPlacementLayout_babyHead.addWidget(self.repeatButton_babyHead)

    # Load existing transform
    self.loadTransformButton_babyHead = qt.QPushButton("Load Existing Transform")
    self.loadTransformButton_babyHead.enabled = True
    BabyGroupBox_Layout.addRow(self.loadTransformButton_babyHead)

    # Configure registration parameters and get the resulting transformation
    self.registrationButton_babyHead = qt.QPushButton("Registration")
    self.registrationButton_babyHead.enabled = False
    BabyGroupBox_Layout.addRow(self.registrationButton_babyHead)

    # RMSE after registration
    self.rmseText_babyHead = qt.QLabel('-')
    self.QFormLayoutLabel_babyHead = qt.QLabel('RMSE (mm): ')
    BabyGroupBox_Layout.addRow(self.QFormLayoutLabel_babyHead, self.rmseText_babyHead)

    # Apply registration to models and fiducials
    self.applyRegistrationButton_babyHead = qt.QPushButton("Apply Registration")
    self.applyRegistrationButton_babyHead.enabled = False
    BabyGroupBox_Layout.addRow(self.applyRegistrationButton_babyHead)

    # Save Registration transform in folder
    self.saveRegistrationButton_babyHead = qt.QPushButton("Save")
    self.saveRegistrationButton_babyHead.enabled = False
    BabyGroupBox_Layout.addRow(self.saveRegistrationButton_babyHead)

    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)

    # --- BODY ---

    self.babyBodyText = qt.QLabel('BODY:')
    self.babyBodyText.setStyleSheet("font-size: 12px; font-weight: bold;")
    BabyGroupBox_Layout.addRow(self.babyBodyText)

    self.fiducialsPlacementLayout_babyBody = qt.QHBoxLayout()
    BabyGroupBox_Layout.addRow(self.fiducialsPlacementLayout_babyBody)


     # Create a Fiducials List and add fiducials
    self.placeRealFiducialsButton_babyBody = qt.QPushButton("Place Real Fiducials")
    self.placeRealFiducialsButton_babyBody.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.placeRealFiducialsButton_babyBody)

    # Remove Last Fiducial
    self.removeLastFiducialButton_babyBody = qt.QPushButton("Remove Last Fiducial")
    self.removeLastFiducialButton_babyBody.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.removeLastFiducialButton_babyBody)

    # Repeat Fiducials Placement
    self.repeatButton_babyBody = qt.QPushButton("Repeat Fiducials Placement")
    self.repeatButton_babyBody.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.repeatButton_babyBody)

    # Load existing transform
    self.loadTransformButton_babyBody = qt.QPushButton("Load Existing Transform")
    self.loadTransformButton_babyBody.enabled = True
    BabyGroupBox_Layout.addRow(self.loadTransformButton_babyBody)

    # Configure registration parameters and get the resulting transformation
    self.registrationButton_babyBody = qt.QPushButton("Registration")
    self.registrationButton_babyBody.enabled = False
    BabyGroupBox_Layout.addRow(self.registrationButton_babyBody)

    # RMSE after registration
    self.rmseText_babyBody = qt.QLabel('-')
    self.QFormLayoutLabel_babyBody = qt.QLabel('RMSE (mm): ')
    BabyGroupBox_Layout.addRow(self.QFormLayoutLabel_babyBody, self.rmseText_babyBody)

    # Apply registration to models and fiducials
    self.applyRegistrationButton_babyBody = qt.QPushButton("Apply Registration")
    self.applyRegistrationButton_babyBody.enabled = False
    BabyGroupBox_Layout.addRow(self.applyRegistrationButton_babyBody)

    # Save Registration transform in folder
    self.saveRegistrationButton_babyBody = qt.QPushButton("Save")
    self.saveRegistrationButton_babyBody.enabled = False
    BabyGroupBox_Layout.addRow(self.saveRegistrationButton_babyBody)

    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)

    # ...........TODO...........

    # --- Mother layout ---
    self.MotherGroupBox = ctk.ctkCollapsibleGroupBox()
    self.MotherGroupBox.setTitle("Mother Registration")
    self.MotherGroupBox.collapsed = True
    registrationFormLayout.addRow(self.MotherGroupBox)
    self.MotherGroupBox_Layout = qt.QFormLayout(self.MotherGroupBox)
    self.MotherGroupBox.setStyleSheet("background-color: rgb(255,174,201);")


    self.fiducialsPlacementLayout_mother = qt.QHBoxLayout()
    self.MotherGroupBox_Layout.addRow(self.fiducialsPlacementLayout_mother)


     # Create a Fiducials List and add fiducials
    self.placeRealFiducialsButton_mother = qt.QPushButton("Place Real Fiducials")
    self.placeRealFiducialsButton_mother.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.placeRealFiducialsButton_mother)

    # Remove Last Fiducial
    self.removeLastFiducialButton_mother = qt.QPushButton("Remove Last Fiducial")
    self.removeLastFiducialButton_mother.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.removeLastFiducialButton_mother)

    # Repeat Fiducials Placement
    self.repeatButton_mother = qt.QPushButton("Repeat Fiducials Placement")
    self.repeatButton_mother.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.repeatButton_mother)

    # Load existing transform
    self.loadTransformButton_mother = qt.QPushButton("Load Existing Transform")
    self.loadTransformButton_mother.enabled = True
    self.MotherGroupBox_Layout.addRow(self.loadTransformButton_mother)

    # Configure registration parameters and get the resulting transformation
    self.registrationButton_mother = qt.QPushButton("Registration")
    self.registrationButton_mother.enabled = False
    self.MotherGroupBox_Layout.addRow(self.registrationButton_mother)

    # RMSE after registration
    self.rmseText_mother = qt.QLabel('-')
    self.QFormLayoutLabel_mother = qt.QLabel('RMSE (mm): ')
    self.MotherGroupBox_Layout.addRow(self.QFormLayoutLabel_mother, self.rmseText_mother)

    # Apply registration to models and fiducials
    self.applyRegistrationButton_mother = qt.QPushButton("Apply Registration")
    self.applyRegistrationButton_mother.enabled = False
    self.MotherGroupBox_Layout.addRow(self.applyRegistrationButton_mother)

    # Save Registration transform in folder
    self.saveRegistrationButton_mother = qt.QPushButton("Save")
    self.saveRegistrationButton_mother.enabled = False
    self.MotherGroupBox_Layout.addRow(self.saveRegistrationButton_mother)

    hEmptyLayout = qt.QFormLayout()
    self.MotherGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    self.MotherGroupBox_Layout.addRow(hEmptyLayout)

    #
    # PIVOTING
    #
    self.pivotingCollapsibleButton = ctk.ctkCollapsibleButton()
    self.pivotingCollapsibleButton.text = "PIVOTING"
    self.pivotingCollapsibleButton.collapsed = True
    self.layout.addWidget(self.pivotingCollapsibleButton)

    pivotingFormLayout = qt.QFormLayout(self.pivotingCollapsibleButton)

    # Start Pivot Calibration
    self.startPivotCalibrationButton = qt.QPushButton("Start Pivot Calibration")
    self.startPivotCalibrationButton.enabled = True
    pivotingFormLayout.addRow(self.startPivotCalibrationButton)

    # Countdown and RMSE text
    self.countdownLabel = qt.QLabel()    
    pivotingFormLayout.addRow(self.countdownLabel)
    self.countdownErrorLabel = qt.QLabel()    
    pivotingFormLayout.addRow(self.countdownErrorLabel)

    # Timer
    self.pivotSamplingTimer = qt.QTimer() 
    self.pivotSamplingTimer.setInterval(500)
    self.pivotSamplingTimer.setSingleShot(True)

    # Save Pivoting transform
    self.savePivotingButton = qt.QPushButton("Save")
    self.savePivotingButton.enabled = False
    pivotingFormLayout.addRow(self.savePivotingButton)

    

    # connections
    # LOADING
    # self.realRadioButton.connect('clicked(bool)', self.onSelectSizeClicked)
    # self.smallRadioButton.connect('clicked(bool)', self.onSelectSizeClicked)
    self.loadDataButton.connect('clicked(bool)', self.onLoadDataButtonClicked)
    self.connectToPlusButton.connect('clicked(bool)', self.onConnectToPlusButtonClicked)
    self.applyTransformsButton.connect('clicked(bool)', self.onApplyTransformsButtonClicked)
    # REGISTRATION
    # forceps left
    self.placeRealFiducialsButton_forcepsLeft.connect('clicked(bool)', self.onPlaceRealFiducialsButtonClicked_forcepsLeft)
    self.removeLastFiducialButton_forcepsLeft.connect('clicked(bool)', self.onRemoveLastFiducialButtonClicked_forcepsLeft)
    self.repeatButton_forcepsLeft.connect('clicked(bool)', self.onRepeatButtonClicked_forcepsLeft)
    self.loadTransformButton_forcepsLeft.connect('clicked(bool)', self.onLoadTransformButtonClicked_forcepsLeft)
    self.registrationButton_forcepsLeft.connect('clicked(bool)', self.onRegistrationButtonClicked_forcepsLeft)
    self.applyRegistrationButton_forcepsLeft.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_forcepsLeft)
    self.saveRegistrationButton_forcepsLeft.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_forcepsLeft)
    # forceps right
    self.placeRealFiducialsButton_forcepsRight.connect('clicked(bool)', self.onPlaceRealFiducialsButtonClicked_forcepsRight)
    self.removeLastFiducialButton_forcepsRight.connect('clicked(bool)', self.onRemoveLastFiducialButtonClicked_forcepsRight)
    self.repeatButton_forcepsRight.connect('clicked(bool)', self.onRepeatButtonClicked_forcepsRight)
    self.loadTransformButton_forcepsRight.connect('clicked(bool)', self.onLoadTransformButtonClicked_forcepsRight)
    self.registrationButton_forcepsRight.connect('clicked(bool)', self.onRegistrationButtonClicked_forcepsRight)
    self.applyRegistrationButton_forcepsRight.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_forcepsRight)
    self.saveRegistrationButton_forcepsRight.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_forcepsRight)
    # baby head
    self.placeRealFiducialsButton_babyHead.connect('clicked(bool)', self.onPlaceRealFiducialsButtonClicked_babyHead)
    self.removeLastFiducialButton_babyHead.connect('clicked(bool)', self.onRemoveLastFiducialButtonClicked_babyHead)
    self.repeatButton_babyHead.connect('clicked(bool)', self.onRepeatButtonClicked_babyHead)
    self.loadTransformButton_babyHead.connect('clicked(bool)', self.onLoadTransformButtonClicked_babyHead)
    self.registrationButton_babyHead.connect('clicked(bool)', self.onRegistrationButtonClicked_babyHead)
    self.applyRegistrationButton_babyHead.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_babyHead)
    self.saveRegistrationButton_babyHead.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_babyHead)
    # baby body
    self.placeRealFiducialsButton_babyBody.connect('clicked(bool)', self.onPlaceRealFiducialsButtonClicked_babyBody)
    self.removeLastFiducialButton_babyBody.connect('clicked(bool)', self.onRemoveLastFiducialButtonClicked_babyBody)
    self.repeatButton_babyBody.connect('clicked(bool)', self.onRepeatButtonClicked_babyBody)
    self.loadTransformButton_babyBody.connect('clicked(bool)', self.onLoadTransformButtonClicked_babyBody)
    self.registrationButton_babyBody.connect('clicked(bool)', self.onRegistrationButtonClicked_babyBody)
    self.applyRegistrationButton_babyBody.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_babyBody)
    self.saveRegistrationButton_babyBody.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_babyBody)
    # mother
    self.placeRealFiducialsButton_mother.connect('clicked(bool)', self.onPlaceRealFiducialsButtonClicked_mother)
    self.removeLastFiducialButton_mother.connect('clicked(bool)', self.onRemoveLastFiducialButtonClicked_mother)
    self.repeatButton_mother.connect('clicked(bool)', self.onRepeatButtonClicked_mother)
    self.loadTransformButton_mother.connect('clicked(bool)', self.onLoadTransformButtonClicked_mother)
    self.registrationButton_mother.connect('clicked(bool)', self.onRegistrationButtonClicked_mother)
    self.applyRegistrationButton_mother.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_mother)
    self.saveRegistrationButton_mother.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_mother)
    # PIVOTING
    self.startPivotCalibrationButton.connect('clicked(bool)', self.onStartPivotCalibrationButtonClicked)
    self.pivotSamplingTimer.connect('timeout()',self.onPivotSamplingTimeout)
    self.savePivotingButton.connect('clicked(bool)', self.onSavePivoting)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  # LOADING

  # def onSelectSizeClicked(self):
  #   if self.realRadioButton.isChecked():
  #     self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/'
  #     self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/RealSize/'
  #   if self.smallRadioButton.isChecked():
  #     self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/SmallSize/'
  #     self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/SmallSize/'

  def onLoadDataButtonClicked(self):
    logging.debug('onloadDataButtonClicked')

    # CREATE PATHS
    # self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/'
    # self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/'
    self.DeliveryTrainingSetupPath_results = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/Results/'

    #LOAD MODELS
    # Forceps Left
    try:
      self.forcepsLeftModel = slicer.util.getNode('ForcepsLeftModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'ForcepsLeftModel.stl')
      try:
        self.forcepsLeftModel = slicer.util.getNode(pattern="ForcepsLeftModel")
        self.forcepsLeftModelDisplay=self.forcepsLeftModel.GetModelDisplayNode()
        self.forcepsLeftModelDisplay.SetColor([0.69,0.90,0.66])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ForcepsLeftModel not found')
        

    # Forceps Right
    try:
      self.forcepsRightModel = slicer.util.getNode('ForcepsRightModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'ForcepsRightModel.stl')
      try:
        self.forcepsRightModel = slicer.util.getNode(pattern="ForcepsRightModel")
        self.forcepsRightModelDisplay=self.forcepsRightModel.GetModelDisplayNode()
        self.forcepsRightModelDisplay.SetColor([0.69,0.90,0.66])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ForcepsRightModel not found')
        

    # Baby Head
    try:
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyHeadModel.stl')
      try:
        self.babyHeadModel = slicer.util.getNode(pattern="BabyHeadModel")
        self.babyHeadModelDisplay=self.babyHeadModel.GetModelDisplayNode()
        self.babyHeadModelDisplay.SetColor([0.6,0.85,0.92])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyHeadModel not found')
        
    # Baby Body
    try:
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyBodyModel.stl')
      try:
        self.babyBodyModel = slicer.util.getNode(pattern="BabyBodyModel")
        self.babyBodyModelDisplay=self.babyBodyModel.GetModelDisplayNode()
        self.babyBodyModelDisplay.SetColor([0.6,0.85,0.92])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyBodyModel not found')

        

    # Mother
    try:
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherModel.stl')
      try:
        self.motherModel = slicer.util.getNode(pattern="MotherModel")
        self.motherModelDisplay=self.motherModel.GetModelDisplayNode()
        self.motherModelDisplay.SetColor([1,0.68,0.79])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: MotherModel not found')
        

    # Mother
    try:
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherTummyModel.stl')
      try:
        self.motherTummyModel = slicer.util.getNode(pattern="MotherTummyModel")
        self.motherTummyModelDisplay=self.motherTummyModel.GetModelDisplayNode()
        self.motherTummyModelDisplay.SetColor([1,0.68,0.79])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: motherTummyModel not found')
        

    # Pointer
    try:
      self.pointerModel = slicer.util.getNode('PointerModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'PointerModel.stl')
      try:
        self.pointerModel = slicer.util.getNode(pattern="PointerModel")
        self.pointerModelDisplay=self.pointerModel.GetModelDisplayNode()
        self.pointerModelDisplay.SetColor([0,0.5,0.25])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: PointerModel not found')

    
    #IF GUIDES ARE USED FOR REGISTRATION LOAD THEIR MODELS
    if self.guideRadioButton.isChecked():
      #HEAD
      try:
        self.eyesGuide = slicer.util.getNode('EyesGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'EyesGuide.stl')
        try:
          self.eyesGuide = slicer.util.getNode('EyesGuide')
          self.eyesGuideDisplay = self.eyesGuide.GetModelDisplayNode()
          self.eyesGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.eyesGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: EyesGuide not found')

      
      try:
        self.leftEarGuide = slicer.util.getNode('LeftEarGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'LeftEarGuide.stl')
        try:
          self.leftEarGuide = slicer.util.getNode('LeftEarGuide')
          self.leftEarGuideDisplay = self.leftEarGuide.GetModelDisplayNode()
          self.leftEarGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.leftEarGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: LeftEarGuide not found')
      

      try:
        self.rightEarGuide = slicer.util.getNode('RightEarGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'RightEarGuide.stl')
        try:
          self.rightEarGuide = slicer.util.getNode('RightEarGuide')
          self.rightEarGuideDisplay = self.rightEarGuide.GetModelDisplayNode()
          self.rightEarGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.rightEarGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: RightEarGuide not found')
      
      try:
        self.fontanelleGuide = slicer.util.getNode('FontanelleGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'FontanelleGuide.stl')
        try:
          self.fontanelleGuide = slicer.util.getNode('FontanelleGuide')
          self.fontanelleGuideDisplay = self.fontanelleGuide.GetModelDisplayNode()
          self.fontanelleGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.fontanelleGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: FontanelleGuide not found')
      

      # try:
      #   self.fontanelle2Guide = slicer.util.getNode('Fontanelle2Guide')
      # except:
      #   slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'Fontanelle2Guide.stl')
      #   try:
      #     self.fontanelle2Guide = slicer.util.getNode('Fontanelle2Guide')
      #     self.fontanelle2GuideDisplay = self.fontanelle2Guide.GetModelDisplayNode()
      #     self.fontanelle2GuideDisplay.SetColor([0.937, 0.941, 0.317])
      #     self.fontanelle2GuideDisplay.SetOpacity(0)
      #   except:
      #     self.nonLoadedModels = self.nonLoadedModels + 1
      #     print('ERROR: Fontanelle2Guide not found')

      #BODY
      try:
        self.frontGuide = slicer.util.getNode('FrontGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'FrontGuide.stl')
        try:
          self.frontGuide = slicer.util.getNode('FrontGuide')
          self.frontGuideDisplay = self.frontGuide.GetModelDisplayNode()
          self.frontGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.frontGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: FrontGuide not found')
      
      try:
        self.backGuide = slicer.util.getNode('BackGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'BackGuide.stl')
        try:
          self.backGuide = slicer.util.getNode('BackGuide')
          self.backGuideDisplay = self.backGuide.GetModelDisplayNode()
          self.backGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.backGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: BackGuide not found')
      

      try:
        self.bellyGuide = slicer.util.getNode('BellyGuide')
      except:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'BellyGuide.stl')
        try:
          self.bellyGuide = slicer.util.getNode('BellyGuide')
          self.bellyGuideDisplay = self.bellyGuide.GetModelDisplayNode()
          self.bellyGuideDisplay.SetColor([0.937, 0.941, 0.317])
          self.bellyGuideDisplay.SetOpacity(0)
        except:
          self.nonLoadedModels = self.nonLoadedModels + 1
          print('ERROR: BellyGuide not found')


        

    # Center view in models
    threeDWidget = self.layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()

    # LOAD FIDUCIALS
    # Forceps Left
    try:
      self.VirtualFiducials_forcepsLeft = slicer.util.getNode('VirtualFiducials_forcepsLeft')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'VirtualFiducials_forcepsLeft.fcsv')
      self.VirtualFiducials_forcepsLeft = slicer.util.getNode(pattern="VirtualFiducials_forcepsLeft")
      if not self.VirtualFiducials_forcepsLeft:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: VirtualFiducials_forcepsLeft not found')
      else:
        # Display them in blue
        displayNode = self.VirtualFiducials_forcepsLeft.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try: #Only available in 4.11
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.VirtualFiducials_forcepsLeft.SetDisplayVisibility(0)

    # Forceps Right
    try:
      self.VirtualFiducials_forcepsRight = slicer.util.getNode('VirtualFiducials_forcepsRight')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'VirtualFiducials_forcepsRight.fcsv')
      self.VirtualFiducials_forcepsRight = slicer.util.getNode(pattern="VirtualFiducials_forcepsRight")
      if not self.VirtualFiducials_forcepsRight:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: VirtualFiducials_forcepsRight not found')
      else:
        # Display them in blue
        displayNode = self.VirtualFiducials_forcepsRight.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.VirtualFiducials_forcepsRight.SetDisplayVisibility(0)

    # Baby Head
    try:
      if self.guideRadioButton.isChecked():
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead_guide'
      else:
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead'

      self.VirtualFiducials_babyHead = slicer.util.getNode(self.fiducialsName_babyHead)
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + self.fiducialsName_babyHead +'.fcsv')
      self.VirtualFiducials_babyHead = slicer.util.getNode(pattern=self.fiducialsName_babyHead)
      if not self.VirtualFiducials_babyHead:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: VirtualFiducials_babyHead not found')
      else:
        # Display them in blue
        displayNode = self.VirtualFiducials_babyHead.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.VirtualFiducials_babyHead.SetDisplayVisibility(0)

    # Baby Body
    try:
      if self.guideRadioButton.isChecked():
        self.fiducialsName_babyBody = 'VirtualFiducials_babyBody_guide'
      else:
        self.fiducialsName_babyBody = 'VirtualFiducials_babyBody'

      self.VirtualFiducials_babyBody = slicer.util.getNode(self.fiducialsName_babyBody)
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + self.fiducialsName_babyBody + '.fcsv')
      self.VirtualFiducials_babyBody = slicer.util.getNode(pattern=self.fiducialsName_babyBody)
      if not self.VirtualFiducials_babyBody:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: VirtualFiducials_babyBody not found')
      else:
        # Display them in blue
        displayNode = self.VirtualFiducials_babyBody.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.VirtualFiducials_babyBody.SetDisplayVisibility(0)
    

    # Mother
    try:
      self.virtualFiducials_mother = slicer.util.getNode('VirtualFiducials_mother')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'VirtualFiducials_mother.fcsv')
      self.virtualFiducials_mother = slicer.util.getNode(pattern="VirtualFiducials_mother")
      if not self.virtualFiducials_mother:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: virtualFiducials_mother not found')
      else:
        # Display them in blue
        displayNode = self.virtualFiducials_mother.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.virtualFiducials_mother.SetDisplayVisibility(0)

    # LOAD TRANSFORMS
    # Load PointerTipToPointer
    try:
      self.pointerTipToPointer = slicer.util.getNode('PointerTipToPointer')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'PointerTipToPointer.h5')
      self.pointerTipToPointer = slicer.util.getNode(pattern="PointerTipToPointer")
      if not self.pointerTipToPointer:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: pointerTipToPointer not found')


    try:
      self.pointerModelToPointerTip = slicer.util.getNode('PointerModelToPointerTip')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'PointerModelToPointerTip.h5')
      self.pointerModelToPointerTip = slicer.util.getNode(pattern="PointerModelToPointerTip")
      if not self.pointerModelToPointerTip:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: pointerModelToPointerTip not found')

    # APPLY EXISTING TRANFORMS
    if self.pointerModel and self.pointerModelToPointerTip and self.pointerTipToPointer:
      self.pointerModel.SetAndObserveTransformNodeID(self.pointerModelToPointerTip.GetID())
      self.pointerModelToPointerTip.SetAndObserveTransformNodeID(self.pointerTipToPointer.GetID())

    if self.nonLoadedModels > 0:
      print("Non loaded models: " + str(self.nonLoadedModels))
    else:
      self.loadDataButton.enabled = False
      self.connectToPlusButton.enabled = True


  def onConnectToPlusButtonClicked(self):
    logging.debug('onconnectToPlusButtonClicked')

    if self.connect:
      try:
        cnode = slicer.util.getNode('IGTLConnector')
      except:
        cnode = slicer.vtkMRMLIGTLConnectorNode()
        slicer.mrmlScene.AddNode(cnode)
        cnode.SetName('IGTLConnector')
      correct = cnode.SetTypeClient('localhost', 18944)
      if correct == 1:
        cnode.Start()
        logging.debug('Connection Successful')
        self.applyTransformsButton.enabled = True
        self.connect = False
        self.connectToPlusButton.setText('Disconnect from Plus')
      else:
        print('ERROR: Unable to connect to PLUS')
        logging.debug('ERROR: Unable to connect to PLUS')

    else:
      cnode = slicer.util.getNode('IGTLConnector')
      cnode.Stop()
      self.connect = True
      self.connectToPlusButton.setText('Connect to Plus')

  def onApplyTransformsButtonClicked(self):
    logging.debug('onApplyTransformsButtonClicked')

    nonLoadedTransforms = 0

    # Apply pointerToTracker to all pointer transforms and model
    try:
      self.pointerToTracker = slicer.util.getNode('PointerToTracker')
      self.pointerTipToPointer.SetAndObserveTransformNodeID(self.pointerToTracker.GetID())
      self.placeRealFiducialsButton_forcepsLeft.enabled = True
      self.placeRealFiducialsButton_forcepsRight.enabled = True
      self.placeRealFiducialsButton_babyBody.enabled = True
      self.placeRealFiducialsButton_mother.enabled = True
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: Unable to load PointerToTracker transform')
      

    # Load transforms
    # Load ForcepsLToTracker
    try:
      self.forcepsLeftToTracker = slicer.util.getNode('ForcepsLToTracker')
      self.addWatchdog(self.forcepsLeftToTracker, warningMessage = 'ForcepsL is out of view', playSound = True)
    except:
      print('ERROR: ForcepsLToTracker not found')

    # Load ForcepsRightToTracker
    try:
      self.forcepsRightToTracker = slicer.util.getNode('ForcepsRToTracker')
      self.addWatchdog(self.forcepsRightToTracker, warningMessage = 'ForcepsR is out of view', playSound = True)
    except:
      print('ERROR: ForcepsRToTracker not found')

    # Load TrackerToForcepsL
    try:
      self.trackerToForcepsLeft = slicer.util.getNode('TrackerToForcepsL')
    except:
      print('ERROR: TrackerToForcepsL not found')

    # Load TrackerToForcepsR
    try:
      self.trackerToForcepsRight = slicer.util.getNode('TrackerToForcepsR')
    except:
      print('ERROR: TrackerToForcepsR not found')

    # Load BabyHeadToTracker
    try:
      self.babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
      # Add watchdog
      self.addWatchdog(self.babyHeadToTracker, warningMessage = 'Baby Head is out of view', playSound = True)
    except:
      print('ERROR: BabyHeadToTracker not found')
      
    # Load BabyBodyToTracker
    try:
      self.babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
      # Add watchdog
      self.addWatchdog(self.babyBodyToTracker, warningMessage = 'Baby Body is out of view', playSound = True)
    except:
      print('ERROR: BabyBodyToTracker not found')

    # Load TrackerToBabyBody
    try:
      self.trackerToBabyBody = slicer.util.getNode('TrackerToBabyBody')
    except:
      print('ERROR: TrackerToBabyBody not found')

    # Load TrackerToBabyHead
    try:
      self.trackerToBabyHead = slicer.util.getNode('TrackerToBabyHead')
    except:
      print('ERROR: TrackerToBabyHead not found')

    # Load TrackerToPointer
    try:
      self.trackerToPointer = slicer.util.getNode('TrackerToPointer')
      # Add watchdog
      self.addWatchdog(self.trackerToPointer, warningMessage = 'Pointer is out of view', playSound = True)
    except:
      print('ERROR: TrackerToPointer not found')
      
    if nonLoadedTransforms == 0:
      self.applyTransformsButton.enabled = False

    self.loadCollapsibleButton.collapsed = True
    self.registrationCollapsibleButton.collapsed = False

  def addWatchdog(self, transformNode, warningMessage, playSound):
    """
    Function to add watchdog node to a transformation node. A warning message will be shown on screen when the tool is out of view.
    """
    wd_logic = slicer.vtkSlicerWatchdogLogic()
    wd_logic.AddNewWatchdogNode('WatchdogNode', slicer.mrmlScene)
    wd = slicer.util.getNode('WatchdogNode')
    wd.AddWatchedNode(transformNode)
    nodeID = 0
    wd.SetWatchedNodeWarningMessage(nodeID, warningMessage)
    wd.SetWatchedNodeUpdateTimeToleranceSec(nodeID, 0.2)
    wd.SetWatchedNodePlaySound(nodeID, playSound)

  # REGISTRATION

  # FORCEPS LEFT

  def onPlaceRealFiducialsButtonClicked_forcepsLeft(self):
    logging.debug('onPlaceRealFiducialsButtonClicked_forcepsLeft')

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      self.trackerToForcepsLeft = slicer.util.getNode('TrackerToForcepsL')
      self.pointerToTracker.SetAndObserveTransformNodeID(self.trackerToForcepsLeft.GetID())
      # Enable the button to remove
      self.removeLastFiducialButton_forcepsLeft.enabled = True
    except:
      print('ERROR: TrackerToForcepsL not found')

    self.logic.reduceVisibilityOtherModels(modelName='ForcepsL')

    try:
      self.VirtualFiducials_forcepsLeft = slicer.util.getNode('VirtualFiducials_forcepsLeft')
      # # hide other fiducials and show the corresponding ones
      # self.VirtualFiducials_forcepsRight.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyHead.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyBody.SetDisplayVisibility(0)
      # self.virtualFiducials_mother.SetDisplayVisibility(0)
      # self.VirtualFiducials_forcepsLeft.SetDisplayVisibility(1)

      # make model fiducials visible
      fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
      for fiducial_node in fiducials_list:
        if fiducial_node.GetName() == 'VirtualFiducials_forcepsLeft' or fiducial_node.GetName() == 'RealFiducials_forcepsLeft':
          fiducial_node.SetDisplayVisibility(1)
        else:
          fiducial_node.SetDisplayVisibility(0)

      try:
        self.realFiducials_forcepsLeft = slicer.util.getNode('RealFiducials_forcepsLeft')
      # Create the list if it doesn't exist
      except:
        self.realFiducials_forcepsLeft = slicer.vtkMRMLMarkupsFiducialNode()  
        self.realFiducials_forcepsLeft.SetName('RealFiducials_forcepsLeft')
        slicer.mrmlScene.AddNode(self.realFiducials_forcepsLeft)
        self.realFiducials_forcepsLeft.GetDisplayNode().SetColor(1,0,0)
      
      # apply transform of reference to fiducials so that the keep the same despite of patient movements
      self.realFiducials_forcepsLeft.SetAndObserveTransformNodeID(self.trackerToForcepsLeft.GetID())

      self.numberOfRealFiducials_forcepsLeft = self.numberOfRealFiducials_forcepsLeft + 1
      numberOfVirtualFiducials = self.VirtualFiducials_forcepsLeft.GetNumberOfFiducials()
      numberOfFiducialsLeft = numberOfVirtualFiducials - self.numberOfRealFiducials_forcepsLeft
      self.placeRealFiducialsButton_forcepsLeft.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      
      # read pointertip position and add fiducial to the list
      # get transform
      m = vtk.vtkMatrix4x4()
      m.Identity()
      self.pointerTipToPointer.GetMatrixTransformToWorld(m)
      # get the values of the last column to add them as the new markup point
      self.realFiducials_forcepsLeft.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

      if self.numberOfRealFiducials_forcepsLeft == numberOfVirtualFiducials:
        self.placeRealFiducialsButton_forcepsLeft.setText('Added Fiducials: '+ str(self.numberOfRealFiducials_forcepsLeft))
        self.placeRealFiducialsButton_forcepsLeft.enabled = False
        self.repeatButton_forcepsLeft.enabled = True
        self.registrationButton_forcepsLeft.enabled = True
        self.pointerToTracker.SetAndObserveTransformNodeID(None)
        self.realFiducials_forcepsLeft.SetAndObserveTransformNodeID(None)
    except:
      print('ERROR: Virtual Fiducials not found')


  def onRemoveLastFiducialButtonClicked_forcepsLeft(self):
    logging.debug('onRemoveLastFiducialButtonClicked_forcepsLeft')

    if not self.realFiducials_forcepsLeft:
      print('ERROR: RealFiducials_forcepsLeft not found')
    else:
      # get the position of the last fiducial
      numberOfRealFiducials_forcepsLeft = self.realFiducials_forcepsLeft.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials_forcepsLeft - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:
        numberOfVirtualFiducials_forcepsLeft = self.VirtualFiducials_forcepsLeft.GetNumberOfFiducials()
        # allow to place more fiducials if one was removed (for the case you remove the last one)
        if (numberOfRealFiducials_forcepsLeft-1) < numberOfVirtualFiducials_forcepsLeft:
          # disable registration as you won't have the maximum needed
          self.registrationButton_forcepsLeft.enabled = False
          self.placeRealFiducialsButton_forcepsLeft.enabled = True
        # delete the corresponding markup
        self.realFiducials_forcepsLeft.RemoveMarkup(positionDelete)
        # refresh the number of real fiducials
        self.numberOfRealFiducials_forcepsLeft = self.numberOfRealFiducials_forcepsLeft - 1
        # correct the button text indicating the number of fiducials left
        numberOfFiducialsLeft = numberOfVirtualFiducials_forcepsLeft - self.numberOfRealFiducials_forcepsLeft
        self.placeRealFiducialsButton_forcepsLeft.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      if positionDelete <= 0:
        self.removeLastFiducialButton_forcepsLeft.enabled = False

  def onRepeatButtonClicked_forcepsLeft(self):
    logging.debug('onRepeatButtonClicked_forcepsLeft')

    self.numberOfRealFiducials_forcepsLeft = 0
    self.realFiducials_forcepsLeft.RemoveAllMarkups()
    self.placeRealFiducialsButton_forcepsLeft.enabled = True
    self.placeRealFiducialsButton_forcepsLeft.setText('Place Real Fiducials')
    self.repeatButton_forcepsLeft.enabled = False
    self.registrationButton_forcepsLeft.enabled = False
    self.saveRegistrationButton_forcepsLeft.enabled = False
    self.removeLastFiducialButton_forcepsLeft.enabled = False
    
    # if ForcepsLeftModelToForcepsLeft was created, remove it
    forcepsLeftModelToForcepsLeft = slicer.util.getNode('ForcepsLeftModelToForcepsLeft')
    if forcepsLeftModelToForcepsLeft:
      slicer.mrmlScene.RemoveNode(forcepsLeftModelToForcepsLeft)

  def onLoadTransformButtonClicked_forcepsLeft(self):
    logging.debug('onLoadTransformButtonClicked_forcepsLeft')

    try:
      self.forcepsLeftModelToForcepsLeft = slicer.util.getNode('ForcepsLeftModelToForcepsLeft')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'ForcepsLeftModelToForcepsLeft.h5')
      try:
        self.forcepsLeftModelToForcepsLeft = slicer.util.getNode(pattern="ForcepsLeftModelToForcepsLeft")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ForcepsLeftModelToForcepsLeft not found')

    # APPLY EXISTING TRANFORMS
    if self.forcepsLeftModel and self.forcepsLeftModelToForcepsLeft and self.forcepsLeftToTracker:
      self.forcepsLeftModel.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.forcepsLeftModelToForcepsLeft.SetAndObserveTransformNodeID(self.forcepsLeftToTracker.GetID())
    else:
        print('Unable to apply or load transform ForcepsLeftModelToForcepsLeft')
    

  def onRegistrationButtonClicked_forcepsLeft(self):
    logging.debug('onRegistrationButtonClicked_forcepsLeft')

    try:
      self.forcepsLeftModelToForcepsLeft = slicer.util.getNode('ForcepsLeftModelToForcepsLeft')
    except:
      print('Creating ForcepsLeftModelToForcepsLeft')
      self.forcepsLeftModelToForcepsLeft = slicer.vtkMRMLLinearTransformNode()
      self.forcepsLeftModelToForcepsLeft.SetName('ForcepsLeftModelToForcepsLeft')
      slicer.mrmlScene.AddNode(self.forcepsLeftModelToForcepsLeft)
      
    movingFiducials = slicer.util.getNode('VirtualFiducials_forcepsLeft')
    movingFiducials.SetDisplayVisibility(1)
    fixedFiducials = slicer.util.getNode('RealFiducials_forcepsLeft')
    fixedFiducials.SetDisplayVisibility(1)      

    rms = self.logic.fiducialRegistration(self.forcepsLeftModelToForcepsLeft, fixedFiducials, movingFiducials, "Rigid")
    
    self.forcepsLeftModelToForcepsLeft = slicer.util.getNode('ForcepsLeftModelToForcepsLeft')

    self.rmseText_forcepsLeft.setText(rms)
    self.applyRegistrationButton_forcepsLeft.enabled = True

  def onApplyRegistrationButtonClicked_forcepsLeft(self):
    logging.debug('onApplyRegistrationButtonClicked_forcepsLeft')

    if not self.forcepsLeftModelToForcepsLeft:
      print('ERROR: forcepsLeftModelToForcepsLeft not found')
    else:
      self.VirtualFiducials_forcepsLeft.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.forcepsLeftModel.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.forcepsLeftModelToForcepsLeft.SetAndObserveTransformNodeID(self.forcepsLeftToTracker.GetID())
      self.saveRegistrationButton_forcepsLeft.enabled = True
      self.applyRegistrationButton_forcepsLeft.enabled = False
      #Show models that were invisible
      self.forcepsLeftModel.GetModelDisplayNode().VisibilityOn()
      # Hide Real Fiducials
      self.realFiducials_forcepsLeft.SetDisplayVisibility(0)
      # Center view in models
      threeDWidget = self.layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()

  def onSaveRegistrationButtonClicked_forcepsLeft(self):
    logging.debug('onSaveRegistrationButtonClicked_forcepsLeft')

    res = self.logic.saveData('ForcepsLeftModelToForcepsLeft',self.DeliveryTrainingSetupPath_data,'ForcepsLeftModelToForcepsLeft.h5')
    if res:
      print('Saved correctly')
      self.saveRegistrationButton_forcepsLeft.enabled = False
    else:
      print('ERROR: Unable to save ForcepsLeftModelToForcepsLeft')

  # FORCEPS RIGHT

  def onPlaceRealFiducialsButtonClicked_forcepsRight(self):
    logging.debug('onPlaceRealFiducialsButtonClicked_forcepsRight')

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      self.trackerToForcepsRight = slicer.util.getNode('TrackerToForcepsR')
      self.pointerToTracker.SetAndObserveTransformNodeID(self.trackerToForcepsRight.GetID())
      # Enable the button to remove
      self.removeLastFiducialButton_forcepsRight.enabled = True
    except:
      print('ERROR: TrackerToForcepsR not found')

    self.logic.reduceVisibilityOtherModels(modelName='ForcepsR')

    try:
      self.VirtualFiducials_forcepsRight = slicer.util.getNode('VirtualFiducials_forcepsRight')
      # # hide other fiducials and show the corresponding ones
      # self.VirtualFiducials_forcepsLeft.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyHead.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyBody.SetDisplayVisibility(0)
      # self.virtualFiducials_mother.SetDisplayVisibility(0)
      # self.VirtualFiducials_forcepsRight.SetDisplayVisibility(1)
      # make model fiducials visible
      fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
      for fiducial_node in fiducials_list:
        if fiducial_node.GetName() == 'VirtualFiducials_forcepsRight' or fiducial_node.GetName() == 'RealFiducials_forcepsRight':
          fiducial_node.SetDisplayVisibility(1)
        else:
          fiducial_node.SetDisplayVisibility(0)
      try:
        self.realFiducials_forcepsRight = slicer.util.getNode('RealFiducials_forcepsRight')
      # Create the list if it doesn't exist
      except:
        self.realFiducials_forcepsRight = slicer.vtkMRMLMarkupsFiducialNode()  
        self.realFiducials_forcepsRight.SetName('RealFiducials_forcepsRight')
        slicer.mrmlScene.AddNode(self.realFiducials_forcepsRight)
        self.realFiducials_forcepsRight.GetDisplayNode().SetColor(1,0,0)
      
      # apply transform of reference to fiducials so that the keep the same despite of patient movements
      self.realFiducials_forcepsRight.SetAndObserveTransformNodeID(self.trackerToForcepsRight.GetID())

      self.numberOfRealFiducials_forcepsRight = self.numberOfRealFiducials_forcepsRight + 1
      numberOfVirtualFiducials = self.VirtualFiducials_forcepsRight.GetNumberOfFiducials()
      numberOfFiducialsRight = numberOfVirtualFiducials - self.numberOfRealFiducials_forcepsRight
      self.placeRealFiducialsButton_forcepsRight.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')
      
      # read pointertip position and add fiducial to the list
      # get transform
      m = vtk.vtkMatrix4x4()
      m.Identity()
      self.pointerTipToPointer.GetMatrixTransformToWorld(m)
      # get the values of the last column to add them as the new markup point
      self.realFiducials_forcepsRight.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

      if self.numberOfRealFiducials_forcepsRight == numberOfVirtualFiducials:
        self.placeRealFiducialsButton_forcepsRight.setText('Added Fiducials: '+ str(self.numberOfRealFiducials_forcepsRight))
        self.placeRealFiducialsButton_forcepsRight.enabled = False
        self.repeatButton_forcepsRight.enabled = True
        self.registrationButton_forcepsRight.enabled = True
        self.pointerToTracker.SetAndObserveTransformNodeID(None)
        self.realFiducials_forcepsRight.SetAndObserveTransformNodeID(None)
    except:
      print('ERROR: Virtual Fiducials not found')


  def onRemoveLastFiducialButtonClicked_forcepsRight(self):
    logging.debug('onRemoveLastFiducialButtonClicked_forcepsRight')

    if not self.realFiducials_forcepsRight:
      print('ERROR: RealFiducials_forcepsRight not found')
    else:
      # get the position of the last fiducial
      numberOfRealFiducials_forcepsRight = self.realFiducials_forcepsRight.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials_forcepsRight - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:
        numberOfVirtualFiducials_forcepsRight = self.VirtualFiducials_forcepsRight.GetNumberOfFiducials()
        # allow to place more fiducials if one was removed (for the case you remove the last one)
        if (numberOfRealFiducials_forcepsRight-1) < numberOfVirtualFiducials_forcepsRight:
          # disable registration as you won't have the maximum needed
          self.registrationButton_forcepsRight.enabled = False
          self.placeRealFiducialsButton_forcepsRight.enabled = True
        # delete the corresponding markup
        self.realFiducials_forcepsRight.RemoveMarkup(positionDelete)
        # refresh the number of real fiducials
        self.numberOfRealFiducials_forcepsRight = self.numberOfRealFiducials_forcepsRight - 1
        # correct the button text indicating the number of fiducials right
        numberOfFiducialsLeft = numberOfVirtualFiducials_forcepsRight - self.numberOfRealFiducials_forcepsRight
        self.placeRealFiducialsButton_forcepsRight.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      if positionDelete <= 0:
        self.removeLastFiducialButton_forcepsRight.enabled = False

  def onRepeatButtonClicked_forcepsRight(self):
    logging.debug('onRepeatButtonClicked_forcepsRight')

    self.numberOfRealFiducials_forcepsRight = 0
    self.realFiducials_forcepsRight.RemoveAllMarkups()
    self.placeRealFiducialsButton_forcepsRight.enabled = True
    self.placeRealFiducialsButton_forcepsRight.setText('Place Real Fiducials')
    self.repeatButton_forcepsRight.enabled = False
    self.registrationButton_forcepsRight.enabled = False
    self.saveRegistrationButton_forcepsRight.enabled = False
    self.removeLastFiducialButton_forcepsRight.enabled = False
    
    # if ForcepsRightModelToForcepsRight was created, remove it
    forcepsRightModelToForcepsRight = slicer.util.getNode('ForcepsRightModelToForcepsRight')
    if forcepsRightModelToForcepsRight:
      slicer.mrmlScene.RemoveNode(forcepsRightModelToForcepsRight)

  def onLoadTransformButtonClicked_forcepsRight(self):
    logging.debug('onLoadTransformButtonClicked_forcepsRight')

    try:
      self.forcepsRightModelToForcepsRight = slicer.util.getNode('ForcepsRightModelToForcepsRight')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'ForcepsRightModelToForcepsRight.h5')
      try:
        self.forcepsRightModelToForcepsRight = slicer.util.getNode(pattern="ForcepsRightModelToForcepsRight")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ForcepsRightModelToForcepsRight not found')

    # APPLY EXISTING TRANFORMS
    if self.forcepsRightModel and self.forcepsRightModelToForcepsRight and self.forcepsRightToTracker:
      self.forcepsRightModel.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.forcepsRightModelToForcepsRight.SetAndObserveTransformNodeID(self.forcepsRightToTracker.GetID())
      # collapse Forceps area
      self.ForcepsGroupBox.collapsed = True
      self.BabyGroupBox.collapsed = False
    else:
        print('Unable to apply or load transform ForcepsRightModelToForcepsRight')
    

  def onRegistrationButtonClicked_forcepsRight(self):
    logging.debug('onRegistrationButtonClicked_forcepsRight')

    
    try:
      self.forcepsRightModelToForcepsRight = slicer.util.getNode('ForcepsRightModelToForcepsRight')
    except:
      print('Creating ForcepsRightModelToForcepsRight')
      self.forcepsRightModelToForcepsRight = slicer.vtkMRMLLinearTransformNode()
      self.forcepsRightModelToForcepsRight.SetName('ForcepsRightModelToForcepsRight')
      slicer.mrmlScene.AddNode(self.forcepsRightModelToForcepsRight)
      
    movingFiducials = slicer.util.getNode('VirtualFiducials_forcepsRight')
    movingFiducials.SetDisplayVisibility(1)
    fixedFiducials = slicer.util.getNode('RealFiducials_forcepsRight')
    fixedFiducials.SetDisplayVisibility(1)      

    rms = self.logic.fiducialRegistration(self.forcepsRightModelToForcepsRight, fixedFiducials, movingFiducials, "Rigid")
    
    self.forcepsRightModelToForcepsRight = slicer.util.getNode('ForcepsRightModelToForcepsRight')

    self.rmseText_forcepsRight.setText(rms)
    self.applyRegistrationButton_forcepsRight.enabled = True

  def onApplyRegistrationButtonClicked_forcepsRight(self):
    logging.debug('onApplyRegistrationButtonClicked_forcepsRight')
    
    if not self.forcepsRightModelToForcepsRight:
      print('ERROR: forcepsRightModelToForcepsRight not found')
    else:
      self.VirtualFiducials_forcepsRight.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.forcepsRightModel.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.forcepsRightModelToForcepsRight.SetAndObserveTransformNodeID(self.forcepsRightToTracker.GetID())
      self.saveRegistrationButton_forcepsRight.enabled = True
      self.applyRegistrationButton_forcepsRight.enabled = False
      #Show models that were invisible
      self.forcepsRightModel.GetModelDisplayNode().VisibilityOn()
      # Hide Real Fiducials
      self.realFiducials_forcepsRight.SetDisplayVisibility(0)
      # Center view in models
      threeDWidget = self.layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()

  def onSaveRegistrationButtonClicked_forcepsRight(self):
    logging.debug('onSaveRegistrationButtonClicked_forcepsRight')

    res = self.logic.saveData('ForcepsRightModelToForcepsRight',self.DeliveryTrainingSetupPath_data,'ForcepsRightModelToForcepsRight.h5')
    if res:
      print('Saved correctly')
      self.saveRegistrationButton_forcepsRight.enabled = False
    else:
      print('ERROR: Unable to save ForcepsRightModelToForcepsRight')

    # collapse Forceps area
    self.ForcepsGroupBox.collapsed = True
    self.BabyGroupBox.collapsed = False

# BABY HEAD

  def onPlaceRealFiducialsButtonClicked_babyHead(self):
    logging.debug('onPlaceRealFiducialsButtonClicked_babyHead')

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      self.trackerToBabyHead = slicer.util.getNode('TrackerToBabyHead')
      self.pointerToTracker.SetAndObserveTransformNodeID(self.trackerToBabyHead.GetID())
      # Enable the button to remove
      self.removeLastFiducialButton_babyHead.enabled = True
    except:
      print('ERROR: TrackerToBabyHead not found')
    
    self.logic.reduceVisibilityOtherModels(modelName='BabyHead')

    try:
      if self.guideRadioButton.isChecked():
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead_guide'
        #Make guides visible
        # self.eyesGuideDisplay.SetOpacity(1)
        # self.leftEarGuideDisplay.SetOpacity(1)
        # self.rightEarGuideDisplay.SetOpacity(1)
        # self.fontanelleGuideDisplay.SetOpacity(1)
        # # self.fontanelle2GuideDisplay.SetOpacity(1)
      else:
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead'

      self.VirtualFiducials_babyHead = slicer.util.getNode(self.fiducialsName_babyHead)
      # # hide other fiducials and show the corresponding ones
      # self.VirtualFiducials_forcepsLeft.SetDisplayVisibility(0)
      # self.VirtualFiducials_forcepsRight.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyBody.SetDisplayVisibility(0)
      # self.virtualFiducials_mother.SetDisplayVisibility(0)
      # self.VirtualFiducials_babyHead.SetDisplayVisibility(1)

      # make model fiducials visible
      fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
      for fiducial_node in fiducials_list:
        if fiducial_node.GetName() == self.fiducialsName_babyHead or fiducial_node.GetName() == 'RealFiducials_babyHead':
          fiducial_node.SetDisplayVisibility(1)
        else:
          fiducial_node.SetDisplayVisibility(0)

      try:
        self.realFiducials_babyHead = slicer.util.getNode('RealFiducials_babyHead')
      # Create the list if it doesn't exist
      except:
        self.realFiducials_babyHead = slicer.vtkMRMLMarkupsFiducialNode()  
        self.realFiducials_babyHead.SetName('RealFiducials_babyHead')
        slicer.mrmlScene.AddNode(self.realFiducials_babyHead)
        self.realFiducials_babyHead.GetDisplayNode().SetColor(1,0,0)
      
      # apply transform of reference to fiducials so that the keep the same despite of patient movements
      self.realFiducials_babyHead.SetAndObserveTransformNodeID(self.trackerToBabyHead.GetID())

      self.numberOfRealFiducials_babyHead = self.numberOfRealFiducials_babyHead + 1
      numberOfVirtualFiducials = self.VirtualFiducials_babyHead.GetNumberOfFiducials()
      numberOfFiducialsRight = numberOfVirtualFiducials - self.numberOfRealFiducials_babyHead
      self.placeRealFiducialsButton_babyHead.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')
      
      # read pointertip position and add fiducial to the list
      # get transform
      m = vtk.vtkMatrix4x4()
      m.Identity()
      self.pointerTipToPointer.GetMatrixTransformToWorld(m)
      # get the values of the last column to add them as the new markup point
      self.realFiducials_babyHead.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

      if self.numberOfRealFiducials_babyHead == numberOfVirtualFiducials:
        self.placeRealFiducialsButton_babyHead.setText('Added Fiducials: '+ str(self.numberOfRealFiducials_babyHead))
        self.placeRealFiducialsButton_babyHead.enabled = False
        self.repeatButton_babyHead.enabled = True
        self.registrationButton_babyHead.enabled = True
        self.pointerToTracker.SetAndObserveTransformNodeID(None)
        self.realFiducials_babyHead.SetAndObserveTransformNodeID(None)
    except:
      print('ERROR: Virtual Fiducials not found')

  def onRemoveLastFiducialButtonClicked_babyHead(self):
    logging.debug('onRemoveLastFiducialButtonClicked_babyHead')

    if not self.realFiducials_babyHead:
      print('ERROR: RealFiducials_babyHead not found')
    else:
      # get the position of the last fiducial
      numberOfRealFiducials_babyHead = self.realFiducials_babyHead.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials_babyHead - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:
        numberOfVirtualFiducials_babyHead = self.VirtualFiducials_babyHead.GetNumberOfFiducials()
        # allow to place more fiducials if one was removed (for the case you remove the last one)
        if (numberOfRealFiducials_babyHead-1) < numberOfVirtualFiducials_babyHead:
          # disable registration as you won't have the maximum needed
          self.registrationButton_babyHead.enabled = False
          self.placeRealFiducialsButton_babyHead.enabled = True
        # delete the corresponding markup
        self.realFiducials_babyHead.RemoveMarkup(positionDelete)
        # refresh the number of real fiducials
        self.numberOfRealFiducials_babyHead = self.numberOfRealFiducials_babyHead - 1
        # correct the button text indicating the number of fiducials right
        numberOfFiducialsLeft = numberOfVirtualFiducials_babyHead - self.numberOfRealFiducials_babyHead
        self.placeRealFiducialsButton_babyHead.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      if positionDelete <= 0:
        self.removeLastFiducialButton_babyHead.enabled = False

  def onRepeatButtonClicked_babyHead(self):
    logging.debug('onRepeatButtonClicked_babyHead')

    self.numberOfRealFiducials_babyHead = 0
    self.realFiducials_babyHead.RemoveAllMarkups()
    self.placeRealFiducialsButton_babyHead.enabled = True
    self.placeRealFiducialsButton_babyHead.setText('Place Real Fiducials')
    self.repeatButton_babyHead.enabled = False
    self.registrationButton_babyHead.enabled = False
    self.saveRegistrationButton_babyHead.enabled = False
    self.removeLastFiducialButton_babyHead.enabled = False

    if self.guideRadioButton.isChecked():
        #Make guides visible
        self.eyesGuideDisplay.SetOpacity(1)
        self.leftEarGuideDisplay.SetOpacity(1)
        self.rightEarGuideDisplay.SetOpacity(1)
        self.fontanelleGuideDisplay.SetOpacity(1)
        # self.fontanelle2GuideDisplay.SetOpacity(1)
    
    # if BabyHeadModelToBabyHead was created, remove it
    babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
    if babyHeadModelToBabyHead:
      slicer.mrmlScene.RemoveNode(babyHeadModelToBabyHead)


  def onLoadTransformButtonClicked_babyHead(self):
    logging.debug('onLoadTransformButtonClicked_babyHead')

    try:
      self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'BabyHeadModelToBabyHead.h5')
      try:
        self.babyHeadModelToBabyHead = slicer.util.getNode(pattern="BabyHeadModelToBabyHead")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyHeadModelToBabyHead not found')

    # APPLY EXISTING TRANFORMS
    if self.babyHeadModel and self.babyHeadModelToBabyHead and self.babyHeadToTracker:
      self.babyHeadModel.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.babyHeadModelToBabyHead.SetAndObserveTransformNodeID(self.babyHeadToTracker.GetID())
      # collapse Baby area
      self.BabyGroupBox.collapsed = True
      self.MotherGroupBox.collapsed = False

      if self.guideRadioButton.isChecked():
        #Make guides invisible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)

    else:
        print('Unable to apply or load transform BabyHeadModelToBabyHead')
    

  def onRegistrationButtonClicked_babyHead(self):
    logging.debug('onRegistrationButtonClicked_babyHead')

    try:
      self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
    except:
      print('Creating BabyHeadModelToBabyHead')
      self.babyHeadModelToBabyHead = slicer.vtkMRMLLinearTransformNode()
      self.babyHeadModelToBabyHead.SetName('BabyHeadModelToBabyHead')
      slicer.mrmlScene.AddNode(self.babyHeadModelToBabyHead)

    if self.guideRadioButton.isChecked():
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead_guide'
    else:
        self.fiducialsName_babyHead = 'VirtualFiducials_babyHead'
      
    movingFiducials = slicer.util.getNode(self.fiducialsName_babyHead)
    movingFiducials.SetDisplayVisibility(1)
    fixedFiducials = slicer.util.getNode('RealFiducials_babyHead')
    fixedFiducials.SetDisplayVisibility(1)      

    rms = self.logic.fiducialRegistration(self.babyHeadModelToBabyHead, fixedFiducials, movingFiducials, "Rigid")
    
    self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')

    self.rmseText_babyHead.setText(rms)
    self.applyRegistrationButton_babyHead.enabled = True

  def onApplyRegistrationButtonClicked_babyHead(self):
    logging.debug('onApplyRegistrationButtonClicked_babyHead')
    
    if not self.babyHeadModelToBabyHead:
      print('ERROR: babyHeadModelToBabyHead not found')
    else:
      self.VirtualFiducials_babyHead.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.babyHeadModel.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.babyHeadModelToBabyHead.SetAndObserveTransformNodeID(self.babyHeadToTracker.GetID())
      self.saveRegistrationButton_babyHead.enabled = True
      self.applyRegistrationButton_babyHead.enabled = False
      #Show models that were invisible
      self.babyHeadModel.GetModelDisplayNode().VisibilityOn()
      # Hide Real Fiducials
      self.realFiducials_babyHead.SetDisplayVisibility(0)
      # Center view in models
      threeDWidget = self.layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()

      if self.guideRadioButton.isChecked():
        #Make guides invisible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)

  def onSaveRegistrationButtonClicked_babyHead(self):
    logging.debug('onSaveRegistrationButtonClicked_babyHead')

    res = self.logic.saveData('BabyHeadModelToBabyHead',self.DeliveryTrainingSetupPath_data,'BabyHeadModelToBabyHead.h5')
    if res:
      print('Saved correctly')
      self.saveRegistrationButton_babyHead.enabled = False
    else:
      print('ERROR: Unable to save BabyHeadModelToBabyHead')

    # # collapse Baby area
    # self.BabyGroupBox.collapsed = True
    # self.MotherGroupBox.collapsed = False


  # BABY BODY

  def onPlaceRealFiducialsButtonClicked_babyBody(self):
    logging.debug('onPlaceRealFiducialsButtonClicked_babyBody')

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      self.trackerToBabyBody = slicer.util.getNode('TrackerToBabyBody')
      self.pointerToTracker.SetAndObserveTransformNodeID(self.trackerToBabyBody.GetID())

      # Enable the button to remove
      self.removeLastFiducialButton_babyBody.enabled = True

      if self.develRadioButton.isChecked():
        # Use babyHead
        modelNameVisibility = 'BabyHead'
      else: 
        # Use babyBody
        modelNameVisibility = 'BabyBody'

      self.logic.reduceVisibilityOtherModels(modelNameVisibility)

      if self.develRadioButton.isChecked():
        try:
          if self.guideRadioButton.isChecked():
            self.fiducialsName_babyBody = 'VirtualFiducials_babyHead_guide'
            # #Make guides visible
            # self.eyesGuideDisplay.SetOpacity(1)
            # self.leftEarGuideDisplay.SetOpacity(1)
            # self.rightEarGuideDisplay.SetOpacity(1)
            # self.fontanelleGuideDisplay.SetOpacity(1)
            # # self.fontanelle2GuideDisplay.SetOpacity(1)
          else:
            self.fiducialsName_babyBody = 'VirtualFiducials_babyHead'

          virtualFiducials = slicer.util.getNode(self.fiducialsName_babyBody)
          numberOfVirtualFiducials = virtualFiducials.GetNumberOfFiducials()
        except:
          print('ERROR: Virtual Fiducials for babybody (babyHead) not found')         
      else:
        try:
          if self.guideRadioButton.isChecked():
            self.fiducialsName_babyBody = 'VirtualFiducials_babyBody_guide'
            # #Make guides visible
            # self.frontGuideDisplay.SetOpacity(1)
            # self.backGuideDisplay.SetOpacity(1)
            # self.bellyGuideDisplay.SetOpacity(1)
          else:
            self.fiducialsName_babyBody = 'VirtualFiducials_babyBody'

          virtualFiducials = slicer.util.getNode(self.fiducialsName_babyBody)
          numberOfVirtualFiducials = virtualFiducials.GetNumberOfFiducials()
        except:
          print('ERROR: Virtual Fiducials baby body not found')
    
        #   # hide other fiducials and show the corresponding ones
        #   self.virtualFiducials_forcepsLeft.SetDisplayVisibility(0)
        #   self.virtualFiducials_forcepsRight.SetDisplayVisibility(0)
        #   self.VirtualFiducials_babyHead.SetDisplayVisibility(1)

      # make model fiducials visible
      fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
      for fiducial_node in fiducials_list:
        if fiducial_node.GetName() == self.fiducialsName_babyBody or fiducial_node.GetName() == 'RealFiducials_babyBody':
          fiducial_node.SetDisplayVisibility(1)
        else:
          fiducial_node.SetDisplayVisibility(0)

      try:
        self.realFiducials_babyBody = slicer.util.getNode('RealFiducials_babyBody')
      # Create the list if it doesn't exist
      except:
        self.realFiducials_babyBody = slicer.vtkMRMLMarkupsFiducialNode()  
        self.realFiducials_babyBody.SetName('RealFiducials_babyBody')
        slicer.mrmlScene.AddNode(self.realFiducials_babyBody)
        self.realFiducials_babyBody.GetDisplayNode().SetColor(1,0,0)
          
      # apply transform of reference to fiducials so that the keep the same despite of patient movements
      self.realFiducials_babyBody.SetAndObserveTransformNodeID(self.trackerToBabyBody.GetID())

      self.numberOfRealFiducials_babyBody = self.numberOfRealFiducials_babyBody + 1
      # numberOfVirtualFiducials = self.VirtualFiducials_babyHead.GetNumberOfFiducials()
      numberOfFiducialsLeft = numberOfVirtualFiducials - self.numberOfRealFiducials_babyBody
      self.placeRealFiducialsButton_babyBody.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      
      # read pointertip position and add fiducial to the list
      # get transform
      m = vtk.vtkMatrix4x4()
      m.Identity()
      self.pointerTipToPointer.GetMatrixTransformToWorld(m)
      # get the values of the last column to add them as the new markup point
      self.realFiducials_babyBody.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

      if self.numberOfRealFiducials_babyBody == numberOfVirtualFiducials:
        self.placeRealFiducialsButton_babyBody.setText('Added Fiducials: '+ str(self.numberOfRealFiducials_babyBody))
        self.placeRealFiducialsButton_babyBody.enabled = False
        self.repeatButton_babyBody.enabled = True
        self.registrationButton_babyBody.enabled = True
        self.pointerToTracker.SetAndObserveTransformNodeID(None)
        self.realFiducials_babyBody.SetAndObserveTransformNodeID(None)
    except:
      print('ERROR: TrackerToBabyBody not found')



  def onRemoveLastFiducialButtonClicked_babyBody(self):
    logging.debug('onRemoveLastFiducialButtonClicked_babyBody')

    if not self.realFiducials_babyBody:
      print('ERROR: RealFiducials_babyBody not found')
    else:
      # get the position of the last fiducial
      numberOfRealFiducials_babyBody = self.realFiducials_babyBody.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials_babyBody - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:

        # FIXED

        if self.develRadioButton.isChecked():
          numberOfVirtualFiducials = self.VirtualFiducials_babyHead.GetNumberOfFiducials() # Either guide or not
        else:
          numberOfVirtualFiducials = self.VirtualFiducials_babyBody.GetNumberOfFiducials()
        # allow to place more fiducials if one was removed (for the case you remove the last one)
        if (numberOfRealFiducials_babyBody-1) < numberOfVirtualFiducials:
          # disable registration as you won't have the maximum needed
          self.registrationButton_babyBody.enabled = False
          self.placeRealFiducialsButton_babyBody.enabled = True
        # delete the corresponding markup
        self.realFiducials_babyBody.RemoveMarkup(positionDelete)
        # refresh the number of real fiducials
        self.numberOfRealFiducials_babyBody = self.numberOfRealFiducials_babyBody - 1
        # correct the button text indicating the number of fiducials right
        numberOfFiducialsLeft = numberOfVirtualFiducials - self.numberOfRealFiducials_babyBody
        self.placeRealFiducialsButton_babyBody.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      if positionDelete <= 0:
        self.removeLastFiducialButton_babyBody.enabled = False

  def onRepeatButtonClicked_babyBody(self):
    logging.debug('onRepeatButtonClicked_babyBody')

    self.numberOfRealFiducials_babyBody = 0
    self.realFiducials_babyBody.RemoveAllMarkups()
    self.placeRealFiducialsButton_babyBody.enabled = True
    self.placeRealFiducialsButton_babyBody.setText('Place Real Fiducials')
    self.repeatButton_babyBody.enabled = False
    self.registrationButton_babyBody.enabled = False
    self.saveRegistrationButton_babyBody.enabled = False
    self.removeLastFiducialButton_babyBody.enabled = False
    
    # if BabyBodyModelToBabyBody was created, remove it
    babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
    if babyBodyModelToBabyBody:
      slicer.mrmlScene.RemoveNode(babyBodyModelToBabyBody)

    if self.guideRadioButton.isChecked(): #guides on
      if self.develRadioButton.isChecked(): #using baby head fiducials
        self.eyesGuideDisplay.SetOpacity(1)
        self.leftEarGuideDisplay.SetOpacity(1)
        self.rightEarGuideDisplay.SetOpacity(1)
        self.fontanelleGuideDisplay.SetOpacity(1)
        # self.fontanelle2GuideDisplay.SetOpacity(1)
      else: #using baby body fiducials
        self.frontGuideDisplay.SetOpacity(1)
        self.backGuideDisplay.SetOpacity(1)
        self.bellyGuideDisplay.SetOpacity(1)



  def onLoadTransformButtonClicked_babyBody(self):
    logging.debug('onLoadTransformButtonClicked_babyBody')

    try:
      self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'BabyBodyModelToBabyBody.h5')
      try:
        self.babyBodyModelToBabyBody = slicer.util.getNode(pattern="BabyBodyModelToBabyBody")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyBodyModelToBabyBody not found')

    # APPLY EXISTING TRANFORMS
    if self.babyBodyModel and self.babyBodyModelToBabyBody and self.babyBodyToTracker:
      self.babyBodyModel.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.babyBodyModelToBabyBody.SetAndObserveTransformNodeID(self.babyBodyToTracker.GetID())
      # collapse Baby area
      self.BabyGroupBox.collapsed = True
      self.MotherGroupBox.collapsed = False

      if self.guideRadioButton.isChecked(): #guides on
        if self.develRadioButton.isChecked(): #using baby head fiducials
          self.eyesGuideDisplay.SetOpacity(0)
          self.leftEarGuideDisplay.SetOpacity(0)
          self.rightEarGuideDisplay.SetOpacity(0)
          self.fontanelleGuideDisplay.SetOpacity(0)
          # self.fontanelle2GuideDisplay.SetOpacity(0)
        else: #using baby body fiducials
          self.frontGuideDisplay.SetOpacity(0)
          self.backGuideDisplay.SetOpacity(0)
          self.bellyGuideDisplay.SetOpacity(0)

    else:
        print('Unable to apply or load transform BabyBodyModelToBabyBody')
    

  def onRegistrationButtonClicked_babyBody(self):
    logging.debug('onRegistrationButtonClicked_babyBody')

    try:
      self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
    except:
      print('Creating BabyBodyModelToBabyBody')
      self.babyBodyModelToBabyBody = slicer.vtkMRMLLinearTransformNode()
      self.babyBodyModelToBabyBody.SetName('BabyBodyModelToBabyBody')
      slicer.mrmlScene.AddNode(self.babyBodyModelToBabyBody)
      
    # FIXED FOR GUIDES
    if self.realRadioButton.isChecked():
      if self.guideRadioButton.isChecked():
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyBody_guide')
      else:
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyBody')
    else:
      if self.guideRadioButton.isChecked():
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyHead_guide')
      else:
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyHead')
    movingFiducials.SetDisplayVisibility(1)
    fixedFiducials = slicer.util.getNode('RealFiducials_babyBody')
    fixedFiducials.SetDisplayVisibility(1)      

    rms = self.logic.fiducialRegistration(self.babyBodyModelToBabyBody, fixedFiducials, movingFiducials, "Rigid")
    
    self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')

    self.rmseText_babyBody.setText(rms)
    self.applyRegistrationButton_babyBody.enabled = True

  def onApplyRegistrationButtonClicked_babyBody(self):
    logging.debug('onApplyRegistrationButtonClicked_babyBody')
    
    if not self.babyBodyModelToBabyBody:
      print('ERROR: babyBodyModelToBabyBody not found')
    else:
      self.VirtualFiducials_babyBody.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.babyBodyModel.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.babyBodyModelToBabyBody.SetAndObserveTransformNodeID(self.babyBodyToTracker.GetID())
      self.saveRegistrationButton_babyBody.enabled = True
      self.applyRegistrationButton_babyBody.enabled = False
      #Show models that were invisible
      self.babyBodyModel.GetModelDisplayNode().VisibilityOn()
      # Hide Real Fiducials
      self.realFiducials_babyBody.SetDisplayVisibility(0)
      # Center view in models
      threeDWidget = self.layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()

      if self.guideRadioButton.isChecked(): #guides on
        if self.develRadioButton.isChecked(): #using baby head fiducials
          #Make guides invisible
          self.eyesGuideDisplay.SetOpacity(0)
          self.leftEarGuideDisplay.SetOpacity(0)
          self.rightEarGuideDisplay.SetOpacity(0)
          self.fontanelleGuideDisplay.SetOpacity(0)
          # self.fontanelle2GuideDisplay.SetOpacity(0)
        else: #using baby body fiducials
          self.frontGuideDisplay.SetOpacity(0)
          self.backGuideDisplay.SetOpacity(0)
          self.bellyGuideDisplay.SetOpacity(0)

  def onSaveRegistrationButtonClicked_babyBody(self):
    logging.debug('onSaveRegistrationButtonClicked_babyBody')

    res = self.logic.saveData('BabyBodyModelToBabyBody',self.DeliveryTrainingSetupPath_data,'BabyBodyModelToBabyBody.h5')
    if res:
      print('Saved correctly')
      self.saveRegistrationButton_babyBody.enabled = False
    else:
      print('ERROR: Unable to save BabyBodyModelToBabyBody')

    # collapse Baby area
    self.BabyGroupBox.collapsed = True
    self.MotherGroupBox.collapsed = False

  # MOTHER

  def onPlaceRealFiducialsButtonClicked_mother(self):
    logging.debug('onPlaceRealFiducialsButtonClicked_mother')

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      self.trackerToMother = slicer.util.getNode('TrackerToMother')
      self.pointerToTracker.SetAndObserveTransformNodeID(self.trackerToMother.GetID())

      # Enable the button to remove
      self.removeLastFiducialButton_mother.enabled = True

      if self.develRadioButton.isChecked():
        # Use babyHead
        modelNameVisibility = 'BabyHead'
      else: 
        # Use mother
        modelNameVisibility = 'Mother'
    
      self.logic.reduceVisibilityOtherModels(modelNameVisibility)


      if self.develRadioButton.isChecked(): #use baby head fiducials
        try:
          if self.guideRadioButton.isChecked(): #use guides
            self.fiducialsName_mother = 'VirtualFiducials_babyHead_guide'
            #Make guides visible
            # self.eyesGuideDisplay.SetOpacity(1)
            # self.leftEarGuideDisplay.SetOpacity(1)
            # self.rightEarGuideDisplay.SetOpacity(1)
            # self.fontanelleGuideDisplay.SetOpacity(1)
            # # self.fontanelle2GuideDisplay.SetOpacity(1)
          else:
            self.fiducialsName_mother = 'VirtualFiducials_babyHead'

          virtualFiducials_mother = slicer.util.getNode(self.fiducialsName_mother)
          numberOfVirtualFiducials = virtualFiducials_mother.GetNumberOfFiducials()
        except:
          print('ERROR: Virtual Fiducials for mother (babyHead) not found')
      else: #use mother fiducials
        try:
          self.fiducialsName_mother = 'VirtualFiducials_mother'
          virtualFiducials_mother = slicer.util.getNode(self.fiducialsName_mother)
          numberOfVirtualFiducials = virtualFiducials_mother.GetNumberOfFiducials()
        except:
          print('ERROR: Virtual Fiducials mother not found')
      
      # make model fiducials visible
      fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
      for fiducial_node in fiducials_list:
        if fiducial_node.GetName() == self.fiducialsName_mother or fiducial_node.GetName() == 'RealFiducials_mother':
          fiducial_node.SetDisplayVisibility(1)
        else:
          fiducial_node.SetDisplayVisibility(0)
      

      try:
        self.realFiducials_mother = slicer.util.getNode('RealFiducials_mother')
      # Create the list if it doesn't exist
      except:
        self.realFiducials_mother = slicer.vtkMRMLMarkupsFiducialNode()  
        self.realFiducials_mother.SetName('RealFiducials_mother')
        slicer.mrmlScene.AddNode(self.realFiducials_mother)
        self.realFiducials_mother.GetDisplayNode().SetColor(1,0,0)
  	      
      # apply transform of reference to fiducials so that they keep the same despite of patient movements
      self.realFiducials_mother.SetAndObserveTransformNodeID(self.trackerToMother.GetID())
      self.numberOfRealFiducials_mother = self.numberOfRealFiducials_mother + 1
        
      numberOfFiducialsLeft = numberOfVirtualFiducials - self.numberOfRealFiducials_mother
      self.placeRealFiducialsButton_mother.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
         
      # read pointertip position and add fiducial to the list
      # get transform
      m = vtk.vtkMatrix4x4()
      m.Identity()
      self.pointerTipToPointer.GetMatrixTransformToWorld(m)
      # get the values of the last column to add them as the new markup point
      self.realFiducials_mother.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

      if self.numberOfRealFiducials_mother == numberOfVirtualFiducials:
        self.placeRealFiducialsButton_mother.setText('Added Fiducials: '+ str(self.numberOfRealFiducials_mother))
        self.placeRealFiducialsButton_mother.enabled = False
        self.repeatButton_mother.enabled = True
        self.registrationButton_mother.enabled = True
        self.pointerToTracker.SetAndObserveTransformNodeID(None)
        self.realFiducials_mother.SetAndObserveTransformNodeID(None)
    except:
      print('ERROR: TrackerToMother not found')

  def onRemoveLastFiducialButtonClicked_mother(self):
    logging.debug('onRemoveLastFiducialButtonClicked_mother')

    if not self.realFiducials_mother:
      print('ERROR: RealFiducials_mother not found')
    else:
      # get the position of the last fiducial
      numberOfRealFiducials_mother = self.realFiducials_mother.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials_mother - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:
        if self.develRadioButton.isChecked():
          numberOfVirtualFiducials_mother = self.VirtualFiducials_babyHead.GetNumberOfFiducials()
        else:
          numberOfVirtualFiducials_mother = self.virtualFiducials_mother.GetNumberOfFiducials()          
        # allow to place more fiducials if one was removed (for the case you remove the last one)
        if (numberOfRealFiducials_mother-1) < numberOfVirtualFiducials_mother:
          # disable registration as you won't have the maximum needed
          self.registrationButton_mother.enabled = False
          self.placeRealFiducialsButton_mother.enabled = True
        # delete the corresponding markup
        self.realFiducials_mother.RemoveMarkup(positionDelete)
        # refresh the number of real fiducials
        self.numberOfRealFiducials_mother = self.numberOfRealFiducials_mother - 1
        # correct the button text indicating the number of fiducials right
        numberOfFiducialsLeft = numberOfVirtualFiducials_mother - self.numberOfRealFiducials_mother
        self.placeRealFiducialsButton_mother.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
      if positionDelete <= 0:
        self.removeLastFiducialButton_mother.enabled = False

  def onRepeatButtonClicked_mother(self):
    logging.debug('onRepeatButtonClicked_mother')

    self.numberOfRealFiducials_mother = 0
    self.realFiducials_mother.RemoveAllMarkups()
    self.placeRealFiducialsButton_mother.enabled = True
    self.placeRealFiducialsButton_mother.setText('Place Real Fiducials')
    self.repeatButton_mother.enabled = False
    self.registrationButton_mother.enabled = False
    self.saveRegistrationButton_mother.enabled = False
    self.removeLastFiducialButton_mother.enabled = False
    
    # if MotherModelToMother was created, remove it
    motherModelToMother = slicer.util.getNode('MotherModelToMother')
    if motherModelToMother:
      slicer.mrmlScene.RemoveNode(motherModelToMother)

    if self.guideRadioButton.isChecked() and self.develRadioButton.isChecked():
      self.eyesGuideDisplay.SetOpacity(1)
      self.leftEarGuideDisplay.SetOpacity(1)
      self.rightEarGuideDisplay.SetOpacity(1)
      self.fontanelleGuideDisplay.SetOpacity(1)
      # self.fontanelle2GuideDisplay.SetOpacity(1)



  def onLoadTransformButtonClicked_mother(self):
    logging.debug('onLoadTransformButtonClicked_mother')

    try:
      self.motherModelToMother = slicer.util.getNode('MotherModelToMother')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'MotherModelToMother.h5')
      try:
        self.motherModelToMother = slicer.util.getNode(pattern="MotherModelToMother")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: MotherModelToMother not found')

    # get motherToTracker
    try:
      self.motherToTracker = slicer.util.getNode('MotherToTracker') # we use the forcepsL sensor for the mother
    except:
      print('ERROR: MotherToTracker not found')

    # APPLY EXISTING TRANFORMS
    if self.motherModel and self.motherTummyModel and self.motherModelToMother and self.motherToTracker:
    # if self.motherModel and self.motherModelToMother:
      self.motherModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherTummyModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherModelToMother.SetAndObserveTransformNodeID(self.motherToTracker.GetID())
      # collapse Mother area
      self.MotherGroupBox.collapsed = True
    else:
        print('Unable to apply or load transform MotherModelToMother')
    

  def onRegistrationButtonClicked_mother(self):
    logging.debug('onRegistrationButtonClicked_mother')

    try:
      self.motherModelToMother = slicer.util.getNode('MotherModelToMother')
    except:
      print('Creating MotherModelToMother')
      self.motherModelToMother = slicer.vtkMRMLLinearTransformNode()
      self.motherModelToMother.SetName('MotherModelToMother')
      slicer.mrmlScene.AddNode(self.motherModelToMother)
      
    if self.realRadioButton.isChecked():
    	movingFiducials = slicer.util.getNode('VirtualFiducials_mother')
    else:
      if self.guideRadioButton.isChecked():
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyHead_guide')
      else:
        movingFiducials = slicer.util.getNode('VirtualFiducials_babyHead')

    movingFiducials.SetDisplayVisibility(1)
    fixedFiducials = slicer.util.getNode('RealFiducials_mother')
    fixedFiducials.SetDisplayVisibility(1)      

    rms = self.logic.fiducialRegistration(self.motherModelToMother, fixedFiducials, movingFiducials, "Rigid")
    
    self.motherModelToMother = slicer.util.getNode('MotherModelToMother')

    self.rmseText_mother.setText(rms)
    self.applyRegistrationButton_mother.enabled = True

  def onApplyRegistrationButtonClicked_mother(self):
    logging.debug('onApplyRegistrationButtonClicked_mother')
    try:
      self.motherToTracker = slicer.util.getNode('MotherToTracker')
      self.virtualFiducials_mother.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherTummyModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherModelToMother.SetAndObserveTransformNodeID(self.motherToTracker.GetID())
      self.saveRegistrationButton_mother.enabled = True
      self.applyRegistrationButton_mother.enabled = False
      #Show models that were invisible
      self.motherModel.GetModelDisplayNode().VisibilityOn()
      self.motherTummyModel.GetModelDisplayNode().VisibilityOn()
      # Hide Real Fiducials
      self.realFiducials_mother.SetDisplayVisibility(0)
      # Center view in models
      threeDWidget = self.layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()
    except:
      print('ERROR: MotherModelToMother not found')
      print('ERROR: MotherToTracker not found')
      

  def onSaveRegistrationButtonClicked_mother(self):
    logging.debug('onSaveRegistrationButtonClicked_mother')

    res = self.logic.saveData('MotherModelToMother',self.DeliveryTrainingSetupPath_data,'MotherModelToMother.h5')
    if res:
      print('Saved correctly')
      self.saveRegistrationButton_mother.enabled = False
    else:
      print('ERROR: Unable to save MotherModelToMother')

    # collapse Mother area
    self.MotherGroupBox.collapsed = True
  
  # PIVOTING

  def onStartPivotCalibrationButtonClicked(self):
    logging.debug('onStartPivotCalibrationButtonClicked')
    
    self.startPivotCalibration('PointerTipToPointer', self.pointerToTracker, self.pointerTipToPointer)
    
    # logic = SacralNavigationPreprocessingLogic()
    # logic.startPivotCalibration(self.countdownLabel)
    # self.pivotCalibrationStopTime = time.time() + 10
    # self.onPivotSamplingTimeout()

  def startPivotCalibration(self,toolToReferenceTransformName, toolToReferenceTransformNode, toolTipToToolTransformNode):
    calibrationLogic = slicer.modules.pivotcalibration.logic()

    self.calibrationMode = self.pivotMode

    self.startPivotCalibrationButton.enabled = False
    #self.startSpinCalibrationButton.enabled = False

    self.pivotCalibrationResultTargetNode =  toolTipToToolTransformNode
    self.pivotCalibrationResultTargetName = toolToReferenceTransformName
    calibrationLogic.SetAndObserveTransformNode(toolToReferenceTransformNode)
    self.pivotCalibrationStopTime = time.time() + float(self.calibrationTime)
    calibrationLogic.SetRecordingState(True)
    
    self.onPivotSamplingTimeout()

  def onPivotSamplingTimeout(self):
    self.countdownLabel.setText("Calibrating for {0:.0f} more seconds".format(self.pivotCalibrationStopTime-time.time()))
    if(time.time()<self.pivotCalibrationStopTime):
      # calibration not finished -> continue
      self.pivotSamplingTimer.start()
    else:
      # calibration completed
      self.onStopPivotCalibration()

  
  def onStopPivotCalibration(self):
    calibrationLogic = slicer.modules.pivotcalibration.logic()
    calibrationLogic.SetRecordingState(False)

    self.startPivotCalibrationButton.enabled = True
    #self.startSpinCalibrationButton.enabled = True

    if self.calibrationMode == self.pivotMode:
      calibrationSuccess = calibrationLogic.ComputePivotCalibration()
    else:
      calibrationSuccess = calibrationLogic.ComputeSpinCalibration()

    if not calibrationSuccess:
      self.countdownLabel.setText("Calibration failed: ")
      self.countdownErrorLabel.setText(calibrationLogic.GetErrorText())
      calibrationLogic.ClearToolToReferenceMatrices()
      return

    if(calibrationLogic.GetPivotRMSE() >= float(self.thresholdError)):
      self.countdownLabel.setText("Calibration failed:")
      self.countdownErrorLabel.setText("Error = {0:.2f} mm").format(calibrationLogic.GetPivotRMSE())
      calibrationLogic.ClearToolToReferenceMatrices()
      return

    tooltipToToolMatrix = vtk.vtkMatrix4x4()
    calibrationLogic.GetToolTipToToolMatrix(tooltipToToolMatrix)
    calibrationLogic.ClearToolToReferenceMatrices()
    self.pivotCalibrationResultTargetNode.SetMatrixTransformToParent(tooltipToToolMatrix)
    
    if self.calibrationMode == self.pivotMode:
      self.countdownLabel.setText("Pivot calibration completed")
      self.countdownErrorLabel.setText("Error = {0:.2f} mm".format(calibrationLogic.GetPivotRMSE()))
      logging.debug("Pivot calibration completed. Tool: {0}. RMSE = {1:.2f} mm".format(self.pivotCalibrationResultTargetNode.GetName(), calibrationLogic.GetPivotRMSE()))
    else:
      self.countdownLabel.setText("Spin calibration completed.")
      logging.debug("Spin calibration completed.")

    self.savePivotingButton.enabled = True

  
  def onSavePivoting(self):
    logging.debug('savePivotingButton')
    try:
      slicer.util.saveNode(self.pivotCalibrationResultTargetNode, os.path.join(self.DeliveryTrainingSpontaneousSetupPath_data, self.pivotCalibrationResultTargetName + ".h5"))
      print('Transform saved correctly')
    except:
      print('Unable to save transform')

  #def onPivotSamplingTimeout(self):
    #pass
    # if(time.time()<self.pivotCalibrationStopTime):
    #     # continue
    #   self.pivotSamplingTimer.start()
    #   self.countdownLabel.setText("Remaining seconds: {0:.0f}".format(self.pivotCalibrationStopTime-time.time()))
    # else:
    # # calibration completed
    #   logic = SacralNavigationPreprocessingLogic()
    #   rmse = logic.stopPivotCalibration()
    #   # Show the resulting RMSE of the transform
    #   self.countdownLabel.setText("RMSE = %f mm" % rmse)
    #   # Apply the transform to the needle model
    #   self.needleTipToNeedle = slicer.util.getNode('NeedleTipToNeedle')
    #   self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    #   self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToTracker.GetID())
    #   self.trackerToReference = slicer.util.getNode('TrackerToReference')
    #   self.needleToTracker.SetAndObserveTransformNodeID(self.trackerToReference.GetID())
      # self.savePivotingButton.enabled = True

  def onSavePivoting(self):
    logging.debug('savePivotingButton')
    # logic = SacralNavigationPreprocessingLogic()
    # res = logic.saveData('NeedleTipToNeedle',self.sacralNavigationDataPath,'NeedleTipToNeedle.h5')
    # if res:
    #   print('Saved correctly'
    #   self.savePivotingButton.enabled = False
    # else:
    #   print('ERROR: Unable to save transform'



#
# DeliveryTrainingSetupLogic
#

class DeliveryTrainingSetupLogic(ScriptedLoadableModuleLogic):

  def fiducialRegistration(self, saveTransform, fixedLandmarks, movingLandmarks, transformType):
    # logging.info("Fiducial registration starts")
    rms = 0
    parameters = {}
    parameters["fixedLandmarks"] = fixedLandmarks.GetID()
    parameters["movingLandmarks"] = movingLandmarks.GetID()
    parameters["saveTransform"] = saveTransform.GetID()
    parameters["rms"] = rms
    parameters["transformType"] = transformType
    node  = slicer.cli.createNode( slicer.modules.fiducialregistration )
    fidReg = slicer.modules.fiducialregistration
    slicer.cli.run(fidReg, node, parameters, True)
    status = node.GetParameterAsString('outputMessage')
    str_rms = node.GetParameterAsString('rms')

    print('Status: ' + status)
    print('RMSE: ' + str_rms)
    return float(str_rms)

  def saveData(self,node_name,path,file_name):
    node = slicer.util.getNode(node_name)
    file_path = os.path.join(path,file_name)
    return slicer.util.saveNode(node,file_path)


  def reduceVisibilityOtherModels(self,modelName):
    babyHead = slicer.mrmlScene.GetFirstNodeByName('BabyHeadModel')
    babyBody = slicer.mrmlScene.GetFirstNodeByName('BabyBodyModel')
    mother = slicer.mrmlScene.GetFirstNodeByName('MotherModel')
    tummy = slicer.mrmlScene.GetFirstNodeByName('MotherTummyModel')
    forcepsL = slicer.mrmlScene.GetFirstNodeByName('ForcepsLeftModel')
    forcepsR = slicer.mrmlScene.GetFirstNodeByName('ForcepsRightModel')
    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):
      eyesGuide = slicer.mrmlScene.GetFirstNodeByName('EyesGuide')
      earLGuide = slicer.mrmlScene.GetFirstNodeByName('LeftEarGuide')
      earRGuide = slicer.mrmlScene.GetFirstNodeByName('RightEarGuide')
      fontanelleGuide = slicer.mrmlScene.GetFirstNodeByName('FontanelleGuide')
      frontGuide = slicer.mrmlScene.GetFirstNodeByName('FrontGuide')
      backGuide = slicer.mrmlScene.GetFirstNodeByName('BackGuide')
      bellyGuide = slicer.mrmlScene.GetFirstNodeByName('BellyGuide') 
    if modelName == 'BabyHead':
      # Show BabyHead
      babyHead.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      forcepsL.GetModelDisplayNode().SetOpacity(0.5)
      forcepsR.GetModelDisplayNode().SetOpacity(0.5)
      
      if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):
        # Show corresponding guides
        eyesGuide.GetModelDisplayNode().SetOpacity(1)
        earLGuide.GetModelDisplayNode().SetOpacity(1)
        earRGuide.GetModelDisplayNode().SetOpacity(1)
        fontanelleGuide.GetModelDisplayNode().SetOpacity(1)
        # Hide the rest
        frontGuide.GetModelDisplayNode().SetOpacity(0)
        backGuide.GetModelDisplayNode().SetOpacity(0)
        bellyGuide.GetModelDisplayNode().SetOpacity(0)

    elif modelName == 'BabyBody':
      # Show BabyBody
      babyBody.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      forcepsL.GetModelDisplayNode().SetOpacity(0.5)
      forcepsR.GetModelDisplayNode().SetOpacity(0.5)
      
      if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):
        # Show corresponding guides
        frontGuide.GetModelDisplayNode().SetOpacity(1)
        backGuide.GetModelDisplayNode().SetOpacity(1)
        bellyGuide.GetModelDisplayNode().SetOpacity(1)
        
        # Hide the rest
        eyesGuide.GetModelDisplayNode().SetOpacity(0)
        earLGuide.GetModelDisplayNode().SetOpacity(0)
        earRGuide.GetModelDisplayNode().SetOpacity(0)
        fontanelleGuide.GetModelDisplayNode().SetOpacity(0)
    
    elif modelName == 'Mother':
      # Show Mother
      mother.GetModelDisplayNode().SetOpacity(1)
      tummy.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      forcepsL.GetModelDisplayNode().SetOpacity(0.5)
      forcepsR.GetModelDisplayNode().SetOpacity(0.5)
    
    elif modelName == 'ForcepsL':
      # Show forcepsL
      forcepsL.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      forcepsR.GetModelDisplayNode().SetOpacity(0.5)

    elif modelName == 'ForcepsR':
      # Show forcepsR
      forcepsR.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      forcepsL.GetModelDisplayNode().SetOpacity(0.5)

