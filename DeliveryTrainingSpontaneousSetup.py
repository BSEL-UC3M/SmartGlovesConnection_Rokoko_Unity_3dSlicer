import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import time

#
# DeliveryTrainingSpontaneousSetup
#

class DeliveryTrainingSpontaneousSetup(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DeliveryTrainingSpontaneousSetup" # TODO make this more human readable by adding spaces
    self.parent.categories = ["DeliveryTraining"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# DeliveryTrainingSpontaneousSetupWidget
#

class DeliveryTrainingSpontaneousSetupWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # # Load widget from .ui file (created by Qt Designer)
    # uiWidget = slicer.util.loadUI(self.resourcePath('UI/DeliveryTrainingSpontaneousSetup.ui'))
    # self.layout.addWidget(uiWidget)
    # self.ui = slicer.util.childWidgetVariables(uiWidget)

    #Hide Slicer logo
    slicer.util.findChild(slicer.util.mainWindow(), "LogoLabel").visible = False

    # variables
    self.connect = True
    self.logic = DeliveryTrainingSpontaneousSetupLogic()
    self.calibrationTime = 5 #seconds to calibrate
    self.pivotMode = 0
    self.spinMode = 1
    self.thresholdError = 1 #maximum error during calibration in mm

    # quit box and axis
    view = slicer.util.getNode('View1')
    view.SetBoxVisible(0)
    view.SetAxisLabelsVisible(0)

    layoutManager = slicer.app.layoutManager()

    layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)

    #
    # LOADING
    #
    self.LoadCollapsibleButton = ctk.ctkCollapsibleButton()
    self.LoadCollapsibleButton.text = "LOAD"
    self.layout.addWidget(self.LoadCollapsibleButton)

    # Layout within the dummy collapsible button
    loadFormLayout = qt.QFormLayout(self.LoadCollapsibleButton)


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
    self.LoadDataButton = qt.QPushButton("Load Data")
    self.LoadDataButton.enabled = True
    loadFormLayout.addRow(self.LoadDataButton)  

    # Connection to PLUS
    self.ConnectToPLUSButton = qt.QPushButton()
    self.ConnectToPLUSButton.enabled = False
    self.ConnectToPLUSButton.setText('Connect to Plus')
    loadFormLayout.addRow(self.ConnectToPLUSButton)

    # Apply transforms
    self.ApplyTransformsButton = qt.QPushButton()
    self.ApplyTransformsButton.enabled = False
    self.ApplyTransformsButton.setText('Apply Transforms')
    loadFormLayout.addRow(self.ApplyTransformsButton)

    #
    # REGISTRATION
    #
    self.RegistrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.RegistrationCollapsibleButton.text = "REGISTRATION"
    self.RegistrationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.RegistrationCollapsibleButton)

    registrationFormLayout = qt.QFormLayout(self.RegistrationCollapsibleButton)

    # --- Left hand layout ---
    self.LeftHandGroupBox = ctk.ctkCollapsibleGroupBox()
    self.LeftHandGroupBox.setTitle("Left Hand Registration")
    self.LeftHandGroupBox.collapsed = True
    registrationFormLayout.addRow(self.LeftHandGroupBox)
    LeftHandGroupBox_Layout = qt.QFormLayout(self.LeftHandGroupBox)
    self.LeftHandGroupBox.setStyleSheet("background-color: rgb(99,204,202);")


    # --- Hand ---

    self.leftHandText = qt.QLabel('LEFT HAND:')
    self.leftHandText.setStyleSheet("font-size: 12px; font-weight: bold;")
    LeftHandGroupBox_Layout.addRow(self.leftHandText)

    self.fiducialsPlacementLayout_handLeft = qt.QHBoxLayout()
    LeftHandGroupBox_Layout.addRow(self.fiducialsPlacementLayout_handLeft)


     # Create a Fiducials List and add fiducials
    self.LeftHand_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.LeftHand_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_handLeft.addWidget(self.LeftHand_PlaceFiducialButton)

    # Remove Last Fiducial
    self.LeftHand_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.LeftHand_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_handLeft.addWidget(self.LeftHand_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.LeftHand_RemoveAllButton = qt.QPushButton("Remove All")
    self.LeftHand_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_handLeft.addWidget(self.LeftHand_RemoveAllButton)

    # Load existing transform
    self.LeftHand_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.LeftHand_LoadExistingTransformButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftHand_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.LeftHand_RegistrationButton = qt.QPushButton("Registration")
    self.LeftHand_RegistrationButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftHand_RegistrationButton)

    # RMSE after registration
    self.LeftHand_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_handLeft = qt.QLabel('RMSE (mm): ')
    LeftHandGroupBox_Layout.addRow(self.QFormLayoutLabel_handLeft, self.LeftHand_RMSE)

    # Apply registration to models and fiducials
    self.LeftHand_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.LeftHand_ApplyTransformButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftHand_ApplyTransformButton)

    # Save Registration transform in folder
    self.LeftHand_SaveButton = qt.QPushButton("Save")
    self.LeftHand_SaveButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftHand_SaveButton)

    hEmptyLayout = qt.QFormLayout()
    LeftHandGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    LeftHandGroupBox_Layout.addRow(hEmptyLayout)

    # --- Thumb ---

    self.leftThumbText = qt.QLabel('LEFT THUMB:')
    self.leftThumbText.setStyleSheet("font-size: 12px; font-weight: bold;")
    LeftHandGroupBox_Layout.addRow(self.leftThumbText)

    self.fiducialsPlacementLayout_thumbLeft = qt.QHBoxLayout()
    LeftHandGroupBox_Layout.addRow(self.fiducialsPlacementLayout_thumbLeft)


     # Create a Fiducials List and add fiducials
    self.LeftThumb_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.LeftThumb_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_thumbLeft.addWidget(self.LeftThumb_PlaceFiducialButton)

    # Remove Last Fiducial
    self.LeftThumb_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.LeftThumb_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_thumbLeft.addWidget(self.LeftThumb_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.LeftThumb_RemoveAllButton = qt.QPushButton("Remove All")
    self.LeftThumb_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_thumbLeft.addWidget(self.LeftThumb_RemoveAllButton)

    # Load existing transform
    self.LeftThumb_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.LeftThumb_LoadExistingTransformButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftThumb_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.LeftThumb_RegistrationButton = qt.QPushButton("Registration")
    self.LeftThumb_RegistrationButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftThumb_RegistrationButton)

    # RMSE after registration
    self.LeftThumb_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_thumbLeft = qt.QLabel('RMSE (mm): ')
    LeftHandGroupBox_Layout.addRow(self.QFormLayoutLabel_thumbLeft, self.LeftThumb_RMSE)

    # Apply registration to models and fiducials
    self.LeftThumb_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.LeftThumb_ApplyTransformButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftThumb_ApplyTransformButton)

    # Save Registration transform in folder
    self.LeftThumb_SaveButton = qt.QPushButton("Save")
    self.LeftThumb_SaveButton.enabled = False
    LeftHandGroupBox_Layout.addRow(self.LeftThumb_SaveButton)



    # --- Right hand layout ---
    self.RightHandGroupBox = ctk.ctkCollapsibleGroupBox()
    self.RightHandGroupBox.setTitle("Right Hand Registration")
    self.RightHandGroupBox.collapsed = True
    registrationFormLayout.addRow(self.RightHandGroupBox)
    RightHandGroupBox_Layout = qt.QFormLayout(self.RightHandGroupBox)
    self.RightHandGroupBox.setStyleSheet("background-color: rgb(232,109,113);")


    # --- Hand ---

    self.rightHandText = qt.QLabel('RIGHT HAND:')
    self.rightHandText.setStyleSheet("font-size: 12px; font-weight: bold;")
    RightHandGroupBox_Layout.addRow(self.rightHandText)

    self.fiducialsPlacementLayout_handRight = qt.QHBoxLayout()
    RightHandGroupBox_Layout.addRow(self.fiducialsPlacementLayout_handRight)


     # Create a Fiducials List and add fiducials
    self.RightHand_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.RightHand_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_handRight.addWidget(self.RightHand_PlaceFiducialButton)

    # Remove Last Fiducial
    self.RightHand_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.RightHand_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_handRight.addWidget(self.RightHand_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.RightHand_RemoveAllButton = qt.QPushButton("Remove All")
    self.RightHand_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_handRight.addWidget(self.RightHand_RemoveAllButton)

    # Load existing transform
    self.RightHand_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.RightHand_LoadExistingTransformButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightHand_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.RightHand_RegistrationButton = qt.QPushButton("Registration")
    self.RightHand_RegistrationButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightHand_RegistrationButton)

    # RMSE after registration
    self.RightHand_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_handRight = qt.QLabel('RMSE (mm): ')
    RightHandGroupBox_Layout.addRow(self.QFormLayoutLabel_handRight, self.RightHand_RMSE)

    # Apply registration to models and fiducials
    self.RightHand_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.RightHand_ApplyTransformButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightHand_ApplyTransformButton)

    # Save Registration transform in folder
    self.RightHand_SaveButton = qt.QPushButton("Save")
    self.RightHand_SaveButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightHand_SaveButton)

    hEmptyLayout = qt.QFormLayout()
    RightHandGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    RightHandGroupBox_Layout.addRow(hEmptyLayout)

    # --- Thumb ---

    self.rightThumbText = qt.QLabel('RIGHT THUMB:')
    self.rightThumbText.setStyleSheet("font-size: 12px; font-weight: bold;")
    RightHandGroupBox_Layout.addRow(self.rightThumbText)

    self.fiducialsPlacementLayout_thumbRight = qt.QHBoxLayout()
    RightHandGroupBox_Layout.addRow(self.fiducialsPlacementLayout_thumbRight)


     # Create a Fiducials List and add fiducials
    self.RightThumb_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.RightThumb_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_thumbRight.addWidget(self.RightThumb_PlaceFiducialButton)

    # Remove Last Fiducial
    self.RightThumb_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.RightThumb_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_thumbRight.addWidget(self.RightThumb_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.RightThumb_RemoveAllButton = qt.QPushButton("Remove All")
    self.RightThumb_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_thumbRight.addWidget(self.RightThumb_RemoveAllButton)

    # Load existing transform
    self.RightThumb_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.RightThumb_LoadExistingTransformButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightThumb_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.RightThumb_RegistrationButton = qt.QPushButton("Registration")
    self.RightThumb_RegistrationButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightThumb_RegistrationButton)

    # RMSE after registration
    self.RightThumb_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_thumbRight = qt.QLabel('RMSE (mm): ')
    RightHandGroupBox_Layout.addRow(self.QFormLayoutLabel_thumbRight, self.RightThumb_RMSE)

    # Apply registration to models and fiducials
    self.RightThumb_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.RightThumb_ApplyTransformButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightThumb_ApplyTransformButton)

    # Save Registration transform in folder
    self.RightThumb_SaveButton = qt.QPushButton("Save")
    self.RightThumb_SaveButton.enabled = False
    RightHandGroupBox_Layout.addRow(self.RightThumb_SaveButton)


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
    self.BabyHead_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.BabyHead_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_babyHead.addWidget(self.BabyHead_PlaceFiducialButton)

    # Remove Last Fiducial
    self.BabyHead_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.BabyHead_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_babyHead.addWidget(self.BabyHead_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.BabyHead_RemoveAllButton = qt.QPushButton("Remove All")
    self.BabyHead_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_babyHead.addWidget(self.BabyHead_RemoveAllButton)

    # Load existing transform
    self.BabyHead_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.BabyHead_LoadExistingTransformButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyHead_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.BabyHead_RegistrationButton = qt.QPushButton("Registration")
    self.BabyHead_RegistrationButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyHead_RegistrationButton)

    # RMSE after registration
    self.BabyHead_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_babyHead = qt.QLabel('RMSE (mm): ')
    BabyGroupBox_Layout.addRow(self.QFormLayoutLabel_babyHead, self.BabyHead_RMSE)

    # Apply registration to models and fiducials
    self.BabyHead_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.BabyHead_ApplyTransformButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyHead_ApplyTransformButton)

    # Save Registration transform in folder
    self.BabyHead_SaveButton = qt.QPushButton("Save")
    self.BabyHead_SaveButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyHead_SaveButton)

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
    self.BabyBody_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.BabyBody_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.BabyBody_PlaceFiducialButton)

    # Remove Last Fiducial
    self.BabyBody_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.BabyBody_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.BabyBody_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.BabyBody_RemoveAllButton = qt.QPushButton("Remove All")
    self.BabyBody_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_babyBody.addWidget(self.BabyBody_RemoveAllButton)

    # Load existing transform
    self.BabyBody_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.BabyBody_LoadExistingTransformButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyBody_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.BabyBody_RegistrationButton = qt.QPushButton("Registration")
    self.BabyBody_RegistrationButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyBody_RegistrationButton)

    # RMSE after registration
    self.BabyBody_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_babyBody = qt.QLabel('RMSE (mm): ')
    BabyGroupBox_Layout.addRow(self.QFormLayoutLabel_babyBody, self.BabyBody_RMSE)

    # Apply registration to models and fiducials
    self.BabyBody_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.BabyBody_ApplyTransformButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyBody_ApplyTransformButton)

    # Save Registration transform in folder
    self.BabyBody_SaveButton = qt.QPushButton("Save")
    self.BabyBody_SaveButton.enabled = False
    BabyGroupBox_Layout.addRow(self.BabyBody_SaveButton)

    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    BabyGroupBox_Layout.addRow(hEmptyLayout)


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
    self.Mother_PlaceFiducialButton = qt.QPushButton("Place Fiducial")
    self.Mother_PlaceFiducialButton.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.Mother_PlaceFiducialButton)

    # Remove Last Fiducial
    self.Mother_RemoveFiducialButton = qt.QPushButton("Remove Fiducial")
    self.Mother_RemoveFiducialButton.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.Mother_RemoveFiducialButton)

    # Repeat Fiducials Placement
    self.Mother_RemoveAllButton = qt.QPushButton("Remove All")
    self.Mother_RemoveAllButton.enabled = False
    self.fiducialsPlacementLayout_mother.addWidget(self.Mother_RemoveAllButton)

    # Load existing transform
    self.Mother_LoadExistingTransformButton = qt.QPushButton("Load Existing Transform")
    self.Mother_LoadExistingTransformButton.enabled = False
    self.MotherGroupBox_Layout.addRow(self.Mother_LoadExistingTransformButton)

    # Configure registration parameters and get the resulting transformation
    self.Mother_RegistrationButton = qt.QPushButton("Registration")
    self.Mother_RegistrationButton.enabled = False
    self.MotherGroupBox_Layout.addRow(self.Mother_RegistrationButton)

    # RMSE after registration
    self.Mother_RMSE = qt.QLabel('-')
    self.QFormLayoutLabel_mother = qt.QLabel('RMSE (mm): ')
    self.MotherGroupBox_Layout.addRow(self.QFormLayoutLabel_mother, self.Mother_RMSE)

    # Apply registration to models and fiducials
    self.Mother_ApplyTransformButton = qt.QPushButton("Apply Transform")
    self.Mother_ApplyTransformButton.enabled = False
    self.MotherGroupBox_Layout.addRow(self.Mother_ApplyTransformButton)

    # Save Registration transform in folder
    self.Mother_SaveButton = qt.QPushButton("Save")
    self.Mother_SaveButton.enabled = False
    self.MotherGroupBox_Layout.addRow(self.Mother_SaveButton)

    hEmptyLayout = qt.QFormLayout()
    self.MotherGroupBox_Layout.addRow(hEmptyLayout)
    hEmptyLayout = qt.QFormLayout()
    self.MotherGroupBox_Layout.addRow(hEmptyLayout)

    #
    # PIVOTING
    #
    self.pivotingCollapsibleButton = ctk.ctkCollapsibleButton()
    self.pivotingCollapsibleButton.text = "Pivot and Spin Calibration"
    self.pivotingCollapsibleButton.collapsed = True
    self.layout.addWidget(self.pivotingCollapsibleButton)

    pivotingFormLayout = qt.QFormLayout(self.pivotingCollapsibleButton)

    # Start Pivot Calibration
    self.startPivotCalibrationButton = qt.QPushButton("Start Pivot Calibration")
    self.startPivotCalibrationButton.enabled = True
    pivotingFormLayout.addRow(self.startPivotCalibrationButton)

    # Start Spin Calibration
    self.startSpinCalibrationButton = qt.QPushButton("Start Spin Calibration")
    self.startSpinCalibrationButton.enabled = True
    pivotingFormLayout.addRow(self.startSpinCalibrationButton)

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

    ### OLD UI

    # self.ui.BabyHead_PlaceFiducialButton.enabled = False
    # self.ui.BabyHead_RemoveFiducialButton.enabled = False
    # self.ui.BabyHead_RemoveAllButton.enabled = False
    # self.ui.BabyHead_RegistrationButton.enabled = False
    # self.ui.BabyHead_ApplyTransformButton.enabled = False
    # self.ui.BabyHead_SaveButton.enabled = False
    # self.ui.BabyHead_LoadExistingTransformButton.enabled = False

    # self.ui.BabyBody_PlaceFiducialButton.enabled = False
    # self.ui.BabyBody_RemoveFiducialButton.enabled = False
    # self.ui.BabyBody_RemoveAllButton.enabled = False
    # self.ui.BabyBody_RegistrationButton.enabled = False
    # self.ui.BabyBody_ApplyTransformButton.enabled = False
    # self.ui.BabyBody_SaveButton.enabled = False
    # self.ui.BabyBody_LoadExistingTransformButton.enabled = False

    # self.ui.Mother_PlaceFiducialButton.enabled = False
    # self.ui.Mother_RemoveFiducialButton.enabled = False
    # self.ui.Mother_RemoveAllButton.enabled = False
    # self.ui.Mother_RegistrationButton.enabled = False
    # self.ui.Mother_ApplyTransformButton.enabled = False
    # self.ui.Mother_SaveButton.enabled = False
    # self.ui.Mother_LoadExistingTransformButton.enabled = False

    # self.ui.LeftHand_PlaceFiducialButton.enabled = False
    # self.ui.LeftHand_RemoveFiducialButton.enabled = False
    # self.ui.LeftHand_RemoveAllButton.enabled = False
    # self.ui.LeftHand_RegistrationButton.enabled = False
    # self.ui.LeftHand_ApplyTransformButton.enabled = False
    # self.ui.LeftHand_SaveButton.enabled = False
    # self.ui.LeftHand_LoadExistingTransformButton.enabled = False

    # self.ui.RightHand_PlaceFiducialButton.enabled = False
    # self.ui.RightHand_RemoveFiducialButton.enabled = False
    # self.ui.RightHand_RemoveAllButton.enabled = False
    # self.ui.RightHand_RegistrationButton.enabled = False
    # self.ui.RightHand_ApplyTransformButton.enabled = False
    # self.ui.RightHand_SaveButton.enabled = False
    # self.ui.RightHand_LoadExistingTransformButton.enabled = False

    # self.ui.LeftThumb_PlaceFiducialButton.enabled = False
    # self.ui.LeftThumb_RemoveFiducialButton.enabled = False
    # self.ui.LeftThumb_RemoveAllButton.enabled = False
    # self.ui.LeftThumb_RegistrationButton.enabled = False
    # self.ui.LeftThumb_ApplyTransformButton.enabled = False
    # self.ui.LeftThumb_SaveButton.enabled = False
    # self.ui.LeftThumb_LoadExistingTransformButton.enabled = False

    # self.ui.RightThumb_PlaceFiducialButton.enabled = False
    # self.ui.RightThumb_RemoveFiducialButton.enabled = False
    # self.ui.RightThumb_RemoveAllButton.enabled = False
    # self.ui.RightThumb_RegistrationButton.enabled = False
    # self.ui.RightThumb_ApplyTransformButton.enabled = False
    # self.ui.RightThumb_SaveButton.enabled = False
    # self.ui.RightThumb_LoadExistingTransformButton.enabled = False

    # connections
    self.LoadDataButton.connect('clicked(bool)', self.onLoadDataButtonClicked)
    self.ConnectToPLUSButton.connect('clicked(bool)', self.onConnectToPlusButtonClicked)
    self.ApplyTransformsButton.connect('clicked(bool)', self.onApplyTransformsButtonClicked)
    
    self.BabyHead_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_BabyHead)
    self.BabyHead_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_BabyHead)
    self.BabyHead_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_BabyHead)
    self.BabyHead_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_BabyHead)
    self.BabyHead_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_BabyHead)
    self.BabyHead_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_BabyHead)
    self.BabyHead_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_BabyHead)
    
    self.BabyBody_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_BabyBody)
    self.BabyBody_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_BabyBody)
    self.BabyBody_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_BabyBody)
    self.BabyBody_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_BabyBody)
    self.BabyBody_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_BabyBody)
    self.BabyBody_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_BabyBody)
    self.BabyBody_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_BabyBody)
    
    self.Mother_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_Mother)
    self.Mother_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_Mother)
    self.Mother_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_Mother)
    self.Mother_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_Mother)
    self.Mother_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_Mother)
    self.Mother_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_Mother)
    self.Mother_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_Mother)
    
    self.LeftHand_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_LeftHand)
    self.LeftHand_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_LeftHand)
    self.LeftHand_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_LeftHand)
    self.LeftHand_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_LeftHand)
    self.LeftHand_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_LeftHand)
    self.LeftHand_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_LeftHand)
    self.LeftHand_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_LeftHand)
    
    self.LeftThumb_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_LeftThumb)
    self.LeftThumb_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_LeftThumb)
    self.LeftThumb_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_LeftThumb)
    self.LeftThumb_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_LeftThumb)
    self.LeftThumb_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_LeftThumb)
    self.LeftThumb_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_LeftThumb)
    self.LeftThumb_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_LeftThumb)
    
    self.RightHand_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_RightHand)
    self.RightHand_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_RightHand)
    self.RightHand_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_RightHand)
    self.RightHand_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_RightHand)
    self.RightHand_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_RightHand)
    self.RightHand_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_RightHand)
    self.RightHand_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_RightHand)
    
    self.RightThumb_PlaceFiducialButton.connect('clicked(bool)', self.onPlaceButtonClicked_RightThumb)
    self.RightThumb_RemoveFiducialButton.connect('clicked(bool)', self.onRemoveButtonClicked_RightThumb)
    self.RightThumb_RemoveAllButton.connect('clicked(bool)', self.onRemoveAllButtonClicked_RightThumb)
    self.RightThumb_LoadExistingTransformButton.connect('clicked(bool)', self.onLoadTransformButtonClicked_RightThumb)
    self.RightThumb_RegistrationButton.connect('clicked(bool)', self.onRegistrationButtonClicked_RightThumb)
    self.RightThumb_ApplyTransformButton.connect('clicked(bool)', self.onApplyRegistrationButtonClicked_RightThumb)
    self.RightThumb_SaveButton.connect('clicked(bool)', self.onSaveRegistrationButtonClicked_RightThumb)

    self.startPivotCalibrationButton.connect('clicked(bool)', self.onStartPivotCalibrationButtonClicked)
    self.startSpinCalibrationButton.connect('clicked(bool)', self.onStartSpinCalibrationButtonClicked)
    self.pivotSamplingTimer.connect('timeout()',self.onPivotSamplingTimeout)
    self.savePivotingButton.connect('clicked(bool)', self.onSavePivoting)


  def cleanup(self):
    pass


  def onLoadDataButtonClicked(self):
    logging.debug('onloadDataButtonClicked')



    # CREATE PATHS
    self.DeliveryTrainingSpontaneousSetupPath_models = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Models/'
    self.DeliveryTrainingSpontaneousSetupPath_data = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Data/'
    self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/'
    self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/RealSize/'
    self.DeliveryTrainingSetupPath_guides = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/Guides/'

    # Model colors
    baby_color = np.divide(np.array([255.0,111.0,224.0]),255)
    mother_color = np.divide(np.array([255.0,183.0,149.0]),255)
    hand_color = np.divide(np.array([76.0,87.0,235.0]),255)
    leftHandColor = np.divide(np.array([99.0,204.0,202.0]),255)
    rightHandColor = np.divide(np.array([214.0,64.0,69.0]),255)
    guides_color = np.array([0.937, 0.941, 0.317])

    #LOAD MODELS

    self.nonLoadedModels = 0

    # Baby Head
    try:
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'BabyHeadModel.stl')
        self.babyHeadModel = slicer.util.getNode(pattern="BabyHeadModel")
        self.babyHeadModelDisplay=self.babyHeadModel.GetModelDisplayNode()
        self.babyHeadModelDisplay.SetColor(baby_color)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyHeadModel not found')
        

    # Baby Body
    try:
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'BabyBodyModel.stl')
        self.babyBodyModel = slicer.util.getNode(pattern="BabyBodyModel")
        self.babyBodyModelDisplay=self.babyBodyModel.GetModelDisplayNode()
        self.babyBodyModelDisplay.SetColor(baby_color)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyBodyModel not found')
        

    # Mother
    try:
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      try:
        #slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'MotherModel.vtk')
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherModel.stl')
        self.motherModel = slicer.util.getNode(pattern="MotherModel")
        self.motherModelDisplay=self.motherModel.GetModelDisplayNode()
        #self.motherModelDisplay.SetColor(mother_color)
        self.motherModelDisplay.SetColor([1,0.68,0.79])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: MotherModel not found')


    # Mother tummy
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

    # Left Hand
    try:
      self.handLModel = slicer.util.getNode('HandLModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'HandLModel.vtk')
        self.handLModel = slicer.util.getNode(pattern="HandLModel")
        self.handLModelDisplay=self.handLModel.GetModelDisplayNode()
        self.handLModelDisplay.SetColor(leftHandColor)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: HandLModel not found')
      

    # Left Thumb
    try:
      self.thumbLModel = slicer.util.getNode('ThumbLModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ThumbLModel.vtk')
        self.thumbLModel = slicer.util.getNode(pattern="ThumbLModel")
        self.thumbLModelDisplay=self.thumbLModel.GetModelDisplayNode()
        self.thumbLModelDisplay.SetColor(leftHandColor)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ThumbLModel not found')


    # Right Hand
    try:
      self.handRModel = slicer.util.getNode('HandRModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'HandRModel.vtk')
        self.handRModel = slicer.util.getNode(pattern="HandRModel")
        self.handRModelDisplay=self.handRModel.GetModelDisplayNode()
        self.handRModelDisplay.SetColor(rightHandColor)
      except:
        self.nonRoadedModels = self.nonLoadedModels + 1
        print('ERROR: HandRModel not found')
      
        
    # Right Thumb
    try:
      self.thumbRModel = slicer.util.getNode('ThumbRModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ThumbRModel.vtk')
        self.thumbRModel = slicer.util.getNode(pattern="ThumbRModel")
        self.thumbRModelDisplay=self.thumbRModel.GetModelDisplayNode()
        self.thumbRModelDisplay.SetColor(rightHandColor)
      except:
        self.nonRoadedModels = self.nonLoadedModels + 1
        print('ERROR: ThumbRModel not found')
        

    # Pointer
    try:
      self.pointerModel = slicer.util.getNode('PointerModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'PointerModel.vtk')
        self.pointerModel = slicer.util.getNode(pattern="PointerModel")
        self.pointerModelDisplay=self.pointerModel.GetModelDisplayNode()
        self.pointerModelDisplay.SetColor([0,0.5,0.25])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: PointerModel not found')



    #IF GUIDES ARE USED FOR REGISTRATION
    if self.guideRadioButton.isChecked():
      #HEAD
      try:
        self.eyesGuide = slicer.util.getNode('EyesGuide')
      except:
        try:
          slicer.util.loadModel(self.DeliveryTrainingSetupPath_guides + 'EyesGuide.stl')
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
          print('ERROR: Fontanelle1Guide not found')



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

    
      

    # LOAD FIDUCIALS

    # Baby Head
    try:
      if self.guideRadioButton.isChecked():
        self.fiducialsName_babyHead = 'BabyHeadModelFiducialsGuide'
      else:
        self.fiducialsName_babyHead = 'BabyHeadModelFiducials'

      self.babyHeadModelFiducials = slicer.util.getNode(self.fiducialsName_babyHead)
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + self.fiducialsName_babyHead + '.fcsv')
        self.babyHeadModelFiducials = slicer.util.getNode(pattern=self.fiducialsName_babyHead)
        self.babyHeadModelFiducials.SetDisplayVisibility(0)
        # Display them in blue
        displayNode = self.babyHeadModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try: #Only available in 4.11
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyHeadModelFiducials not found')

    # Baby Body
    try:
      if self.guideRadioButton.isChecked():
        self.fiducialsName_babyBody = 'BabyBodyModelFiducialsGuide'
      else:
        self.fiducialsName_babyBody = 'BabyBodyModelFiducials'

      self.babyBodyModelFiducials = slicer.util.getNode(self.fiducialsName_babyBody)
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + self.fiducialsName_babyBody + '.fcsv')
        self.babyBodyModelFiducials = slicer.util.getNode(pattern=self.fiducialsName_babyBody)
        # Display them in blue
        displayNode = self.babyBodyModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        self.babyBodyModelFiducials.SetDisplayVisibility(0)
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: BabyBodyModelFiducials not found')

    # Mother
    try:
      self.motherModelFiducials = slicer.util.getNode('MotherModelFiducials')
    except:
      try:
        #slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'MotherModelFiducials.fcsv')
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'MotherModelFiducials.fcsv')
        self.motherModelFiducials = slicer.util.getNode(pattern="MotherModelFiducials")
        # Display them in blue
        displayNode = self.motherModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.motherModelFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: MotherModelFiducials not found')

    # Left Hand
    try:
      self.handLModelFiducials = slicer.util.getNode('HandLModelFiducials')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'HandLModelFiducials.fcsv')
        self.handLModelFiducials = slicer.util.getNode(pattern="HandLModelFiducials")
        # Display them in blue
        displayNode = self.handLModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.handLModelFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: HandLModelFiducials not found')
        
    # Left Thumb
    try:
      self.thumbLModelFiducials = slicer.util.getNode('ThumbLModelFiducials')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'ThumbLModelFiducials.fcsv')
        self.thumbLModelFiducials = slicer.util.getNode(pattern="ThumbLModelFiducials")
        # Display them in blue
        displayNode = self.thumbLModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.thumbLModelFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ThumbLModelFiducials not found')

    # Right Hand
    try:
      self.handRModelFiducials = slicer.util.getNode('HandRModelFiducials')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'HandRModelFiducials.fcsv')
        self.handRModelFiducials = slicer.util.getNode(pattern="HandRModelFiducials")
        # Display them in blue
        displayNode = self.handRModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.handRModelFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: HandRModelFiducials not found')
        
    # Right Thumb
    try:
      self.thumbRModelFiducials = slicer.util.getNode('ThumbRModelFiducials')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'ThumbRModelFiducials.fcsv')
        self.thumbRModelFiducials = slicer.util.getNode(pattern="ThumbRModelFiducials")
        # Display them in blue
        displayNode = self.thumbRModelFiducials.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        displayNode.SetGlyphScale(4.0)
        displayNode.SetGlyphTypeFromString('Sphere3D')
        try:
          displayNode.SetOccludedVisibility(True)
          displayNode.SetOccludedOpacity(0.1)
        except:
          pass
        self.thumbRModelFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: ThumbRModelFiducials not found')

    # LOAD TRANSFORMS
    # Load PointerTipToPointer
    try:
      self.pointerTipToPointer = slicer.util.getNode('PointerTipToPointer')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'PointerTipToPointer.h5')
        self.pointerTipToPointer = slicer.util.getNode(pattern="PointerTipToPointer")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: PointerTipToPointer not found')

    # Load PointerModelToPointerTip
    try:
      self.pointerModelToPointerTip = slicer.util.getNode('PointerModelToPointerTip')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'PointerModelToPointerTip.h5')
        self.pointerModelToPointerTip = slicer.util.getNode(pattern="PointerModelToPointerTip")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: PointerModelToPointerTip not found')

    # APPLY EXISTING TRANFORMS
    try:
      self.pointerModel.SetAndObserveTransformNodeID(self.pointerModelToPointerTip.GetID())
      self.pointerModelToPointerTip.SetAndObserveTransformNodeID(self.pointerTipToPointer.GetID())
    except:
      print('ERROR: unable to apply pointer transforms')

    if self.nonLoadedModels > 0:
      print("Non loaded models: " + str(self.nonLoadedModels))
    else:
      self.LoadDataButton.enabled = False
      self.ConnectToPLUSButton.enabled = True


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
        self.ApplyTransformsButton.enabled = True
        self.BabyHead_LoadExistingTransformButton.enabled = True
        self.BabyBody_LoadExistingTransformButton.enabled = True
        self.Mother_LoadExistingTransformButton.enabled = True
        self.LeftHand_LoadExistingTransformButton.enabled = True
        self.LeftThumb_LoadExistingTransformButton.enabled = True
        self.RightHand_LoadExistingTransformButton.enabled = True
        self.RightThumb_LoadExistingTransformButton.enabled = True
        self.connect = False
        self.ConnectToPLUSButton.setText('Disconnect from Plus')
      else:
        print('ERROR: Unable to connect to PLUS')
        logging.debug('ERROR: Unable to connect to PLUS')

    else:
      cnode = slicer.util.getNode('IGTLConnector')
      cnode.Stop()
      self.connect = True
      self.ConnectToPLUSButton.setText('Connect to Plus')


  def onApplyTransformsButtonClicked(self):
    logging.debug('onApplyTransformsButtonClicked')

    nonLoadedTransforms = 0

    # Apply pointerToTracker to all pointer transforms and model
    try:
      self.pointerToTracker = slicer.util.getNode('PointerToTracker')
      self.pointerTipToPointer.SetAndObserveTransformNodeID(self.pointerToTracker.GetID())
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: Unable to load PointerToTracker transform')
      

    # Load transforms

    # Load BabyHeadToTracker
    try:
      self.babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: BabyHeadToTracker not found')
      
    # Load BabyBodyToTracker
    try:
      self.babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: BabyBodyToTracker not found')

    # Load MotherToTracker
    try:
      self.motherToTracker = slicer.util.getNode('MotherToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: MotherToTracker not found')
      
    # Load HandLToTracker
    try:
      self.handLToTracker = slicer.util.getNode('HandLToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: HandLToTracker not found')

    # Load HandRToTracker
    try:
      self.handRToTracker = slicer.util.getNode('HandRToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: HandRToTracker not found')
      
    # Load ThumbLToTracker
    try:
      self.thumbLToTracker = slicer.util.getNode('ThumbLToTracker')
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: ThumbLToTracker not found')

    # Load ThumbRToTracker
    try:
      self.thumbRToTracker = slicer.util.getNode('ThumbRToTracker')
      self.addWatchdog(self.thumbRToTracker, warningMessage = 'ThumbR is out of view', playSound = True)
    except:
      nonLoadedTransforms = nonLoadedTransforms + 1
      print('ERROR: ThumbRToTracker not found')
      

    if nonLoadedTransforms == 0:
      self.ApplyTransformsButton.enabled = False
      self.BabyHead_PlaceFiducialButton.enabled = True
      self.BabyBody_PlaceFiducialButton.enabled = True
      self.Mother_PlaceFiducialButton.enabled = True
      self.LeftHand_PlaceFiducialButton.enabled = True
      self.RightHand_PlaceFiducialButton.enabled = True
      self.LeftThumb_PlaceFiducialButton.enabled = True
      self.RightThumb_PlaceFiducialButton.enabled = True
      self.LoadCollapsibleButton.collapsed = True
      self.RegistrationCollapsibleButton.collapsed = False


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


  def placeFiducial(self, modelName):

    # define node names for specified model
    transformName = 'TrackerTo' + modelName
    modelFiducialsName = modelName + 'ModelFiducials'
    realFiducialsName = modelName + 'RealFiducials'

    if self.develRadioButton.isChecked() and (modelName == 'Mother' or modelName == 'BabyBody'): #if developer mode and model is mother or baby body
      modelFiducialsName = 'BabyHeadModelFiducials' #use baby head fiducials

    if self.guideRadioButton.isChecked() and (modelFiducialsName == 'BabyHeadModelFiducials' or modelFiducialsName == 'BabyBodyModelFiducials'): #if we use guides and the resgistered model is baby body or head (from head, mother or body), use the corresponding fiducials
      modelFiducialsName = modelFiducialsName + 'Guide' #use fiducials for guides
 

    # apply transform to pointer so that it gets the points with respect to the reference
    try:
      transform = slicer.util.getNode(transformName)
      self.pointerToTracker.SetAndObserveTransformNodeID(transform.GetID())
    except:
      print('ERROR: ' + transformName + ' not found')
    
    # make model fiducials visible
    fiducials_list = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    for fiducial_node in fiducials_list:
      if fiducial_node.GetName() == modelFiducialsName:
        fiducial_node.SetDisplayVisibility(1)
        virtualFiducials = fiducial_node
      elif fiducial_node.GetName() == realFiducialsName:
        fiducial_node.SetDisplayVisibility(1)
      else:
        fiducial_node.SetDisplayVisibility(0)
    
    # get or create real fiducuals
    try:
      realFiducials = slicer.util.getNode(realFiducialsName)
    except:
      realFiducials = slicer.vtkMRMLMarkupsFiducialNode()  
      realFiducials.SetName(realFiducialsName)
      slicer.mrmlScene.AddNode(realFiducials)
      realFiducials.GetDisplayNode().SetColor(1,0,0)

    # apply transform of reference to fiducials so that they keep the same despite of patient movements
    realFiducials.SetAndObserveTransformNodeID(transform.GetID())

    numberOfRealFiducials = realFiducials.GetNumberOfFiducials() + 1
    numberOfVirtualFiducials = virtualFiducials.GetNumberOfFiducials()
    numberOfFiducialsLeft = numberOfVirtualFiducials - numberOfRealFiducials

    # read pointertip position and add fiducial to the list
    # get transform
    m = vtk.vtkMatrix4x4()
    m.Identity()
    self.pointerTipToPointer.GetMatrixTransformToWorld(m)
    # get the values of the last column to add them as the new markup point
    realFiducials.AddFiducialFromArray([m.GetElement(0,3),m.GetElement(1,3),m.GetElement(2,3)])

    complete = False
    if numberOfRealFiducials == numberOfVirtualFiducials:
      # stop observing transform
      realFiducials.SetAndObserveTransformNodeID(None)
      complete = True

    return numberOfFiducialsLeft, complete
    

  def removeFiducial(self, modelName):

    # define node names for specified model
    modelFiducialsName = modelName + 'ModelFiducials'
    realFiducialsName = modelName + 'RealFiducials'
    numberOfFiducialsLeft = 0
    complete = False

    if self.develRadioButton.isChecked() and (modelName == 'Mother' or modelName == 'BabyBody'): #if developer mode and model is mother or baby body
      modelFiducialsName = 'BabyHeadModelFiducials' #use baby head fiducials
    
    if self.guideRadioButton.isChecked() and (modelFiducialsName == 'BabyHeadModelFiducials' or modelFiducialsName == 'BabyBodyModelFiducials'): #if we use guides and the resgistered model is baby body or head (from head, mother or body), use the corresponding fiducials
      modelFiducialsName = modelFiducialsName + 'Guide' #use fiducials for guides

    try:
      virtualFiducials = slicer.util.getNode(modelFiducialsName)
      realFiducials = slicer.util.getNode(realFiducialsName)
      numberOfRealFiducials = realFiducials.GetNumberOfFiducials()
      numberOfVirtualFiducials = virtualFiducials.GetNumberOfFiducials()
      positionDelete = numberOfRealFiducials - 1
      if positionDelete < 0:
        print('ERROR: No markups were found on the list. Positions < 0 are not valid')
      else:
        realFiducials.RemoveMarkup(positionDelete)
        numberOfRealFiducials = numberOfRealFiducials - 1
        # correct the button text indicating the number of fiducials left
        numberOfFiducialsLeft = numberOfVirtualFiducials - numberOfRealFiducials
        if positionDelete <= 0:
          complete = True
    except:
      print('ERROR: Unable to load ' + realFiducialsName)

    return numberOfFiducialsLeft, complete


  def removeAllFiducials(self, modelName):

    # define node names for specified model
    transformName = modelName + 'ModelTo' + modelName
    modelFiducialsName = modelName + 'ModelFiducials'
    realFiducialsName = modelName + 'RealFiducials'

    # get or create real fiducuals
    try:
      realFiducials = slicer.util.getNode(realFiducialsName)
      realFiducials.RemoveAllMarkups()
    except:
      print('ERROR: Unable to load Fiducials')
    try:
      transform = slicer.util.getNode(transformName)
      slicer.mrmlScene.RemoveNode(transform)
    except:
      print(transformName + ' not found')


  def loadTransform(self, modelName):
    
    # define node names for specified model
    transformName = modelName + 'ModelTo' + modelName
    trackerTransformName = modelName + 'ToTracker'

    try:
      transform = slicer.util.getNode(transformName)
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + transformName + '.h5')
        transform = slicer.util.getNode(transformName)
      except:
        print('ERROR: ' + transformName + ' not found')
    try:
      modelNode = slicer.util.getNode(modelName+'Model')
      modelNode.SetAndObserveTransformNodeID(transform.GetID())
      trackerTransform = slicer.util.getNode(trackerTransformName)
      transform.SetAndObserveTransformNodeID(trackerTransform.GetID())
      if modelName == 'Mother':
        self.motherTummyModel = slicer.util.getNode(pattern="MotherTummyModel")
        self.motherTummyModel.SetAndObserveTransformNodeID(transform.GetID())
    except:
      print('ERROR: unable to apply transform')    

  def registration(self, modelName, registrationType):

    # FIXED

    # define node names for specifed model
    transformName = modelName + 'ModelTo' + modelName
    realFiducialsName = modelName + 'RealFiducials'
    modelFiducialsName = modelName + 'ModelFiducials'

    if self.develRadioButton.isChecked() and (modelName == 'Mother' or modelName == 'BabyBody'): #if developer mode and model is mother or baby body
      modelFiducialsName = 'BabyHeadModelFiducials' #use baby head fiducials

    if self.guideRadioButton.isChecked() and (modelFiducialsName == 'BabyHeadModelFiducials' or modelFiducialsName == 'BabyBodyModelFiducials'): #if we use guides and the resgistered model is baby body or head (from head, mother or body), use the corresponding fiducials
      modelFiducialsName = modelFiducialsName + 'Guide' #use fiducials for guides

    rms = -1

    try:
      transform = slicer.util.getNode(transformName)
    except:
      print('Creating ' + transformName)
      transform = slicer.vtkMRMLLinearTransformNode()
      transform.SetName(transformName)
      slicer.mrmlScene.AddNode(transform)
    try:
      virtualFiducials = slicer.util.getNode(modelFiducialsName)
      realFiducials = slicer.util.getNode(realFiducialsName)    
      rms = self.logic.fiducialRegistration(transform, realFiducials, virtualFiducials, registrationType)
    except:
      print('ERROR: Unable to perform registration')
    return rms

  def applyRegistration(self, modelName):

    # define node names for specifed model
    transformName = modelName + 'ModelTo' + modelName
    realFiducialsName = modelName + 'RealFiducials'
    modelFiducialsName = modelName + 'ModelFiducials'
    modelNodeName = modelName + 'Model'
    trackerTransformName = modelName + 'ToTracker'

    try:
      transform = slicer.util.getNode(transformName)
    except:
      print('ERROR: Unable to load transform ' + transformName)
    try:
      virtualFiducials = slicer.util.getNode(modelFiducialsName)
      realFiducials = slicer.util.getNode(realFiducialsName)
      modelNode = slicer.util.getNode(modelNodeName)
      trackerTransform = slicer.util.getNode(trackerTransformName)
      virtualFiducials.SetAndObserveTransformNodeID(transform.GetID())
      modelNode.SetAndObserveTransformNodeID(transform.GetID())
      transform.SetAndObserveTransformNodeID(trackerTransform.GetID())
      realFiducials.SetDisplayVisibility(0)
      virtualFiducials.SetDisplayVisibility(0)
      if modelName == 'Mother':
        self.motherTummyModel = slicer.util.getNode(pattern="MotherTummyModel")
        self.motherTummyModel.SetAndObserveTransformNodeID(transform.GetID())
    except:
      print('ERROR: Unable to apply transform ' + transformName)

  def saveRegistration(self, modelName):
    transformName = modelName + 'ModelTo' + modelName

    res = self.logic.saveData(transformName, self.DeliveryTrainingSpontaneousSetupPath_data,transformName + '.h5')
    if res:
      print('Saved correctly')
    else:
      print('ERROR: Unable to save ' + transformName)
    return res


  # BABY HEAD

  def onPlaceButtonClicked_BabyHead(self):
    logging.debug('onPlaceButtonClicked_BabyHead')

    modelName = 'BabyHead'
    # Enable the button to remove
    self.BabyHead_RemoveFiducialButton.enabled = True
    self.BabyHead_RemoveAllButton.enabled = True

    # if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'): #if the guides exist 
    #   if self.eyesGuideDisplay.GetOpacity() == 0: #if the guides are invisible
    #     self.eyesGuideDisplay.SetOpacity(1)
    #     self.leftEarGuideDisplay.SetOpacity(1)
    #     self.rightEarGuideDisplay.SetOpacity(1)
    #     self.fontanelleGuideDisplay.SetOpacity(1)
    #     # self.fontanelle2GuideDisplay.SetOpacity(1)

    self.logic.reduceVisibilityOtherModels(modelName)


    numberOfFiducialsLeft, complete = self.placeFiducial(modelName)
    
    self.BabyHead_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
    if complete:
      self.BabyHead_PlaceFiducialButton.enabled = False
      self.BabyHead_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_BabyHead(self):
    logging.debug('onRemoveButtonClicked_BabyHead')

    modelName = 'BabyHead'

    self.BabyHead_PlaceFiducialButton.enabled = True
    self.BabyHead_RegistrationButton.enabled = False


    numberOfFiducialsLeft, complete = self.removeFiducial(modelName)

    self.BabyHead_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')

    if complete: 
      self.BabyHead_RemoveFiducialButton.enabled = False
      self.BabyHead_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_BabyHead(self):
    logging.debug('onRemoveAllButtonClicked_BabyHead')
    
    modelName = 'BabyHead'

    self.removeAllFiducials(modelName)

    self.BabyHead_PlaceFiducialButton.enabled = True
    self.BabyHead_PlaceFiducialButton.setText('Place Real Fiducials')
    self.BabyHead_RemoveAllButton.enabled = False
    self.BabyHead_RegistrationButton.enabled = False
    self.BabyHead_SaveButton.enabled = False
    self.BabyHead_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_BabyHead(self):
    logging.debug('onLoadTransformButtonClicked_BabyHead')

    modelName = 'BabyHead'
    self.loadTransform(modelName)

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):  # if the guides exist
      if self.eyesGuideDisplay.GetOpacity() == 1: #if the guides are visible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)


    

  def onRegistrationButtonClicked_BabyHead(self):
    logging.debug('onRegistrationButtonClicked_BabyHead')

    modelName = 'BabyHead'

    rms = self.registration(modelName, 'Rigid')

    self.BabyHead_RMSE.setText(rms)
    self.BabyHead_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_BabyHead(self):
    logging.debug('onApplyRegistrationButtonClicked_BabyHead')

    modelName = 'BabyHead'
    self.applyRegistration(modelName)
    self.BabyHead_SaveButton.enabled = True

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'): #if the guides exist 
      if self.eyesGuideDisplay.GetOpacity() == 1: #if the guides are visible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)


  def onSaveRegistrationButtonClicked_BabyHead(self):
    logging.debug('onSaveRegistrationButtonClicked_BabyHead')

    modelName = 'BabyHead'
    res = self.saveRegistration(modelName)
    if res:
      self.BabyHead_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')
    

  # BABY BODY

  def onPlaceButtonClicked_BabyBody(self):
    logging.debug('onPlaceButtonClicked_BabyBody')

    modelName = 'BabyBody'
    
    # Enable the button to remove
    self.BabyBody_RemoveFiducialButton.enabled = True
    self.BabyBody_RemoveAllButton.enabled = True

    # if self.guideRadioButton.isChecked(): 
    #   if self.develRadioButton.isChecked(): #use head guides
    #     if self.eyesGuideDisplay.GetOpacity() == 0: #if the guides are invisible
    #       self.eyesGuideDisplay.SetOpacity(1)
    #       self.leftEarGuideDisplay.SetOpacity(1)
    #       self.rightEarGuideDisplay.SetOpacity(1)
    #       self.fontanelleGuideDisplay.SetOpacity(1)
    #       # self.fontanelle2GuideDisplay.SetOpacity(1)
    #   else: #use body guides
    #     if self.frontGuideDisplay.GetOpacity() == 0:
    #       self.frontGuideDisplay.SetOpacity(1)
    #       self.backGuideDisplay.SetOpacity(1)
    #       self.bellyGuideDisplay.SetOpacity(1)

    if self.develRadioButton.isChecked():
      # Use babyHead
      modelNameVisibility = 'BabyHead'
    else: 
      # Use babyBody
      modelNameVisibility = 'BabyBody'
    
    self.logic.reduceVisibilityOtherModels(modelNameVisibility)

    numberOfFiducialsLeft, complete = self.placeFiducial(modelName)
    
    self.BabyBody_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
    if complete:
      self.BabyBody_PlaceFiducialButton.enabled = False
      self.BabyBody_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_BabyBody(self):
    logging.debug('onRemoveButtonClicked_BabyBody')

    modelName = 'BabyBody'

    self.BabyBody_PlaceFiducialButton.enabled = True
    self.BabyBody_RegistrationButton.enabled = False


    numberOfFiducialsLeft, complete = self.removeFiducial(modelName)

    self.BabyBody_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')

    if complete: 
      self.BabyBody_RemoveFiducialButton.enabled = False
      self.BabyBody_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_BabyBody(self):
    logging.debug('onRemoveAllButtonClicked_BabyBody')
    
    modelName = 'BabyBody'

    self.removeAllFiducials(modelName)

    self.BabyBody_PlaceFiducialButton.enabled = True
    self.BabyBody_PlaceFiducialButton.setText('Place Real Fiducials')
    self.BabyBody_RemoveAllButton.enabled = False
    self.BabyBody_RegistrationButton.enabled = False
    self.BabyBody_SaveButton.enabled = False
    self.BabyBody_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_BabyBody(self):
    logging.debug('onLoadTransformButtonClicked_BabyBody')

    modelName = 'BabyBody'
    self.loadTransform(modelName)

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):  # if the guides exist
      if self.eyesGuideDisplay.GetOpacity() == 1 or self.frontGuideDisplay.GetOpacity() == 1: #if any of the guides are visible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)
        self.frontGuideDisplay.SetOpacity(0)
        self.backGuideDisplay.SetOpacity(0)
        self.bellyGuideDisplay.SetOpacity(0)
    

  def onRegistrationButtonClicked_BabyBody(self):
    logging.debug('onRegistrationButtonClicked_BabyBody')

    modelName = 'BabyBody'

    rms = self.registration(modelName, 'Rigid')

    self.BabyBody_RMSE.setText(rms)
    self.BabyBody_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_BabyBody(self):
    logging.debug('onApplyRegistrationButtonClicked_BabyBody')

    modelName = 'BabyBody'
    self.applyRegistration(modelName)
    self.BabyBody_SaveButton.enabled = True

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'):  # if the guides exist
      if self.eyesGuideDisplay.GetOpacity() == 1 or self.frontGuideDisplay.GetOpacity() == 1: #if any of the guides are visible
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)
        self.frontGuideDisplay.SetOpacity(0)
        self.backGuideDisplay.SetOpacity(0)
        self.bellyGuideDisplay.SetOpacity(0)


  def onSaveRegistrationButtonClicked_BabyBody(self):
    logging.debug('onSaveRegistrationButtonClicked_BabyBody')

    modelName = 'BabyBody'
    res = self.saveRegistration(modelName)
    if res:
      self.BabyBody_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')
    
  # MOTHER

  def onPlaceButtonClicked_Mother(self):
    logging.debug('onPlaceButtonClicked_Mother')

    modelName = 'Mother'
    # Enable the button to remove
    self.Mother_RemoveFiducialButton.enabled = True
    self.Mother_RemoveAllButton.enabled = True

    # if self.develRadioButton.isChecked() and self.guideRadioButton.isChecked() and self.eyesGuideDisplay.GetOpacity() == 0:
    #   self.eyesGuideDisplay.SetOpacity(1)
    #   self.leftEarGuideDisplay.SetOpacity(1)
    #   self.rightEarGuideDisplay.SetOpacity(1)
    #   self.fontanelleGuideDisplay.SetOpacity(1)
    #   # self.fontanelle2GuideDisplay.SetOpacity(1)

    if self.develRadioButton.isChecked():
      # Use babyHead
      modelNameVisibility = 'BabyHead'
    else: 
      # Use mother
      modelNameVisibility = 'Mother'
    
    self.logic.reduceVisibilityOtherModels(modelNameVisibility)

    numberOfFiducialsLeft, complete = self.placeFiducial(modelName)
    
    self.Mother_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
    if complete:
      self.Mother_PlaceFiducialButton.enabled = False
      self.Mother_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_Mother(self):
    logging.debug('onRemoveButtonClicked_Mother')

    modelName = 'Mother'

    self.Mother_PlaceFiducialButton.enabled = True
    self.Mother_RegistrationButton.enabled = False


    numberOfFiducialsLeft, complete = self.removeFiducial(modelName)

    self.Mother_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')

    if complete: 
      self.Mother_RemoveFiducialButton.enabled = False
      self.Mother_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_Mother(self):
    logging.debug('onRemoveAllButtonClicked_Mother')
    
    modelName = 'Mother'

    self.removeAllFiducials(modelName)

    self.Mother_PlaceFiducialButton.enabled = True
    self.Mother_PlaceFiducialButton.setText('Place Real Fiducials')
    self.Mother_RemoveAllButton.enabled = False
    self.Mother_RegistrationButton.enabled = False
    self.Mother_SaveButton.enabled = False
    self.Mother_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_Mother(self):
    logging.debug('onLoadTransformButtonClicked_Mother')

    modelName = 'Mother'
    self.loadTransform(modelName)

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'): #if the guides exist 
      if self.eyesGuideDisplay.GetOpacity() == 1:
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)
    

  def onRegistrationButtonClicked_Mother(self):
    logging.debug('onRegistrationButtonClicked_Mother')

    modelName = 'Mother'

    rms = self.registration(modelName, 'Rigid')

    self.Mother_RMSE.setText(rms)
    self.Mother_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_Mother(self):
    logging.debug('onApplyRegistrationButtonClicked_Mother')

    modelName = 'Mother'
    self.applyRegistration(modelName)
    self.Mother_SaveButton.enabled = True

    if slicer.mrmlScene.GetFirstNodeByName('EyesGuide'): #if the guides exist 
      if self.eyesGuideDisplay.GetOpacity() == 1:
        self.eyesGuideDisplay.SetOpacity(0)
        self.leftEarGuideDisplay.SetOpacity(0)
        self.rightEarGuideDisplay.SetOpacity(0)
        self.fontanelleGuideDisplay.SetOpacity(0)
        # self.fontanelle2GuideDisplay.SetOpacity(0)


  def onSaveRegistrationButtonClicked_Mother(self):
    logging.debug('onSaveRegistrationButtonClicked_Mother')

    modelName = 'Mother'
    res = self.saveRegistration(modelName)
    if res:
      self.Mother_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')
    
  
  # HAND LEFT

  def onPlaceButtonClicked_LeftHand(self):
    logging.debug('onPlaceButtonClicked_LeftHand')

    modelName = 'HandL'
    # Enable the button to remove
    self.LeftHand_RemoveFiducialButton.enabled = True
    self.LeftHand_RemoveAllButton.enabled = True

    self.logic.reduceVisibilityOtherModels(modelName)

    numberOfFiducialsLeft, complete = self.placeFiducial(modelName)
    
    self.LeftHand_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
    if complete:
      self.LeftHand_PlaceFiducialButton.enabled = False
      self.LeftHand_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_LeftHand(self):
    logging.debug('onRemoveButtonClicked_LeftHand')

    modelName = 'HandL'

    self.LeftHand_PlaceFiducialButton.enabled = True
    self.LeftHand_RegistrationButton.enabled = False


    numberOfFiducialsLeft, complete = self.removeFiducial(modelName)

    self.LeftHand_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')

    if complete: 
      self.LeftHand_RemoveFiducialButton.enabled = False
      self.LeftHand_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_LeftHand(self):
    logging.debug('onRemoveAllButtonClicked_LeftHand')
    
    modelName = 'HandL'

    self.removeAllFiducials(modelName)

    self.LeftHand_PlaceFiducialButton.enabled = True
    self.LeftHand_PlaceFiducialButton.setText('Place Real Fiducials')
    self.LeftHand_RemoveAllButton.enabled = False
    self.LeftHand_RegistrationButton.enabled = False
    self.LeftHand_SaveButton.enabled = False
    self.LeftHand_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_LeftHand(self):
    logging.debug('onLoadTransformButtonClicked_LeftHand')

    modelName = 'HandL'
    self.loadTransform(modelName)
    

  def onRegistrationButtonClicked_LeftHand(self):
    logging.debug('onRegistrationButtonClicked_LeftHand')

    modelName = 'HandL'

    rms = self.registration(modelName, 'Similarity')

    self.LeftHand_RMSE.setText(rms)
    self.LeftHand_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_LeftHand(self):
    logging.debug('onApplyRegistrationButtonClicked_LeftHand')

    modelName = 'HandL'
    self.applyRegistration(modelName)
    self.LeftHand_SaveButton.enabled = True


  def onSaveRegistrationButtonClicked_LeftHand(self):
    logging.debug('onSaveRegistrationButtonClicked_LeftHand')

    modelName = 'HandL'
    res = self.saveRegistration(modelName)
    if res:
      self.LeftHand_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')
    

    # THUMB LEFT

  def onPlaceButtonClicked_LeftThumb(self):
    logging.debug('onPlaceButtonClicked_LeftThumb')

    modelName = 'ThumbL'
    # Enable the button to remove
    self.LeftThumb_RemoveFiducialButton.enabled = True
    self.LeftThumb_RemoveAllButton.enabled = True

    self.logic.reduceVisibilityOtherModels(modelName)

    numberOfFiducialsLeft, complete = self.placeFiducial(modelName)
    
    self.LeftThumb_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')
    if complete:
      self.LeftThumb_PlaceFiducialButton.enabled = False
      self.LeftThumb_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_LeftThumb(self):
    logging.debug('onRemoveButtonClicked_LeftThumb')

    modelName = 'ThumbL'

    self.LeftThumb_PlaceFiducialButton.enabled = True
    self.LeftThumb_RegistrationButton.enabled = False


    numberOfFiducialsLeft, complete = self.removeFiducial(modelName)

    self.LeftThumb_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsLeft) + ' left)')

    if complete: 
      self.LeftThumb_RemoveFiducialButton.enabled = False
      self.LeftThumb_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_LeftThumb(self):
    logging.debug('onRemoveAllButtonClicked_LeftThumb')
    
    modelName = 'ThumbL'

    self.removeAllFiducials(modelName)

    self.LeftThumb_PlaceFiducialButton.enabled = True
    self.LeftThumb_PlaceFiducialButton.setText('Place Real Fiducials')
    self.LeftThumb_RemoveAllButton.enabled = False
    self.LeftThumb_RegistrationButton.enabled = False
    self.LeftThumb_SaveButton.enabled = False
    self.LeftThumb_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_LeftThumb(self):
    logging.debug('onLoadTransformButtonClicked_LeftThumb')

    modelName = 'ThumbL'
    self.loadTransform(modelName)
    

  def onRegistrationButtonClicked_LeftThumb(self):
    logging.debug('onRegistrationButtonClicked_LeftThumb')

    modelName = 'ThumbL'

    rms = self.registration(modelName, 'Similarity')

    self.LeftThumb_RMSE.setText(rms)
    self.LeftThumb_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_LeftThumb(self):
    logging.debug('onApplyRegistrationButtonClicked_LeftThumb')

    modelName = 'ThumbL'
    self.applyRegistration(modelName)
    self.LeftThumb_SaveButton.enabled = True


  def onSaveRegistrationButtonClicked_LeftThumb(self):
    logging.debug('onSaveRegistrationButtonClicked_LeftThumb')

    modelName = 'ThumbL'
    res = self.saveRegistration(modelName)
    if res:
      self.LeftThumb_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')

  
  # HAND RIGHT

  def onPlaceButtonClicked_RightHand(self):
    logging.debug('onPlaceButtonClicked_RightHand')

    modelName = 'HandR'
    # Enable the button to remove
    self.RightHand_RemoveFiducialButton.enabled = True
    self.RightHand_RemoveAllButton.enabled = True

    self.logic.reduceVisibilityOtherModels(modelName)

    numberOfFiducialsRight, complete = self.placeFiducial(modelName)
    
    self.RightHand_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')
    if complete:
      self.RightHand_PlaceFiducialButton.enabled = False
      self.RightHand_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_RightHand(self):
    logging.debug('onRemoveButtonClicked_RightHand')

    modelName = 'HandR'

    self.RightHand_PlaceFiducialButton.enabled = True
    self.RightHand_RegistrationButton.enabled = False


    numberOfFiducialsRight, complete = self.removeFiducial(modelName)

    self.RightHand_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')

    if complete: 
      self.RightHand_RemoveFiducialButton.enabled = False
      self.RightHand_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_RightHand(self):
    logging.debug('onRemoveAllButtonClicked_RightHand')
    
    modelName = 'HandR'

    self.removeAllFiducials(modelName)

    self.RightHand_PlaceFiducialButton.enabled = True
    self.RightHand_PlaceFiducialButton.setText('Place Real Fiducials')
    self.RightHand_RemoveAllButton.enabled = False
    self.RightHand_RegistrationButton.enabled = False
    self.RightHand_SaveButton.enabled = False
    self.RightHand_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_RightHand(self):
    logging.debug('onLoadTransformButtonClicked_RightHand')

    modelName = 'HandR'
    self.loadTransform(modelName)
    

  def onRegistrationButtonClicked_RightHand(self):
    logging.debug('onRegistrationButtonClicked_RightHand')

    modelName = 'HandR'

    rms = self.registration(modelName, 'Similarity')

    self.RightHand_RMSE.setText(rms)
    self.RightHand_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_RightHand(self):
    logging.debug('onApplyRegistrationButtonClicked_RightHand')

    modelName = 'HandR'
    self.applyRegistration(modelName)
    self.RightHand_SaveButton.enabled = True


  def onSaveRegistrationButtonClicked_RightHand(self):
    logging.debug('onSaveRegistrationButtonClicked_RightHand')

    modelName = 'HandR'
    res = self.saveRegistration(modelName)
    if res:
      self.RightHand_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')
    

    # THUMB RIGHT

  def onPlaceButtonClicked_RightThumb(self):
    logging.debug('onPlaceButtonClicked_RightThumb')

    modelName = 'ThumbR'
    # Enable the button to remove
    self.RightThumb_RemoveFiducialButton.enabled = True
    self.RightThumb_RemoveAllButton.enabled = True

    self.logic.reduceVisibilityOtherModels(modelName)

    numberOfFiducialsRight, complete = self.placeFiducial(modelName)
    
    self.RightThumb_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')
    if complete:
      self.RightThumb_PlaceFiducialButton.enabled = False
      self.RightThumb_RegistrationButton.enabled = True
      self.pointerToTracker.SetAndObserveTransformNodeID(None)


  def onRemoveButtonClicked_RightThumb(self):
    logging.debug('onRemoveButtonClicked_RightThumb')

    modelName = 'ThumbR'

    self.RightThumb_PlaceFiducialButton.enabled = True
    self.RightThumb_RegistrationButton.enabled = False


    numberOfFiducialsRight, complete = self.removeFiducial(modelName)

    self.RightThumb_PlaceFiducialButton.setText('Place Fiducial ('+ str(numberOfFiducialsRight) + ' left)')

    if complete: 
      self.RightThumb_RemoveFiducialButton.enabled = False
      self.RightThumb_RemoveAllButton.enabled = False


  def onRemoveAllButtonClicked_RightThumb(self):
    logging.debug('onRemoveAllButtonClicked_RightThumb')
    
    modelName = 'ThumbR'

    self.removeAllFiducials(modelName)

    self.RightThumb_PlaceFiducialButton.enabled = True
    self.RightThumb_PlaceFiducialButton.setText('Place Real Fiducials')
    self.RightThumb_RemoveAllButton.enabled = False
    self.RightThumb_RegistrationButton.enabled = False
    self.RightThumb_SaveButton.enabled = False
    self.RightThumb_RemoveFiducialButton.enabled = False


  def onLoadTransformButtonClicked_RightThumb(self):
    logging.debug('onLoadTransformButtonClicked_RightThumb')

    modelName = 'ThumbR'
    self.loadTransform(modelName)
    

  def onRegistrationButtonClicked_RightThumb(self):
    logging.debug('onRegistrationButtonClicked_RightThumb')

    modelName = 'ThumbR'

    rms = self.registration(modelName, 'Similarity')

    self.RightThumb_RMSE.setText(rms)
    self.RightThumb_ApplyTransformButton.enabled = True

  
  def onApplyRegistrationButtonClicked_RightThumb(self):
    logging.debug('onApplyRegistrationButtonClicked_RightThumb')

    modelName = 'ThumbR'
    self.applyRegistration(modelName)
    self.RightThumb_SaveButton.enabled = True


  def onSaveRegistrationButtonClicked_RightThumb(self):
    logging.debug('onSaveRegistrationButtonClicked_RightThumb')

    modelName = 'ThumbR'
    res = self.saveRegistration(modelName)
    if res:
      self.RightThumb_SaveButton.enabled = False
    else:
      print('ERROR: Unable to save transform')


  def onStartPivotCalibrationButtonClicked(self):
    logging.debug('onStartPivotCalibrationButtonClicked')

    self.startPivotCalibration('PointerTipToPointer', self.pointerToTracker, self.pointerTipToPointer)


  def onStartSpinCalibrationButtonClicked(self):
    logging.debug('onStartSpinCalibrationButtonClicked')
    calibrationLogic = slicer.modules.pivotcalibration.logic()

    self.calibrationMode = self.spinMode
    self.startPivotCalibrationButton.enabled = False
    self.startSpinCalibrationButton.enabled = False
    self.pivotCalibrationResultTargetNode = self.pointerTipToPointer
    self.pivotCalibrationResultTargetName = 'PointerTipToPointer'
    calibrationLogic.SetAndObserveTransformNode(self.pointerToTracker)
    self.pivotCalibrationStopTime = time.time() + float(self.calibrationTime)
    calibrationLogic.SetRecordingState(True)
    self.onPivotSamplingTimeout()



  def startPivotCalibration(self,toolToReferenceTransformName, toolToReferenceTransformNode, toolTipToToolTransformNode):
    calibrationLogic = slicer.modules.pivotcalibration.logic()

    self.calibrationMode = self.pivotMode

    self.startPivotCalibrationButton.enabled = False
    self.startSpinCalibrationButton.enabled = False

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
    self.startSpinCalibrationButton.enabled = True

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

#
# DeliveryTrainingSpontaneousSetupLogic
#

class DeliveryTrainingSpontaneousSetupLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

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
    handL = slicer.mrmlScene.GetFirstNodeByName('HandLModel')
    handR = slicer.mrmlScene.GetFirstNodeByName('HandRModel')
    thumbL = slicer.mrmlScene.GetFirstNodeByName('ThumbLModel')
    thumbR = slicer.mrmlScene.GetFirstNodeByName('ThumbRModel')
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
      handL.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)
      
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
      handL.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)
      
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
      handL.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)
    
    elif modelName == 'HandL':
      # Show HandL
      handL.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)

    elif modelName == 'ThumbL':
      # Show ThumbL
      thumbL.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      handL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)

    elif modelName == 'HandR':
      # Show HandR
      handR.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      handL.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      thumbR.GetModelDisplayNode().SetOpacity(0.5)

    elif modelName == 'ThumbR':
      # Show ThumbR
      thumbR.GetModelDisplayNode().SetOpacity(1)
      # Reduce visibility rest of models 
      babyBody.GetModelDisplayNode().SetOpacity(0.5)
      babyHead.GetModelDisplayNode().SetOpacity(0.5)
      mother.GetModelDisplayNode().SetOpacity(0.5)
      tummy.GetModelDisplayNode().SetOpacity(0.5)
      handR.GetModelDisplayNode().SetOpacity(0.5)
      handL.GetModelDisplayNode().SetOpacity(0.5)
      thumbL.GetModelDisplayNode().SetOpacity(0.5)
      
    
    

      


