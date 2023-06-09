import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import math
import time
import csv
#
# DeliveryTrainingNavigation_Module
#

class DeliveryTrainingNavigation_Module(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DeliveryTrainingNavigation_Module" # TODO make this more human readable by adding spaces
    self.parent.categories = ["DeliveryTraining"]
    self.parent.dependencies = []
    self.parent.contributors = ["Monica Garcia Sevilla (Universidad Carlos III de Madrid)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This training module was designed to navigate forceps with respect to mother and baby phantoms. It checks their position and movements as training.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Monica Garcia Sevilla from Universidad Carlos III de Madrid.""" # replace with organization, grant and thanks.

#
# DeliveryTrainingNavigation_ModuleWidget
#

class DeliveryTrainingNavigation_ModuleWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Widget variables
    self.logic = DeliveryTrainingNavigation_ModuleLogic()
    self.nonLoadedModels = 0
    self.connect = True
    self.browserName = ''
    self.recording = False
    self.firstTime = True
    self.callbackObserverTag = -1
    self.observerTag = None

    # System error margin
    # self.errorMargin_dist1 = 0
    # self.errorMargin_dist = 0 # mm
    # self.errorMargin_angle = 0 # degrees
    self.errorMargin_dist1 = 3
    self.errorMargin_dist = 6 #3
    self.errorMargin_angle = 10 #5

    # CREATE PATHS
    self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/'
    self.DeliveryTrainingSetupPath_realisticModels = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/Realistic/'
    self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/RealSize/'
    self.DeliveryTrainingPath_record = slicer.modules.deliverytrainingnavigation_module.path.replace("DeliveryTrainingNavigation_Module.py","") + 'Resources/Record/'
    self.DeliveryTrainingSetupPath_dataViews = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/ViewPoints/'
    # self.DeliveryTrainingNavigation_ModulePath_dataSequences = slicer.modules.deliverytrainingnavigation_module.path.replace("DeliveryTrainingNavigation_Module.py","") + 'Resources/Data/Sequences/'
    self.DeliveryTrainingNavigation_ModulePath_dataIcons = slicer.modules.deliverytrainingnavigation_module.path.replace("DeliveryTrainingNavigation_Module.py","") + 'Resources/Data/Icons/'
    self.DeliveryTrainingSetupPath_helpModels = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/Help/'
    # ICONS
    iconPlayPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'play.png')
    iconPausePath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'pause.png')
    iconRetryPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'retry.png')
    iconNextPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'next.png')
    iconHelpPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'info.png')

    # # Error messages
    # self.EM_step1_assembly_forwards = "Forceps are not at the same level"
    # self.EM_step1_assembly_closing = "Forceps are not correctly closed"
    # self.EM_step1_presentation_upsideDown = "Forceps is upside down"
    # self.EM_step1_presentation_rotated = "Forceps is not correctly oriented"
    # self.EM_step2_initial_angle = "Forceps angle to baby is incorrect"
    # self.EM_step2_initial_distance = "Forceps distance to baby's head is too high"
    # self.EM_step2_final_distanceEyeEar = "Forceps is too close or too far from eye or facial nerve"
    # self.EM_step2_final_distanceCheek = "Forceps is too far from cheek"
    # self.EM_step4_initial_distanceEyeEar = "Forceps is too close or too far from eye or facial nerve"
    # self.EM_step4_initial_distanceForceps = "Forceps are not correctly closed"
    # self.EM_step4_initial_distanceBaby = "Forceps distance to baby's cheek is too high"
    # self.EM_step4_initial_distanceFontanelle = "Forceps plane is too close to posterior fontanelle"

    #
    # Setup view
    #

    # Triple 3D layout
    self.layoutManager= slicer.app.layoutManager()
    layoutLogic = self.layoutManager.layoutLogic()
    customLayout = (
      # "<layout type=\"vertical\" split=\"true\" >"
      # "<item>"
      # "  <layout type=\"horizontal\" split=\"false\" >"
      # "<item>"
      # "   <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      # "      <property name=\"viewlabel\" action=\"default\">1</property>"
      # "   </view>"
      # "</item>"
      # "<item>"
      # "    <view class=\"vtkMRMLViewNode\" singletontag=\"2\" type=\"secondary\">"
      # "     <property name=\"viewlabel\" action=\"default\">2</property>"
      # "    </view>"
      # "</item>"
      # "</layout>"
      # "</item>"
      # "<item>"
      # "<view class=\"vtkMRMLViewNode\" singletontag=\"3\">"
      # "    <property name=\"viewlabel\" action=\"default\">3</property>"
      # "</view> </item></layout>")


    "<layout type=\"horizontal\" split=\"false\" >"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
      "    <property name=\"viewlabel\" action=\"default\">1</property>"
      "  </view>"
      " </item>"
      " <item>"
      "  <view class=\"vtkMRMLViewNode\" singletontag=\"2\" type=\"secondary\">"
      "   <property name=\"viewlabel\" action=\"default\">2</property>"
      "  </view>"
      " </item>"
      "</layout>"
    )

    
    self.triple3dviewLayout=509
    layoutLogic.GetLayoutNode().AddLayoutDescription(self.triple3dviewLayout, customLayout)
    
    self.layoutManager.setLayout(self.triple3dviewLayout)

    view = slicer.util.getNode('View1')
    view.SetBoxVisible(0)
    view.SetAxisLabelsVisible(0)

    view = slicer.util.getNode('View2')
    view.SetBoxVisible(0)
    view.SetAxisLabelsVisible(0)

    # view = slicer.util.getNode('View3')
    # view.SetBoxVisible(0)
    # view.SetAxisLabelsVisible(0)

    # make SequenceBrowser Toolbar visible
    try:
      slicer.modules.sequences.setToolBarVisible(1) #4.11 version
    except:
      try:
        slicer.modules.sequencebrowser.setToolBarVisible(1) #4.10.2 version
      except:
        print('SequenceBrowser not found')
      pass

    #
    # LOADING
    #
    self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
    self.loadCollapsibleButton.text = "LOAD"
    self.layout.addWidget(self.loadCollapsibleButton)

    # Layout within the dummy collapsible button
    self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

    # Select how to visualize tummy
    self.loadButtons = qt.QHBoxLayout()
    self.loadFormLayout.addRow(self.loadButtons)

    # Load models and other data
    self.loadDataButton = qt.QPushButton("Load Data")
    self.loadDataButton.enabled = True
    self.loadButtons.addWidget(self.loadDataButton)  

    # Connection to PLUS
    self.connectToPlusButton = qt.QPushButton()
    self.connectToPlusButton.enabled = False
    self.connectToPlusButton.setText('Connect to Plus')
    self.loadButtons.addWidget(self.connectToPlusButton)

    # Apply Transforms
    self.applyTransformsButton = qt.QPushButton()
    self.applyTransformsButton.enabled = False
    self.applyTransformsButton.setText('Apply Transforms')
    self.loadButtons.addWidget(self.applyTransformsButton)
    
    #
    # CONFIGURATION
    #
    self.configurationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.configurationCollapsibleButton.text = "CONFIGURATION"
    self.configurationCollapsibleButton.collapsed = False
    self.layout.addWidget(self.configurationCollapsibleButton)
    
    # Layout within the dummy collapsible button
    configurationFormLayout = qt.QFormLayout(self.configurationCollapsibleButton)

    # User Name
    self.userNameLayout = qt.QHBoxLayout()
    configurationFormLayout.addRow(self.userNameLayout)
    self.userName_label = qt.QLabel('User Name: ')
    self.userName_textInput = qt.QLineEdit()
    self.userName_saveButton = qt.QPushButton()
    self.userName_saveButton.setText('Save')
    self.userNameLayout.addWidget(self.userName_label)
    self.userNameLayout.addWidget(self.userName_textInput)
    self.userNameLayout.addWidget(self.userName_saveButton)
    
    # System's sensibility
    self.sensibilitySelection = qt.QHBoxLayout()
    configurationFormLayout.addRow(self.sensibilitySelection)
    self.sensibilityCheckBox = qt.QCheckBox('Decrease sensibility')
    self.sensibilityCheckBox.checkable = True
    self.sensibilityCheckBox.checked = False
    self.sensibilitySelection.addWidget(self.sensibilityCheckBox)

    #
    # VISUALIZATION
    #
    self.visualizationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.visualizationCollapsibleButton.text = "VISUALIZATION"
    self.visualizationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.visualizationCollapsibleButton)


    # Layout within the dummy collapsible button
    visualizationFormLayout = qt.QFormLayout(self.visualizationCollapsibleButton)

    # --- MANIKIN ---
    self.VisualizationManikinGroupBox = ctk.ctkCollapsibleGroupBox()
    self.VisualizationManikinGroupBox.setTitle("Manikins")
    self.VisualizationManikinGroupBox.collapsed = True
    visualizationFormLayout.addRow(self.VisualizationManikinGroupBox)
    VisualizationManikinGroupBox_Layout = qt.QFormLayout(self.VisualizationManikinGroupBox)
    
    # Select how to visualize belly
    self.bellyViewSelection = qt.QHBoxLayout()
    VisualizationManikinGroupBox_Layout.addRow(self.bellyViewSelection)

    # Text
    self.bellyViewLabel = qt.QLabel('Belly:')    
    self.bellyViewSelection.addWidget(self.bellyViewLabel)

    #NEW TO MAKE THE RADIO BUTTONS MUTUALLY EXCLUSIVE
    self.bellyButtonGroup = qt.QButtonGroup()
    self.bellyButtonGroup.setExclusive(True)

    self.solidRadioButton_belly = qt.QRadioButton('SOLID')
    self.solidRadioButton_belly.checked = False
    self.bellyViewSelection.addWidget(self.solidRadioButton_belly)
    self.bellyButtonGroup.addButton(self.solidRadioButton_belly) #NEW

    self.transparentRadioButton_belly = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_belly.checked = False
    self.bellyViewSelection.addWidget(self.transparentRadioButton_belly)
    self.bellyButtonGroup.addButton(self.transparentRadioButton_belly) #NEW

    self.invisibleRadioButton_belly = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_belly.checked = True
    self.bellyViewSelection.addWidget(self.invisibleRadioButton_belly)
    self.bellyButtonGroup.addButton(self.invisibleRadioButton_belly) #NEW

    # Select how to visualize mother
    self.motherViewSelection = qt.QHBoxLayout()
    VisualizationManikinGroupBox_Layout.addRow(self.motherViewSelection)

    # Text
    self.motherViewLabel = qt.QLabel('Mother:')    
    self.motherViewSelection.addWidget(self.motherViewLabel)

    #NEW
    self.motherButtonGroup = qt.QButtonGroup()
    self.motherButtonGroup.setExclusive(True)

    self.solidRadioButton_mother = qt.QRadioButton('SOLID')
    self.solidRadioButton_mother.checked = False
    self.motherViewSelection.addWidget(self.solidRadioButton_mother)
    self.motherButtonGroup.addButton(self.solidRadioButton_mother)

    self.transparentRadioButton_mother = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_mother.checked = False
    self.motherViewSelection.addWidget(self.transparentRadioButton_mother)
    self.motherButtonGroup.addButton(self.transparentRadioButton_mother)

    self.invisibleRadioButton_mother = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_mother.checked = True
    self.motherViewSelection.addWidget(self.invisibleRadioButton_mother)
    self.motherButtonGroup.addButton(self.invisibleRadioButton_mother)

    # Select how to visualize baby
    self.babyViewSelection = qt.QHBoxLayout()
    VisualizationManikinGroupBox_Layout.addRow(self.babyViewSelection)

    # Text
    self.babyViewLabel = qt.QLabel('Baby:')    
    self.babyViewSelection.addWidget(self.babyViewLabel)

    #NEW 
    self.babyButtonGroup = qt.QButtonGroup()
    self.babyButtonGroup.setExclusive(True)

    self.solidRadioButton_baby = qt.QRadioButton('SOLID')
    self.solidRadioButton_baby.checked = True
    self.babyViewSelection.addWidget(self.solidRadioButton_baby)
    self.babyButtonGroup.addButton(self.solidRadioButton_baby)

    self.transparentRadioButton_baby = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_baby.checked = False
    self.babyViewSelection.addWidget(self.transparentRadioButton_baby)
    self.babyButtonGroup.addButton(self.transparentRadioButton_baby)

    self.invisibleRadioButton_baby = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_baby.checked = False
    self.babyViewSelection.addWidget(self.invisibleRadioButton_baby)
    self.babyButtonGroup.addButton(self.invisibleRadioButton_baby)

    # --- REALISTIC ---
    self.VisualizationRealisticGroupBox = ctk.ctkCollapsibleGroupBox()
    self.VisualizationRealisticGroupBox.setTitle("Realistic")
    self.VisualizationRealisticGroupBox.collapsed = True
    visualizationFormLayout.addRow(self.VisualizationRealisticGroupBox)
    VisualizationRealisticGroupBox_Layout = qt.QFormLayout(self.VisualizationRealisticGroupBox)
    
    # Select how to visualize motherReal
    self.motherRealViewSelection = qt.QHBoxLayout()
    VisualizationRealisticGroupBox_Layout.addRow(self.motherRealViewSelection)

    # Text
    self.motherRealViewLabel = qt.QLabel('Mother:')    
    self.motherRealViewSelection.addWidget(self.motherRealViewLabel)

    #NEW
    self.motherRealButtonGroup = qt.QButtonGroup()
    self.motherRealButtonGroup.setExclusive(True)

    self.solidRadioButton_motherReal = qt.QRadioButton('SOLID')
    self.solidRadioButton_motherReal.checked = True
    self.motherRealViewSelection.addWidget(self.solidRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.solidRadioButton_motherReal)

    self.transparentRadioButton_motherReal = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_motherReal.checked = False
    self.motherRealViewSelection.addWidget(self.transparentRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.transparentRadioButton_motherReal)

    self.invisibleRadioButton_motherReal = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_motherReal.checked = False
    self.motherRealViewSelection.addWidget(self.invisibleRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.invisibleRadioButton_motherReal)

    # Select how to visualize pelvis Right
    self.pelvisRightViewSelection = qt.QHBoxLayout()
    VisualizationRealisticGroupBox_Layout.addRow(self.pelvisRightViewSelection)

    # Text
    self.pelvisRightViewLabel = qt.QLabel('Right Pelvis:')    
    self.pelvisRightViewSelection.addWidget(self.pelvisRightViewLabel)

    #NEW
    self.pelvisRightButtonGroup = qt.QButtonGroup()
    self.pelvisRightButtonGroup.setExclusive(True)

    self.solidRadioButton_pelvisRight = qt.QRadioButton('SOLID')
    self.solidRadioButton_pelvisRight.checked = True
    self.pelvisRightViewSelection.addWidget(self.solidRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.solidRadioButton_pelvisRight)

    self.transparentRadioButton_pelvisRight = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_pelvisRight.checked = False
    self.pelvisRightViewSelection.addWidget(self.transparentRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.transparentRadioButton_pelvisRight)

    self.invisibleRadioButton_pelvisRight = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_pelvisRight.checked = False
    self.pelvisRightViewSelection.addWidget(self.invisibleRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.invisibleRadioButton_pelvisRight)

    # Select how to visualize pelvis Left
    self.pelvisLeftViewSelection = qt.QHBoxLayout()
    VisualizationRealisticGroupBox_Layout.addRow(self.pelvisLeftViewSelection)

    # Text
    self.pelvisLeftViewLabel = qt.QLabel('Left Pelvis:')    
    self.pelvisLeftViewSelection.addWidget(self.pelvisLeftViewLabel)

    #NEW
    self.pelvisLeftButtonGroup = qt.QButtonGroup()
    self.pelvisLeftButtonGroup.setExclusive(True)

    self.solidRadioButton_pelvisLeft = qt.QRadioButton('SOLID')
    self.solidRadioButton_pelvisLeft.checked = True
    self.pelvisLeftViewSelection.addWidget(self.solidRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.solidRadioButton_pelvisLeft)

    self.transparentRadioButton_pelvisLeft = qt.QRadioButton('TRANSPARENT')
    self.transparentRadioButton_pelvisLeft.checked = False
    self.pelvisLeftViewSelection.addWidget(self.transparentRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.transparentRadioButton_pelvisLeft)

    self.invisibleRadioButton_pelvisLeft = qt.QRadioButton('INVISIBLE')
    self.invisibleRadioButton_pelvisLeft.checked = False
    self.pelvisLeftViewSelection.addWidget(self.invisibleRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.invisibleRadioButton_pelvisLeft)

    # Free/Fixed View
    self.freeViewSelection = qt.QHBoxLayout()
    visualizationFormLayout.addRow(self.freeViewSelection)

    # # Text
    # self.freeViewLabel = qt.QLabel('Free View:')    
    # self.freeViewSelection.addWidget(self.freeViewLabel)

    self.freeViewCheckBox = qt.QCheckBox('Free View')
    self.freeViewCheckBox.checkable = True
    self.freeViewCheckBox.checked = False
    self.freeViewSelection.addWidget(self.freeViewCheckBox)

    # STEP 1: Forceps arrangement and presentation

    self.Step1CollapsibleButton = ctk.ctkCollapsibleButton()
    self.Step1CollapsibleButton.text = "STEP 1: Preparation"
    self.Step1CollapsibleButton.collapsed = True
    self.layout.addWidget(self.Step1CollapsibleButton)

    Step1FormLayout = qt.QFormLayout(self.Step1CollapsibleButton)

    # --- FORCEPS ARRANGEMENT ---
    self.ArrangementGroupBox = ctk.ctkCollapsibleGroupBox()
    self.ArrangementGroupBox.setTitle("Forceps Arrangement")
    self.ArrangementGroupBox.collapsed = True
    Step1FormLayout.addRow(self.ArrangementGroupBox)
    ArrangementGroupBox_Layout = qt.QFormLayout(self.ArrangementGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.arrangementText = qt.QLabel('Place forceps together')
    self.arrangementText.setStyleSheet("font-size: 14px; font-weight: bold;")
    ArrangementGroupBox_Layout.addRow(self.arrangementText)

    self.arrangementHorizontalLayout = qt.QHBoxLayout()
    ArrangementGroupBox_Layout.addRow(self.arrangementHorizontalLayout)

     # Check arrangement
    self.check_arrangement = qt.QPushButton("Check")
    self.check_arrangement.enabled = False
    self.arrangementHorizontalLayout.addWidget(self.check_arrangement)

    # Retry arrangement
    self.retry_arrangement = qt.QPushButton("Retry")
    self.retry_arrangement.enabled = False
    self.retry_arrangement_icon = qt.QIcon(iconRetryPath)
    self.retry_arrangement.setIcon(self.retry_arrangement_icon)
    self.arrangementHorizontalLayout.addWidget(self.retry_arrangement)

    # Start/Stop Real Time
    self.start_arrangement = qt.QPushButton("Start")
    self.start_arrangement.enabled = False
    self.start_arrangement_icon_play = qt.QIcon(iconPlayPath)
    self.start_arrangement_icon_pause = qt.QIcon(iconPausePath)
    self.start_arrangement.setIcon(self.start_arrangement_icon_play)
    self.arrangementHorizontalLayout.addWidget(self.start_arrangement)

    # Next step
    self.next_arrangement = qt.QPushButton("Next")
    self.next_arrangement.enabled = False
    self.next_arrangement_icon = qt.QIcon(iconNextPath)
    self.next_arrangement.setIcon(self.next_arrangement_icon)
    self.arrangementHorizontalLayout.addWidget(self.next_arrangement)

    #  Help
    self.help_arrangement = qt.QPushButton("Help")
    self.help_arrangement.enabled = False
    self.help_arrangement_icon = qt.QIcon(iconHelpPath)
    self.help_arrangement.setIcon(self.help_arrangement_icon)
    self.arrangementHorizontalLayout.addWidget(self.help_arrangement)

    # Result
    self.arrangementResultHorizontalLayout = qt.QHBoxLayout()
    ArrangementGroupBox_Layout.addRow(self.arrangementResultHorizontalLayout)

    self.result_arrangement_text = qt.QLabel('Result: ')
    self.arrangementResultHorizontalLayout.addWidget(self.result_arrangement_text)

    self.result_arrangement = qt.QLabel()
    self.arrangementResultHorizontalLayout.addWidget(self.result_arrangement)

    # --- FORCEPS PRESENTATION ---
    self.PresentationGroupBox = ctk.ctkCollapsibleGroupBox()
    self.PresentationGroupBox.setTitle("Forceps Presentation")
    self.PresentationGroupBox.collapsed = True
    Step1FormLayout.addRow(self.PresentationGroupBox)
    PresentationGroupBox_Layout = qt.QFormLayout(self.PresentationGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.presentationText = qt.QLabel('Present the final forceps orientation')
    self.presentationText.setStyleSheet("font-size: 14px; font-weight: bold;")
    PresentationGroupBox_Layout.addRow(self.presentationText)

    self.presentationHorizontalLayout = qt.QHBoxLayout()
    PresentationGroupBox_Layout.addRow(self.presentationHorizontalLayout)

     # Check presentation
    self.check_presentation = qt.QPushButton("Check")
    self.check_presentation.enabled = False
    self.presentationHorizontalLayout.addWidget(self.check_presentation)

    # Retry presentation
    self.retry_presentation = qt.QPushButton("Retry")
    self.retry_presentation.enabled = False
    self.retry_presentation_icon = qt.QIcon(iconRetryPath)
    self.retry_presentation.setIcon(self.retry_presentation_icon)
    self.presentationHorizontalLayout.addWidget(self.retry_presentation)

    # Start/Stop Real Time
    self.start_presentation = qt.QPushButton("Start")
    self.start_presentation.enabled = False
    self.start_presentation_icon_play = qt.QIcon(iconPlayPath)
    self.start_presentation_icon_pause = qt.QIcon(iconPausePath)
    self.start_presentation.setIcon(self.start_presentation_icon_play)
    self.presentationHorizontalLayout.addWidget(self.start_presentation)

    # Next step
    self.next_presentation = qt.QPushButton("Next")
    self.next_presentation.enabled = False
    self.next_presentation_icon = qt.QIcon(iconNextPath)
    self.next_presentation.setIcon(self.next_presentation_icon)
    self.presentationHorizontalLayout.addWidget(self.next_presentation)

    # Help
    self.help_presentation = qt.QPushButton("Help")
    self.help_presentation.enabled = False
    self.help_presentation_icon = qt.QIcon(iconHelpPath)
    self.help_presentation.setIcon(self.help_presentation_icon)
    self.presentationHorizontalLayout.addWidget(self.help_presentation)

    # Result
    self.presentationResultHorizontalLayout = qt.QHBoxLayout()
    PresentationGroupBox_Layout.addRow(self.presentationResultHorizontalLayout)

    self.result_presentation_text = qt.QLabel('Result: ')
    self.presentationResultHorizontalLayout.addWidget(self.result_presentation_text)

    self.result_presentation = qt.QLabel()
    self.presentationResultHorizontalLayout.addWidget(self.result_presentation)

    # STEP 2: First forceps placement

    self.Step2CollapsibleButton = ctk.ctkCollapsibleButton()
    self.Step2CollapsibleButton.text = "STEP 2: First Forceps Placement"
    self.Step2CollapsibleButton.collapsed = True
    self.layout.addWidget(self.Step2CollapsibleButton)

    Step2FormLayout = qt.QFormLayout(self.Step2CollapsibleButton)

    # --- INITIAL POSITION ---
    self.InitialPositionLGroupBox = ctk.ctkCollapsibleGroupBox()
    self.InitialPositionLGroupBox.setTitle("Initial Position")
    self.InitialPositionLGroupBox.collapsed = True
    Step2FormLayout.addRow(self.InitialPositionLGroupBox)
    InitialPositionLGroupBox_Layout = qt.QFormLayout(self.InitialPositionLGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.initialPositionLText = qt.QLabel('Place forceps in its initial position')
    self.initialPositionLText.setStyleSheet("font-size: 14px; font-weight: bold;")
    InitialPositionLGroupBox_Layout.addRow(self.initialPositionLText)

    self.initialPositionLHorizontalLayout = qt.QHBoxLayout()
    InitialPositionLGroupBox_Layout.addRow(self.initialPositionLHorizontalLayout)

     # Check arrangement
    self.check_initialPositionL = qt.QPushButton("Check")
    self.check_initialPositionL.enabled = False
    self.initialPositionLHorizontalLayout.addWidget(self.check_initialPositionL)

    # Retry arrangement
    self.retry_initialPositionL = qt.QPushButton("Retry")
    self.retry_initialPositionL.enabled = False
    self.retry_initialPositionL_icon = qt.QIcon(iconRetryPath)
    self.retry_initialPositionL.setIcon(self.retry_initialPositionL_icon)
    self.initialPositionLHorizontalLayout.addWidget(self.retry_initialPositionL)

    # Start/Stop Real Time
    self.start_initialPositionL = qt.QPushButton("Start")
    self.start_initialPositionL.enabled = False
    self.start_initialPositionL_icon_play = qt.QIcon(iconPlayPath)
    self.start_initialPositionL_icon_pause = qt.QIcon(iconPausePath)
    self.start_initialPositionL.setIcon(self.start_initialPositionL_icon_play)
    self.initialPositionLHorizontalLayout.addWidget(self.start_initialPositionL)

    # Next step
    self.next_initialPositionL = qt.QPushButton("Next")
    self.next_initialPositionL.enabled = False
    self.next_initialPositionL_icon = qt.QIcon(iconNextPath)
    self.next_initialPositionL.setIcon(self.next_initialPositionL_icon)
    self.initialPositionLHorizontalLayout.addWidget(self.next_initialPositionL)

    #  Help
    self.help_initialPositionL = qt.QPushButton("Help")
    self.help_initialPositionL.enabled = False
    self.help_initialPositionL_icon = qt.QIcon(iconHelpPath)
    self.help_initialPositionL.setIcon(self.help_initialPositionL_icon)
    self.initialPositionLHorizontalLayout.addWidget(self.help_initialPositionL)

    # Result
    self.initialPositionLResultHorizontalLayout = qt.QHBoxLayout()
    InitialPositionLGroupBox_Layout.addRow(self.initialPositionLResultHorizontalLayout)

    self.result_initialPositionL_text = qt.QLabel('Result: ')
    self.initialPositionLResultHorizontalLayout.addWidget(self.result_initialPositionL_text)

    self.result_initialPositionL = qt.QLabel()
    self.initialPositionLResultHorizontalLayout.addWidget(self.result_initialPositionL)
    

    # --- ROTATION ---
    self.RotationLGroupBox = ctk.ctkCollapsibleGroupBox()
    self.RotationLGroupBox.setTitle("Rotation")
    self.RotationLGroupBox.collapsed = True
    Step2FormLayout.addRow(self.RotationLGroupBox)
    RotationLGroupBox_Layout = qt.QFormLayout(self.RotationLGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.rotationLText = qt.QLabel('Present the final forceps orientation')
    self.rotationLText.setStyleSheet("font-size: 14px; font-weight: bold;")
    RotationLGroupBox_Layout.addRow(self.rotationLText)

    self.rotationLHorizontalLayout = qt.QHBoxLayout()
    RotationLGroupBox_Layout.addRow(self.rotationLHorizontalLayout)

     # Check presentation
    self.check_rotationL = qt.QPushButton("Check")
    self.check_rotationL.enabled = False
    self.rotationLHorizontalLayout.addWidget(self.check_rotationL)

    # Next step
    self.next_rotationL = qt.QPushButton("Next")
    self.next_rotationL.enabled = False
    self.next_rotationL_icon = qt.QIcon(iconNextPath)
    self.next_rotationL.setIcon(self.next_rotationL_icon)
    self.rotationLHorizontalLayout.addWidget(self.next_rotationL)

    # Help
    self.help_rotationL = qt.QPushButton("Help")
    self.help_rotationL.enabled = False
    self.help_rotationL_icon = qt.QIcon(iconHelpPath)
    self.help_rotationL.setIcon(self.help_rotationL_icon)
    self.rotationLHorizontalLayout.addWidget(self.help_rotationL)
    
    # --- FINAL POSITION ---
    self.FinalPositionLGroupBox = ctk.ctkCollapsibleGroupBox()
    self.FinalPositionLGroupBox.setTitle("Final Position")
    self.FinalPositionLGroupBox.collapsed = True
    Step2FormLayout.addRow(self.FinalPositionLGroupBox)
    FinalPositionLGroupBox_Layout = qt.QFormLayout(self.FinalPositionLGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.finalPositionLText = qt.QLabel('Place forceps in its final position')
    self.finalPositionLText.setStyleSheet("font-size: 14px; font-weight: bold;")
    FinalPositionLGroupBox_Layout.addRow(self.finalPositionLText)

    self.finalPositionLHorizontalLayout = qt.QHBoxLayout()
    FinalPositionLGroupBox_Layout.addRow(self.finalPositionLHorizontalLayout)

     # Check final position
    self.check_finalPositionL = qt.QPushButton("Check")
    self.check_finalPositionL.enabled = False
    self.finalPositionLHorizontalLayout.addWidget(self.check_finalPositionL)

    # Retry final position
    self.retry_finalPositionL = qt.QPushButton("Retry")
    self.retry_finalPositionL.enabled = False
    self.retry_finalPositionL_icon = qt.QIcon(iconRetryPath)
    self.retry_finalPositionL.setIcon(self.retry_finalPositionL_icon)
    self.finalPositionLHorizontalLayout.addWidget(self.retry_finalPositionL)

    # Start/Stop Real Time
    self.start_finalPositionL = qt.QPushButton("Start")
    self.start_finalPositionL.enabled = False
    self.start_finalPositionL_icon_play = qt.QIcon(iconPlayPath)
    self.start_finalPositionL_icon_pause = qt.QIcon(iconPausePath)
    self.start_finalPositionL.setIcon(self.start_finalPositionL_icon_play)
    self.finalPositionLHorizontalLayout.addWidget(self.start_finalPositionL)

    # Next step
    self.next_finalPositionL = qt.QPushButton("Next")
    self.next_finalPositionL.enabled = False
    self.next_finalPositionL_icon = qt.QIcon(iconNextPath)
    self.next_finalPositionL.setIcon(self.next_finalPositionL_icon)
    self.finalPositionLHorizontalLayout.addWidget(self.next_finalPositionL)

    #  Help
    self.help_finalPositionL = qt.QPushButton("Help")
    self.help_finalPositionL.enabled = False
    self.help_finalPositionL_icon = qt.QIcon(iconHelpPath)
    self.help_finalPositionL.setIcon(self.help_finalPositionL_icon)
    self.finalPositionLHorizontalLayout.addWidget(self.help_finalPositionL)

    # Result
    self.finalPositionLResultHorizontalLayout = qt.QHBoxLayout()
    FinalPositionLGroupBox_Layout.addRow(self.finalPositionLResultHorizontalLayout)

    self.result_presentation_text = qt.QLabel('Result: ')
    self.finalPositionLResultHorizontalLayout.addWidget(self.result_presentation_text)

    self.result_finalPositionL = qt.QLabel()
    self.finalPositionLResultHorizontalLayout.addWidget(self.result_finalPositionL)

    # STEP 3: Second forceps placement

    self.Step3CollapsibleButton = ctk.ctkCollapsibleButton()
    self.Step3CollapsibleButton.text = "STEP 3: Second Forceps Placement"
    self.Step3CollapsibleButton.collapsed = True
    self.layout.addWidget(self.Step3CollapsibleButton)

    Step3FormLayout = qt.QFormLayout(self.Step3CollapsibleButton)

    # --- INITIAL POSITION ---
    self.InitialPositionRGroupBox = ctk.ctkCollapsibleGroupBox()
    self.InitialPositionRGroupBox.setTitle("Initial Position")
    self.InitialPositionRGroupBox.collapsed = True
    Step3FormLayout.addRow(self.InitialPositionRGroupBox)
    InitialPositionRGroupBox_Layout = qt.QFormLayout(self.InitialPositionRGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.initialPositionRText = qt.QLabel('Place forceps in its initial position')
    self.initialPositionRText.setStyleSheet("font-size: 14px; font-weight: bold;")
    InitialPositionRGroupBox_Layout.addRow(self.initialPositionRText)

    self.initialPositionRHorizontalLayout = qt.QHBoxLayout()
    InitialPositionRGroupBox_Layout.addRow(self.initialPositionRHorizontalLayout)

     # Check initial position R
    self.check_initialPositionR = qt.QPushButton("Check")
    self.check_initialPositionR.enabled = False
    self.initialPositionRHorizontalLayout.addWidget(self.check_initialPositionR)

    # Retry arrangement
    self.retry_initialPositionR = qt.QPushButton("Retry")
    self.retry_initialPositionR.enabled = False
    self.retry_initialPositionR_icon = qt.QIcon(iconRetryPath)
    self.retry_initialPositionR.setIcon(self.retry_initialPositionR_icon)
    self.initialPositionRHorizontalLayout.addWidget(self.retry_initialPositionR)

    # Start/Stop Real Time
    self.start_initialPositionR = qt.QPushButton("Start")
    self.start_initialPositionR.enabled = False
    self.start_initialPositionR_icon_play = qt.QIcon(iconPlayPath)
    self.start_initialPositionR_icon_pause = qt.QIcon(iconPausePath)
    self.start_initialPositionR.setIcon(self.start_initialPositionR_icon_play)
    self.initialPositionRHorizontalLayout.addWidget(self.start_initialPositionR)

    # Next step
    self.next_initialPositionR = qt.QPushButton("Next")
    self.next_initialPositionR.enabled = False
    self.next_initialPositionR_icon = qt.QIcon(iconNextPath)
    self.next_initialPositionR.setIcon(self.next_initialPositionR_icon)
    self.initialPositionRHorizontalLayout.addWidget(self.next_initialPositionR)

    #  Help
    self.help_initialPositionR = qt.QPushButton("Help")
    self.help_initialPositionR.enabled = False
    self.help_initialPositionR_icon = qt.QIcon(iconHelpPath)
    self.help_initialPositionR.setIcon(self.help_initialPositionR_icon)
    self.initialPositionRHorizontalLayout.addWidget(self.help_initialPositionR)

    # Result
    self.initialPositionRResultHorizontalLayout = qt.QHBoxLayout()
    InitialPositionRGroupBox_Layout.addRow(self.initialPositionRResultHorizontalLayout)

    self.result_initialPositionR_text = qt.QLabel('Result: ')
    self.initialPositionRResultHorizontalLayout.addWidget(self.result_initialPositionR_text)

    self.result_initialPositionR = qt.QLabel()
    self.initialPositionRResultHorizontalLayout.addWidget(self.result_initialPositionR)


    # --- ROTATION ---
    self.RotationRGroupBox = ctk.ctkCollapsibleGroupBox()
    self.RotationRGroupBox.setTitle("Rotation")
    self.RotationRGroupBox.collapsed = True
    Step3FormLayout.addRow(self.RotationRGroupBox)
    RotationRGroupBox_Layout = qt.QFormLayout(self.RotationRGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.rotationRText = qt.QLabel('Present the final forceps orientation')
    self.rotationRText.setStyleSheet("font-size: 14px; font-weight: bold;")
    RotationRGroupBox_Layout.addRow(self.rotationRText)

    self.rotationRHorizontalLayout = qt.QHBoxLayout()
    RotationRGroupBox_Layout.addRow(self.rotationRHorizontalLayout)

     # Check presentation
    self.check_rotationR = qt.QPushButton("Check")
    self.check_rotationR.enabled = False
    self.rotationRHorizontalLayout.addWidget(self.check_rotationR)

    # Next step
    self.next_rotationR = qt.QPushButton("Next")
    self.next_rotationR.enabled = False
    self.next_rotationR_icon = qt.QIcon(iconNextPath)
    self.next_rotationR.setIcon(self.next_rotationR_icon)
    self.rotationRHorizontalLayout.addWidget(self.next_rotationR)

    # Help
    self.help_rotationR = qt.QPushButton("Help")
    self.help_rotationR.enabled = False
    self.help_rotationR_icon = qt.QIcon(iconHelpPath)
    self.help_rotationR.setIcon(self.help_rotationR_icon)
    self.rotationRHorizontalLayout.addWidget(self.help_rotationR)
    
    # --- FINAL POSITION ---
    self.FinalPositionRGroupBox = ctk.ctkCollapsibleGroupBox()
    self.FinalPositionRGroupBox.setTitle("Final Position")
    self.FinalPositionRGroupBox.collapsed = True
    Step3FormLayout.addRow(self.FinalPositionRGroupBox)
    FinalPositionRGroupBox_Layout = qt.QFormLayout(self.FinalPositionRGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.finalPositionRText = qt.QLabel('Place forceps in its final position')
    self.finalPositionRText.setStyleSheet("font-size: 14px; font-weight: bold;")
    FinalPositionRGroupBox_Layout.addRow(self.finalPositionRText)

    self.finalPositionRHorizontalLayout = qt.QHBoxLayout()
    FinalPositionRGroupBox_Layout.addRow(self.finalPositionRHorizontalLayout)

    # Check arrangement
    self.check_finalPositionR = qt.QPushButton("Check")
    self.check_finalPositionR.enabled = False
    self.finalPositionRHorizontalLayout.addWidget(self.check_finalPositionR)

    # Retry arrangement
    self.retry_finalPositionR = qt.QPushButton("Retry")
    self.retry_finalPositionR.enabled = False
    self.retry_finalPositionR_icon = qt.QIcon(iconRetryPath)
    self.retry_finalPositionR.setIcon(self.retry_finalPositionR_icon)
    self.finalPositionRHorizontalLayout.addWidget(self.retry_finalPositionR)

    # Start/Stop Real Time
    self.start_finalPositionR = qt.QPushButton("Start")
    self.start_finalPositionR.enabled = False
    self.start_finalPositionR_icon_play = qt.QIcon(iconPlayPath)
    self.start_finalPositionR_icon_pause = qt.QIcon(iconPausePath)
    self.start_finalPositionR.setIcon(self.start_finalPositionR_icon_play)
    self.finalPositionRHorizontalLayout.addWidget(self.start_finalPositionR)

    # Next step
    self.next_finalPositionR = qt.QPushButton("Next")
    self.next_finalPositionR.enabled = False
    self.next_finalPositionR_icon = qt.QIcon(iconNextPath)
    self.next_finalPositionR.setIcon(self.next_finalPositionR_icon)
    self.finalPositionRHorizontalLayout.addWidget(self.next_finalPositionR)

    #  Help
    self.help_finalPositionR = qt.QPushButton("Help")
    self.help_finalPositionR.enabled = False
    self.help_finalPositionR_icon = qt.QIcon(iconHelpPath)
    self.help_finalPositionR.setIcon(self.help_finalPositionR_icon)
    self.finalPositionRHorizontalLayout.addWidget(self.help_finalPositionR)

    # Result
    self.finalPositionRResultHorizontalLayout = qt.QHBoxLayout()
    FinalPositionRGroupBox_Layout.addRow(self.finalPositionRResultHorizontalLayout)

    self.result_finalPositionR_text = qt.QLabel('Result: ')
    self.finalPositionRResultHorizontalLayout.addWidget(self.result_finalPositionR_text)

    self.result_finalPositionR = qt.QLabel()
    self.finalPositionRResultHorizontalLayout.addWidget(self.result_finalPositionR)

    # STEP 4: Traction 

    self.Step4CollapsibleButton = ctk.ctkCollapsibleButton()
    self.Step4CollapsibleButton.text = "STEP 4: Traction"
    self.Step4CollapsibleButton.collapsed = True
    self.layout.addWidget(self.Step4CollapsibleButton)

    Step4FormLayout = qt.QFormLayout(self.Step4CollapsibleButton)

    # --- TRACTION ---
    self.TractionGroupBox = ctk.ctkCollapsibleGroupBox()
    self.TractionGroupBox.setTitle("Traction")
    self.TractionGroupBox.collapsed = True
    Step4FormLayout.addRow(self.TractionGroupBox)
    TractionGroupBox_Layout = qt.QFormLayout(self.TractionGroupBox)
    # self.Step1GroupBox.setStyleSheet("background-color: rgb(176,231,169);")

    self.tractionText = qt.QLabel('Forceps assembled')
    self.tractionText.setStyleSheet("font-size: 14px; font-weight: bold;")
    TractionGroupBox_Layout.addRow(self.tractionText)

    self.TractionInitHorizontalLayout = qt.QHBoxLayout()
    TractionGroupBox_Layout.addRow(self.TractionInitHorizontalLayout)

    # Check initial position for traction
    self.check_tractionInit = qt.QPushButton("Check")
    self.check_tractionInit.enabled = False
    self.TractionInitHorizontalLayout.addWidget(self.check_tractionInit)

    # Retry initial position for traction
    self.retry_tractionInit = qt.QPushButton("Retry")
    self.retry_tractionInit.enabled = False
    self.retry_tractionInit_icon = qt.QIcon(iconRetryPath)
    self.retry_tractionInit.setIcon(self.retry_tractionInit_icon)
    self.TractionInitHorizontalLayout.addWidget(self.retry_tractionInit)

    # Start/Stop Real Time
    self.start_tractionInit = qt.QPushButton("Start")
    self.start_tractionInit.enabled = False
    self.start_tractionInit_icon_play = qt.QIcon(iconPlayPath)
    self.start_tractionInit_icon_pause = qt.QIcon(iconPausePath)
    self.start_tractionInit.setIcon(self.start_tractionInit_icon_play)
    self.TractionInitHorizontalLayout.addWidget(self.start_tractionInit)

    # Next step
    self.next_tractionInit = qt.QPushButton("Next")
    self.next_tractionInit.enabled = False
    self.next_tractionInit_icon = qt.QIcon(iconNextPath)
    self.next_tractionInit.setIcon(self.next_tractionInit_icon)
    self.TractionInitHorizontalLayout.addWidget(self.next_tractionInit)

    #  Help
    self.help_tractionInit = qt.QPushButton("Help")
    self.help_tractionInit.enabled = False
    self.help_tractionInit_icon = qt.QIcon(iconHelpPath)
    self.help_tractionInit.setIcon(self.help_tractionInit_icon)
    self.TractionInitHorizontalLayout.addWidget(self.help_tractionInit)

    # Result
    self.tractionInitResultHorizontalLayout = qt.QHBoxLayout()
    TractionGroupBox_Layout.addRow(self.tractionInitResultHorizontalLayout)

    self.result_tractionInit_text = qt.QLabel('Result: ')
    self.tractionInitResultHorizontalLayout.addWidget(self.result_tractionInit_text)

    self.result_tractionInit = qt.QLabel()
    self.tractionInitResultHorizontalLayout.addWidget(self.result_tractionInit)

    self.tractionText = qt.QLabel('Perform traction to extract the baby')
    self.tractionText.setStyleSheet("font-size: 14px; font-weight: bold;")
    TractionGroupBox_Layout.addRow(self.tractionText)

    self.TractionHorizontalLayout = qt.QHBoxLayout()
    TractionGroupBox_Layout.addRow(self.TractionHorizontalLayout)

     # Record traction
    self.record_Traction = qt.QPushButton("Record")
    self.record_Traction.enabled = False
    self.TractionHorizontalLayout.addWidget(self.record_Traction)

    # Retry arrangement
    self.retry_Traction = qt.QPushButton("Retry")
    self.retry_Traction.enabled = False
    self.retry_Traction_icon = qt.QIcon(iconRetryPath)
    self.retry_Traction.setIcon(self.retry_Traction_icon)
    self.TractionHorizontalLayout.addWidget(self.retry_Traction)

    # Next step
    self.next_Traction = qt.QPushButton("Next")
    self.next_Traction.enabled = False
    self.next_Traction_icon = qt.QIcon(iconNextPath)
    self.next_Traction.setIcon(self.next_Traction_icon)
    self.TractionHorizontalLayout.addWidget(self.next_Traction)

    #  Help
    self.help_Traction = qt.QPushButton("Help")
    self.help_Traction.enabled = False
    self.help_Traction_icon = qt.QIcon(iconHelpPath)
    self.help_Traction.setIcon(self.help_Traction_icon)
    self.TractionHorizontalLayout.addWidget(self.help_Traction)

    # SAVE DATA
    self.SaveDataCollapsibleButton = ctk.ctkCollapsibleButton()
    self.SaveDataCollapsibleButton.text = "SAVE DATA"
    self.SaveDataCollapsibleButton.collapsed = False
    self.layout.addWidget(self.SaveDataCollapsibleButton)

    SaveDataFormLayout = qt.QFormLayout(self.SaveDataCollapsibleButton)

    self.saveDataButton = qt.QPushButton("SAVE")
    self.saveDataButton.enabled = True
    SaveDataFormLayout.addRow(self.saveDataButton)

    self.resetButton = qt.QPushButton('RESET')
    self.resetButton.enabled = True
    SaveDataFormLayout.addRow(self.resetButton)



    # connections
    # LOADING
    # self.realRadioButton.connect('clicked(bool)', self.onSelectSizeClicked)
    # self.smallRadioButton.connect('clicked(bool)', self.onSelectSizeClicked)
    self.loadDataButton.connect('clicked(bool)', self.onLoadDataButtonClicked)
    self.connectToPlusButton.connect('clicked(bool)', self.onConnectToPlusButtonClicked)
    self.applyTransformsButton.connect('clicked(bool)', self.onApplyTransformsButtonClicked)

    # CONFIGURATION
    self.sensibilityCheckBox.connect('clicked(bool)', self.onSensibilityCheckBoxClicked)
    self.userName_saveButton.connect('clicked(bool)', self.onSaveUserNameButtonClicked)


    # VISUALIZATION
    self.solidRadioButton_belly.connect('clicked(bool)', self.onSelectBellyClicked)
    self.transparentRadioButton_belly.connect('clicked(bool)', self.onSelectBellyClicked)
    self.invisibleRadioButton_belly.connect('clicked(bool)', self.onSelectBellyClicked)
    self.solidRadioButton_mother.connect('clicked(bool)', self.onSelectMotherClicked)
    self.transparentRadioButton_mother.connect('clicked(bool)', self.onSelectMotherClicked)
    self.invisibleRadioButton_mother.connect('clicked(bool)', self.onSelectMotherClicked)
    self.solidRadioButton_baby.connect('clicked(bool)', self.onSelectBabyClicked)
    self.transparentRadioButton_baby.connect('clicked(bool)', self.onSelectBabyClicked)
    self.invisibleRadioButton_baby.connect('clicked(bool)', self.onSelectBabyClicked)
    self.solidRadioButton_motherReal.connect('clicked(bool)', self.onSelectMotherRealClicked)
    self.transparentRadioButton_motherReal.connect('clicked(bool)', self.onSelectMotherRealClicked)
    self.invisibleRadioButton_motherReal.connect('clicked(bool)', self.onSelectMotherRealClicked)
    self.solidRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.transparentRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.invisibleRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.solidRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.transparentRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.invisibleRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.freeViewCheckBox.connect('clicked(bool)', self.onFreeViewCheckBoxClicked)

    # STEP 1: Forceps arrangement and presentation
    self.check_arrangement.connect('clicked(bool)', self.onCheckArrangementClicked)
    self.retry_arrangement.connect('clicked(bool)', self.onRetryArrangementClicked)
    self.start_arrangement.connect('clicked(bool)', self.onStartArrangementClicked)
    self.next_arrangement.connect('clicked(bool)', self.onNextArrangementClicked)
    self.help_arrangement.connect('clicked(bool)', self.onHelpArrangementClicked)
    self.check_presentation.connect('clicked(bool)', self.onCheckPresentationClicked)
    self.retry_presentation.connect('clicked(bool)', self.onRetryPresentationClicked)
    self.start_presentation.connect('clicked(bool)', self.onStartPresentationClicked)
    self.next_presentation.connect('clicked(bool)', self.onNextPresentationClicked)
    self.help_presentation.connect('clicked(bool)', self.onHelpPresentationClicked)

    # STEP 2: First Forceps Placement
    self.check_initialPositionL.connect('clicked(bool)', self.onCheckInitialPositionLClicked)
    self.retry_initialPositionL.connect('clicked(bool)', self.onRetryInitialPositionLClicked)
    self.start_initialPositionL.connect('clicked(bool)', self.onStartInitialPositionLClicked)
    self.next_initialPositionL.connect('clicked(bool)', self.onNextInitialPositionLClicked)
    self.help_initialPositionL.connect('clicked(bool)', self.onHelpInitialPositionLClicked)
    self.check_finalPositionL.connect('clicked(bool)', self.onCheckFinalPositionLClicked)
    self.retry_finalPositionL.connect('clicked(bool)', self.onRetryFinalPositionLClicked)
    self.start_finalPositionL.connect('clicked(bool)', self.onStartFinalPositionLClicked)
    self.next_finalPositionL.connect('clicked(bool)', self.onNextFinalPositionLClicked)
    self.help_finalPositionL.connect('clicked(bool)', self.onHelpFinalPositionLClicked)

    # STEP 3: Second Forceps Placement
    self.check_initialPositionR.connect('clicked(bool)', self.onCheckInitialPositionRClicked)
    self.retry_initialPositionR.connect('clicked(bool)', self.onRetryInitialPositionRClicked)
    self.start_initialPositionR.connect('clicked(bool)', self.onStartInitialPositionRClicked)
    self.next_initialPositionR.connect('clicked(bool)', self.onNextInitialPositionRClicked)
    self.help_initialPositionR.connect('clicked(bool)', self.onHelpInitialPositionRClicked)
    self.check_finalPositionR.connect('clicked(bool)', self.onCheckFinalPositionRClicked)
    self.retry_finalPositionR.connect('clicked(bool)', self.onRetryFinalPositionRClicked)
    self.start_finalPositionR.connect('clicked(bool)', self.onStartFinalPositionRClicked)
    self.next_finalPositionR.connect('clicked(bool)', self.onNextFinalPositionRClicked)
    self.help_finalPositionR.connect('clicked(bool)', self.onHelpFinalPositionRClicked)

    # STEP 4: Traction
    self.check_tractionInit.connect('clicked(bool)', self.onCheckTractionInitClicked)
    self.retry_tractionInit.connect('clicked(bool)', self.onRetryTractionInitClicked)
    self.start_tractionInit.connect('clicked(bool)', self.onStartTractionInitClicked)
    self.next_tractionInit.connect('clicked(bool)', self.onNextTractionInitClicked)
    self.help_tractionInit.connect('clicked(bool)', self.onHelpTractionInitClicked)

    # SAVE DATA
    self.saveDataButton.connect('clicked(bool)', self.onSaveDataButtonClicked)
    self.resetButton.connect('clicked(bool)', self.onResetButtonClicked)
    


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

    logging.debug('Load transforms')

    try:
      self.forcepsLeftModelToForcepsLeft = slicer.util.getNode('ForcepsLeftModelToForcepsLeft')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'ForcepsLeftModelToForcepsLeft.h5')
      self.forcepsLeftModelToForcepsLeft = slicer.util.getNode(pattern="ForcepsLeftModelToForcepsLeft")

    try:
      self.forcepsRightModelToForcepsRight = slicer.util.getNode('ForcepsRightModelToForcepsRight')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'ForcepsRightModelToForcepsRight.h5')
      self.forcepsRightModelToForcepsRight = slicer.util.getNode(pattern="ForcepsRightModelToForcepsRight")

    try:
      self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'BabyHeadModelToBabyHead.h5')
      self.babyHeadModelToBabyHead = slicer.util.getNode(pattern="BabyHeadModelToBabyHead")

    try:
      self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'BabyBodyModelToBabyBody.h5')
      self.babyBodyModelToBabyBody = slicer.util.getNode(pattern="BabyBodyModelToBabyBody")

    try:
      self.motherModelToMother =  slicer.util.getNode('MotherModelToMother')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_data + 'MotherModelToMother.h5')
      self.motherModelToMother = slicer.util.getNode(pattern="MotherModelToMother")

    try:
      self.cameraTransform_front =  slicer.util.getNode('FrontCameraToMother')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'FrontCameraToMother.h5')
      self.cameraTransform_front = slicer.util.getNode(pattern="FrontCameraToMother")

    try:
      self.cameraTransform_side =  slicer.util.getNode('SideCameraToMother')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'SideCameraToMother.h5')
      self.cameraTransform_side = slicer.util.getNode(pattern="SideCameraToMother")

    try:
      self.cameraTransform_up =  slicer.util.getNode('UpCameraToMother')
    except:
      slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'UpCameraToMother.h5')
      self.cameraTransform_up = slicer.util.getNode(pattern="UpCameraToMother")


    # Models
    logging.debug('Load models')

    try:
      self.forcepsLeftModel = slicer.util.getNode('ForcepsLeftModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'ForcepsLeftModel.stl')
      self.forcepsLeftModel = slicer.util.getNode(pattern="ForcepsLeftModel")
      self.forcepsLeftModelDisplay=self.forcepsLeftModel.GetModelDisplayNode()
      self.forcepsLeftModelDisplay.SetColor([1,0,0])

    try:
      self.forcepsRightModel = slicer.util.getNode('ForcepsRightModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'ForcepsRightModel.stl')
      self.forcepsRightModel = slicer.util.getNode(pattern="ForcepsRightModel")
      self.forcepsRightModelDisplay=self.forcepsRightModel.GetModelDisplayNode()
      self.forcepsRightModelDisplay.SetColor([0,0,1])

    try:
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyBodyModel.stl')
      self.babyBodyModel = slicer.util.getNode(pattern="BabyBodyModel")
      self.babyBodyModelDisplay=self.babyBodyModel.GetModelDisplayNode()
      self.babyBodyModelDisplay.SetColor([1,0.68,0.62])

    try:
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyHeadModel.stl')
      self.babyHeadModel = slicer.util.getNode(pattern="BabyHeadModel")
      self.babyHeadModelDisplay=self.babyHeadModel.GetModelDisplayNode()
      self.babyHeadModelDisplay.SetColor([1,0.68,0.62])

    try:
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherModel.stl')
      self.motherModel = slicer.util.getNode(pattern="MotherModel")
      self.motherModelDisplay=self.motherModel.GetModelDisplayNode()
      self.motherModelDisplay.SetColor([1,0.68,0.62])
      self.motherModelDisplay.SetOpacity(0)

    try:
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherTummyModel.stl')
      self.motherTummyModel = slicer.util.getNode(pattern="MotherTummyModel")
      self.motherTummyModelDisplay=self.motherTummyModel.GetModelDisplayNode()
      self.motherTummyModelDisplay.SetColor([1,0.68,0.62])
      self.motherTummyModelDisplay.SetOpacity(0)

    # Realistic Models
    logging.debug('Load models')

    try:
      self.rightPelvis1Model = slicer.util.getNode('rightPelvis1Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis1Model.stl')
      self.rightPelvis1Model = slicer.util.getNode(pattern="rightPelvis1Model")
      self.rightPelvis1ModelDisplay=self.rightPelvis1Model.GetModelDisplayNode()
      self.rightPelvis1ModelDisplay.SetColor(np.array([221,130,101])/255.0)

    try:
      self.rightPelvis2Model = slicer.util.getNode('rightPelvis2Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis2Model.stl')
      self.rightPelvis2Model = slicer.util.getNode(pattern="rightPelvis2Model")
      self.rightPelvis2ModelDisplay=self.rightPelvis2Model.GetModelDisplayNode()
      self.rightPelvis2ModelDisplay.SetColor(np.array([144,238,144])/255.0)

    try:
      self.rightPelvis3Model = slicer.util.getNode('rightPelvis3Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis3Model.stl')
      self.rightPelvis3Model = slicer.util.getNode(pattern="rightPelvis3Model")
      self.rightPelvis3ModelDisplay=self.rightPelvis3Model.GetModelDisplayNode()
      self.rightPelvis3ModelDisplay.SetColor(np.array([111,184,210])/255.0)

    try:
      self.leftPelvis1Model = slicer.util.getNode('leftPelvis1Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis1Model.stl')
      self.leftPelvis1Model = slicer.util.getNode(pattern="leftPelvis1Model")
      self.leftPelvis1ModelDisplay=self.leftPelvis1Model.GetModelDisplayNode()
      self.leftPelvis1ModelDisplay.SetColor(np.array([85,188,255])/255.0)

    try:
      self.leftPelvis2Model = slicer.util.getNode('leftPelvis2Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis2Model.stl')
      self.leftPelvis2Model = slicer.util.getNode(pattern="leftPelvis2Model")
      self.leftPelvis2ModelDisplay=self.leftPelvis2Model.GetModelDisplayNode()
      self.leftPelvis2ModelDisplay.SetColor(np.array([253,135,192])/255.0)

    try:
      self.leftPelvis3Model = slicer.util.getNode('leftPelvis3Model')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis3Model.stl')
      self.leftPelvis3Model = slicer.util.getNode(pattern="leftPelvis3Model")
      self.leftPelvis3ModelDisplay=self.leftPelvis3Model.GetModelDisplayNode()
      self.leftPelvis3ModelDisplay.SetColor(np.array([47,150,103])/255.0)

    try:
      self.coxisRightModel = slicer.util.getNode('coxisRightModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'coxisRightModel.stl')
      self.coxisRightModel = slicer.util.getNode(pattern="coxisRightModel")
      self.coxisRightModelDisplay=self.coxisRightModel.GetModelDisplayNode()
      self.coxisRightModelDisplay.SetColor(np.array([255,255,220])/255.0)

    try:
      self.coxisLeftModel = slicer.util.getNode('coxisLeftModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'coxisLeftModel.stl')
      self.coxisLeftModel = slicer.util.getNode(pattern="coxisLeftModel")
      self.coxisLeftModelDisplay=self.coxisLeftModel.GetModelDisplayNode()
      self.coxisLeftModelDisplay.SetColor(np.array([255,255,220])/255.0)

    try:
      self.middlePelvisModel = slicer.util.getNode('middlePelvisModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'middlePelvisModel.stl')
      self.middlePelvisModel = slicer.util.getNode(pattern="middlePelvisModel")
      self.middlePelvisModelDisplay=self.middlePelvisModel.GetModelDisplayNode()
      self.middlePelvisModelDisplay.SetColor(np.array([188,135,166])/255.0)

    try:
      self.sacrumRightModel = slicer.util.getNode('sacrumRightModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'sacrumRightModel.stl')
      self.sacrumRightModel = slicer.util.getNode(pattern="sacrumRightModel")
      self.sacrumRightModelDisplay=self.sacrumRightModel.GetModelDisplayNode()
      self.sacrumRightModelDisplay.SetColor(np.array([255,255,220])/255.0)

    try:
      self.sacrumLeftModel = slicer.util.getNode('sacrumLeftModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'sacrumLeftModel.stl')
      self.sacrumLeftModel = slicer.util.getNode(pattern="sacrumLeftModel")
      self.sacrumLeftModelDisplay=self.sacrumLeftModel.GetModelDisplayNode()
      self.sacrumLeftModelDisplay.SetColor(np.array([255,255,220])/255.0)

    try:
      self.motherRealisticModel = slicer.util.getNode('motherRealisticModel')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'motherRealisticModel.stl')
      self.motherRealisticModel = slicer.util.getNode(pattern="motherRealisticModel")
      self.motherRealisticModelDisplay=self.motherRealisticModel.GetModelDisplayNode()
      self.motherRealisticModelDisplay.SetColor([1,0.68,0.62])

    # HELP models

    # Presentation

    try:
      self.forcepsLeftModel_presentation = slicer.util.getNode('ForcepsLeftModel_presentation')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsLeftModel_presentation.stl')
      self.forcepsLeftModel_presentation = slicer.util.getNode(pattern="ForcepsLeftModel_presentation")
      self.forcepsLeftModel_presentationDisplay=self.forcepsLeftModel_presentation.GetModelDisplayNode()
      self.forcepsLeftModel_presentationDisplay.SetColor([1,0,0])
      self.forcepsLeftModel_presentationDisplay.SetOpacity(0)

    try:
      self.forcepsRightModel_presentation = slicer.util.getNode('ForcepsRightModel_presentation')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsRightModel_presentation.stl')
      self.forcepsRightModel_presentation = slicer.util.getNode(pattern="ForcepsRightModel_presentation")
      self.forcepsRightModel_presentationDisplay=self.forcepsRightModel_presentation.GetModelDisplayNode()
      self.forcepsRightModel_presentationDisplay.SetColor([0,0,1])
      self.forcepsRightModel_presentationDisplay.SetOpacity(0)

    # Initial Position L

    try:
      self.forcepsLeftModel_initialPositionL = slicer.util.getNode('ForcepsLeftModel_initialPositionL')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsLeftModel_initialPositionL.stl')
      self.forcepsLeftModel_initialPositionL = slicer.util.getNode(pattern="ForcepsLeftModel_initialPositionL")
      self.forcepsLeftModel_initialPositionLDisplay=self.forcepsLeftModel_initialPositionL.GetModelDisplayNode()
      self.forcepsLeftModel_initialPositionLDisplay.SetColor([1,0,0])
      self.forcepsLeftModel_initialPositionLDisplay.SetOpacity(0)

    # Final Position L

    try:
      self.forcepsLeftModel_finalPositionL = slicer.util.getNode('ForcepsLeftModel_finalPositionL')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsLeftModel_finalPositionL.stl')
      self.forcepsLeftModel_finalPositionL = slicer.util.getNode(pattern="ForcepsLeftModel_finalPositionL")
      self.forcepsLeftModel_finalPositionLDisplay=self.forcepsLeftModel_finalPositionL.GetModelDisplayNode()
      self.forcepsLeftModel_finalPositionLDisplay.SetColor([1,0,0])
      self.forcepsLeftModel_finalPositionLDisplay.SetOpacity(0)


    # Initial Position R

    try:
      self.forcepsRightModel_initialPositionR = slicer.util.getNode('ForcepsRightModel_initialPositionR')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsRightModel_initialPositionR.stl')
      self.forcepsRightModel_initialPositionR = slicer.util.getNode(pattern="ForcepsRightModel_initialPositionR")
      self.forcepsRightModel_initialPositionRDisplay=self.forcepsRightModel_initialPositionR.GetModelDisplayNode()
      self.forcepsRightModel_initialPositionRDisplay.SetColor([0,0,1])
      self.forcepsRightModel_initialPositionRDisplay.SetOpacity(0)

    # Final Position R

    try:
      self.forcepsRightModel_finalPositionR = slicer.util.getNode('ForcepsRightModel_finalPositionR')
    except:
      slicer.util.loadModel(self.DeliveryTrainingSetupPath_helpModels + 'ForcepsRightModel_finalPositionR.stl')
      self.forcepsRightModel_finalPositionR = slicer.util.getNode(pattern="ForcepsRightModel_finalPositionR")
      self.forcepsRightModel_finalPositionRDisplay=self.forcepsRightModel_finalPositionR.GetModelDisplayNode()
      self.forcepsRightModel_finalPositionRDisplay.SetColor([0,0,1])
      self.forcepsRightModel_finalPositionRDisplay.SetOpacity(0)


    # LOAD FIDUCIALS
    
    # Fiducials for checking (Left)

    try:
      self.checkFiducialsL = slicer.util.getNode('CheckFiducialsL')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsL.fcsv')
      try:
        self.checkFiducialsL = slicer.util.getNode(pattern="CheckFiducialsL")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsL not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsL.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        self.checkFiducialsL.SetDisplayVisibility(0)

    # Fiducials for checking (Right)
    try:
      self.checkFiducialsR = slicer.util.getNode('CheckFiducialsR')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsR.fcsv')
      try:
        self.checkFiducialsR = slicer.util.getNode(pattern="CheckFiducialsR")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsR not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsR.GetDisplayNode()
        displayNode.SetSelectedColor(1, 0, 0)
        self.checkFiducialsR.SetDisplayVisibility(0)

    # Fiducials for checking forceps in baby head (left)
    try:
      self.checkFiducialsL_finalPosition = slicer.util.getNode('CheckFiducialsL_finalPosition')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsL_finalPosition.fcsv')
      try:
        self.checkFiducialsL_finalPosition = slicer.util.getNode(pattern="CheckFiducialsL_finalPosition")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsL_finalPosition not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsL_finalPosition.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        self.checkFiducialsL_finalPosition.SetDisplayVisibility(0)

    # Fiducials for checking forceps in baby head (right)
    try:
      self.checkFiducialsR_finalPosition = slicer.util.getNode('CheckFiducialsR_finalPosition')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsR_finalPosition.fcsv')
      try:
        self.checkFiducialsR_finalPosition = slicer.util.getNode(pattern="CheckFiducialsR_finalPosition")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsR_finalPosition not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsR_finalPosition.GetDisplayNode()
        displayNode.SetSelectedColor(1, 0, 0)
        self.checkFiducialsR_finalPosition.SetDisplayVisibility(0)

    # Fiducials in baby's sensible parts (eyes and ears)
    try:
      self.checkFiducialsBaby = slicer.util.getNode('CheckFiducialsBaby')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsBaby.fcsv')
      try:
        self.checkFiducialsBaby = slicer.util.getNode(pattern="CheckFiducialsBaby")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsBaby not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsBaby.GetDisplayNode()
        displayNode.SetSelectedColor(1, 0, 0)
        self.checkFiducialsBaby.SetDisplayVisibility(0)

    # Fiducials for creating plane (Left)
    try:
      self.checkFiducialsL_plane = slicer.util.getNode('CheckFiducialsL_plane')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsL_plane.fcsv')
      try:
        self.checkFiducialsL_plane = slicer.util.getNode(pattern="CheckFiducialsL_plane")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsL_plane not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsL_plane.GetDisplayNode()
        displayNode.SetSelectedColor(0, 0, 1)
        self.checkFiducialsL_plane.SetDisplayVisibility(0)

    # Fiducials for creating plane (Right)
    try:
      self.checkFiducialsR_plane = slicer.util.getNode('CheckFiducialsR_plane')
    except:
      slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSetupPath_data + 'CheckFiducialsR_plane.fcsv')
      try:
        self.checkFiducialsR_plane = slicer.util.getNode(pattern="CheckFiducialsR_plane")
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ERROR: CheckFiducialsR_plane not found')
      else:
        # Display them in blue
        displayNode = self.checkFiducialsR_plane.GetDisplayNode()
        displayNode.SetSelectedColor(1, 0, 0)
        self.checkFiducialsR_plane.SetDisplayVisibility(0)

    #Create a cone and line
    try:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
    except:
      marginAngle = 10 + self.errorMargin_angle
      self.logic.showCone('Cone', marginAngle)
    finally:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      if cone.GetDisplayNode():
          cone.GetDisplayNode().SetOpacity(0)
          line.GetDisplayNode().SetOpacity(0)


    redSlice = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
    redSlice.SetSliceVisible(False)

    if self.nonLoadedModels > 0:
      print("Non loaded models: " + str(self.nonLoadedModels))
    else:
      self.loadDataButton.enabled = False
      self.connectToPlusButton.enabled = True

    self.setupViews()

  def setupViews(self):
    import Viewpoint
    viewpointLogic = Viewpoint.ViewpointLogic()

    cameraTransform_front = slicer.util.getNode('FrontCameraToMother')
    cameraTransform_side = slicer.util.getNode('SideCameraToMother')
    cameraTransform_up = slicer.util.getNode('UpCameraToMother')

    viewName1 = 'View1'
    viewName2 = 'View2'
    # viewName3 = 'View3'

    viewNode1 = slicer.util.getNode(viewName1)
    viewNode2 = slicer.util.getNode(viewName2)
    # viewNode3 = slicer.util.getNode(viewName3)

    viewNode1.SetBoxVisible(False)
    viewNode1.SetAxisLabelsVisible(False)
    viewNode2.SetBoxVisible(False)
    viewNode2.SetAxisLabelsVisible(False)
    # viewNode3.SetBoxVisible(False)
    # viewNode3.SetAxisLabelsVisible(False)

    viewpointLogic.getViewpointForViewNode(viewNode1).setViewNode(viewNode1)
    viewpointLogic.getViewpointForViewNode(viewNode2).setViewNode(viewNode2)
    # viewpointLogic.getViewpointForViewNode(viewNode3).setViewNode(viewNode3)

    viewpointLogic.getViewpointForViewNode(viewNode1).bullseyeSetTransformNode(cameraTransform_front)
    viewpointLogic.getViewpointForViewNode(viewNode2).bullseyeSetTransformNode(cameraTransform_side)
    # viewpointLogic.getViewpointForViewNode(viewNode3).bullseyeSetTransformNode(cameraTransform_up)

    viewpointLogic.getViewpointForViewNode(viewNode1).bullseyeStart()
    viewpointLogic.getViewpointForViewNode(viewNode2).bullseyeStart()
    # viewpointLogic.getViewpointForViewNode(viewNode3).bullseyeStart()

  def addWatchedNode(self, watchdogNode, transformNode, warningMessage, playSound):
    nodeID = watchdogNode.AddWatchedNode(transformNode)
    watchdogNode.SetWatchedNodeWarningMessage(nodeID, warningMessage)
    watchdogNode.SetWatchedNodeUpdateTimeToleranceSec(nodeID, 0.2)
    watchdogNode.SetWatchedNodePlaySound(nodeID, playSound)
    

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
        self.connect = False
        self.connectToPlusButton.setText('Disconnect from Plus')
        self.applyTransformsButton.enabled = True
      else:
        print('ERROR: Unable to connect to PLUS')
        logging.debug('ERROR: Unable to connect to PLUS')

    else:
      cnode = slicer.util.getNode('IGTLConnector')
      cnode.Stop()
      self.connect = True
      self.connectToPlusButton.setText('Connect to Plus')

  def onApplyTransformsButtonClicked(self):
    nonLoadedTransforms = 0
    # Create PLUS transforms
    # Load ForcepsLToTracker
    if self.firstTime:
      wd_logic = slicer.vtkSlicerWatchdogLogic()
      wd_logic.AddNewWatchdogNode('WatchdogNode', slicer.mrmlScene)
      wd = slicer.util.getNode('WatchdogNode')
      wd_display = wd.GetDisplayNode()
      # set opacity of background
      wd_display.SetOpacity(0)
      # Set text color
      wd_display.SetColor(1,0,0)
      # Set background color
      wd_display.SetEdgeColor(1,1,1)

      self.start_presentation.enabled = True
      self.check_presentation.enabled = True
      self.next_presentation.enabled = True
      self.help_presentation.enabled = True

      self.start_arrangement.enabled = True
      self.check_arrangement.enabled = True
      self.next_arrangement.enabled = True
      self.help_arrangement.enabled = True

      self.start_initialPositionL.enabled = True
      self.check_initialPositionL.enabled = True
      self.next_initialPositionL.enabled = True
      self.help_initialPositionL.enabled = True

      self.start_finalPositionL.enabled = True
      self.check_finalPositionL.enabled = True
      self.next_finalPositionL.enabled = True
      self.help_finalPositionL.enabled = True

      self.start_initialPositionR.enabled = True
      self.check_initialPositionR.enabled = True
      self.next_initialPositionR.enabled = True
      self.help_initialPositionR.enabled = True

      self.start_finalPositionR.enabled = True
      self.check_finalPositionR.enabled = True
      self.next_finalPositionR.enabled = True
      self.help_finalPositionR.enabled = True
      
      self.next_tractionInit.enabled = True
      self.start_tractionInit.enabled = True
      self.check_tractionInit.enabled = True
      self.help_tractionInit.enabled = True



    try:
      self.forcepsLeftToTracker = slicer.util.getNode('ForcepsLToTracker')
    except:
      print('Unable to receive ForcepsLToTracker')
      nonLoadedTransforms = nonLoadedTransforms + 1
    else:
      if self.firstTime:
        # Add watchdog
        # self.addWatchdog(self.forcepsLeftToTracker, warningMessage = 'ForcepsL is out of view', playSound = True)
        self.addWatchedNode(wd, self.forcepsLeftToTracker, warningMessage = 'ForcepsL is out of view', playSound = True)

    # Load ForcepsRightToTracker
    try:
      self.forcepsRightToTracker = slicer.util.getNode('ForcepsRToTracker')
    except:
      print('Unable to receive ForcepsRToTracker')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # Add watchdog
        # self.addWatchdog(self.forcepsRightToTracker, warningMessage = 'ForcepsR is out of view', playSound = True)
        self.addWatchedNode(wd, self.forcepsRightToTracker, warningMessage = 'ForcepsR is out of view', playSound = True)

    # Load TrackerToForcepsL
    try:
      self.trackerToForcepsLeft = slicer.util.getNode('TrackerToForcepsL')
    except:
      self.trackerToForcepsLeft = slicer.vtkMRMLLinearTransformNode()
      self.trackerToForcepsLeft.SetName('TrackerToForcepsL')
      slicer.mrmlScene.AddNode(self.trackerToForcepsLeft)

    # Load TrackerToForcepsR
    try:
      self.trackerToForcepsRight = slicer.util.getNode('TrackerToForcepsR')
    except:
      self.trackerToForcepsRight = slicer.vtkMRMLLinearTransformNode()
      self.trackerToForcepsRight.SetName('TrackerToForcepsR')
      slicer.mrmlScene.AddNode(self.trackerToForcepsRight)

    # Load BabyHeadToTracker
    try:
      self.babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
    except:
      print('Unable to receive BabyHeadToTracker')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # Add watchdog
        # self.addWatchdog(self.babyHeadToTracker, warningMessage = 'Baby Head is out of view', playSound = True)
        self.addWatchedNode(wd, self.babyHeadToTracker, warningMessage = 'Baby Head is out of view', playSound = True)

    # Load BabyBodyToTracker
    try:
      self.babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
    except:
      print('Unable to receive BabyBodyToTracker')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # Add watchdog
        # self.addWatchdog(self.babyBodyToTracker, warningMessage = 'Baby Body is out of view', playSound = True)
        self.addWatchedNode(wd, self.babyBodyToTracker, warningMessage = 'Baby Body is out of view', playSound = True)

    # Load TrackerToBabyHead
    try:
      self.trackerToBabyHead = slicer.util.getNode('TrackerToBabyHead')
    except:
      print('Unable to receive TrackerToBabyHead')
      nonLoadedTransforms = nonLoadedTransforms +1

    # Load TrackerToBabyBody
    try:
      self.trackerToBabyBody = slicer.util.getNode('TrackerToBabyBody')
    except:
      print('Unable to receive TrackerToBabyBody')
      nonLoadedTransforms = nonLoadedTransforms +1

    # Load MotherToTracker
    try:
      self.motherToTracker = slicer.util.getNode('MotherToTracker')
    except:
      print('Unable to receive MotherToTracker')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # Add watchdog
        # self.addWatchdog(self.motherToTracker, warningMessage = 'Mother is out of view', playSound = True)
        self.addWatchedNode(wd, self.motherToTracker, warningMessage = 'Mother is out of view', playSound = True)

    # Load TrackerToMother
    try:
      self.trackerToMother = slicer.util.getNode('TrackerToMother')
    except:
      print('Unable to receive TrackerToMother')
      nonLoadedTransforms = nonLoadedTransforms +1

    if nonLoadedTransforms==0:
      # Build transform tree
      logging.debug('Set up transform tree')

      self.forcepsLeftModel.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.checkFiducialsL.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.checkFiducialsL_plane.SetAndObserveTransformNodeID(self.forcepsLeftModelToForcepsLeft.GetID())
      self.forcepsLeftModelToForcepsLeft.SetAndObserveTransformNodeID(self.forcepsLeftToTracker.GetID())

      self.forcepsRightModel.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.checkFiducialsR.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.checkFiducialsR_plane.SetAndObserveTransformNodeID(self.forcepsRightModelToForcepsRight.GetID())
      self.forcepsRightModelToForcepsRight.SetAndObserveTransformNodeID(self.forcepsRightToTracker.GetID())

      self.babyBodyModel.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.babyHeadModel.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.checkFiducialsL_finalPosition.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.checkFiducialsR_finalPosition.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.checkFiducialsBaby.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.babyHeadModelToBabyHead.SetAndObserveTransformNodeID(self.babyHeadToTracker.GetID())
      self.babyBodyModelToBabyBody.SetAndObserveTransformNodeID(self.babyBodyToTracker.GetID())

      self.motherModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherTummyModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherModelToMother.SetAndObserveTransformNodeID(self.motherToTracker.GetID())

      self.cameraTransform_front.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.cameraTransform_side.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.cameraTransform_up.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      #help models
      self.forcepsLeftModel_presentation.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.forcepsRightModel_presentation.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.forcepsLeftModel_initialPositionL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.forcepsLeftModel_finalPositionL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.forcepsRightModel_initialPositionR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.forcepsRightModel_finalPositionR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())

      #realistic models
      self.rightPelvis1Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.rightPelvis2Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.rightPelvis3Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.leftPelvis1Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.leftPelvis2Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.leftPelvis3Model.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.sacrumRightModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.sacrumLeftModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.coxisRightModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.coxisLeftModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.middlePelvisModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherRealisticModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      # make sure modelsToTracker or TrackerToModel dont observe any transform
      self.forcepsLeftToTracker.SetAndObserveTransformNodeID(None)
      self.forcepsRightToTracker.SetAndObserveTransformNodeID(None)
      self.babyHeadToTracker.SetAndObserveTransformNodeID(None)
      self.babyBodyToTracker.SetAndObserveTransformNodeID(None)
      self.motherToTracker.SetAndObserveTransformNodeID(None)
      self.trackerToForcepsLeft.SetAndObserveTransformNodeID(None)
      self.trackerToForcepsRight.SetAndObserveTransformNodeID(None)
      self.trackerToBabyHead.SetAndObserveTransformNodeID(None)
      self.trackerToBabyBody.SetAndObserveTransformNodeID(None)
      self.trackerToMother.SetAndObserveTransformNodeID(None)


      if self.firstTime:
        self.ArrangementGroupBox.collapsed = False
        self.firstTime = False
        self.loadCollapsibleButton.collapsed = True
        self.check_arrangement.enabled = True
        self.Step1CollapsibleButton.collapsed = False
      

  def onSelectBellyClicked(self):
    try:
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
    except:
      print('MotherTummyModel not found')
    else:
      if self.solidRadioButton_belly.isChecked():
        self.transparentRadioButton_belly.checked = False
        self.invisibleRadioButton_belly.checked = False
        print('solid')
        self.motherTummyModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_belly.isChecked():
        self.solidRadioButton_belly.checked = False
        self.invisibleRadioButton_belly.checked = False
        print('transparent')
        self.motherTummyModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_belly.checked = False
        self.transparentRadioButton_belly.checked = False
        print('invisible')
        self.motherTummyModel.GetDisplayNode().SetOpacity(0)


  def onSelectMotherClicked(self):
    try:
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      print('MotherModel not found')
    else:
      if self.solidRadioButton_mother.isChecked():
        self.transparentRadioButton_mother.checked = False
        self.invisibleRadioButton_mother.checked = False
        print('solid')
        self.motherModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_mother.isChecked():
        self.solidRadioButton_mother.checked = False
        self.invisibleRadioButton_mother.checked = False
        print('transparent')
        self.motherModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_mother.checked = False
        self.transparentRadioButton_mother.checked = False
        print('invisible')
        self.motherModel.GetDisplayNode().SetOpacity(0)

  def onSelectBabyClicked(self):
    try:
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
    except:
      print('BabyBodyModel not found')
    else:
      if self.solidRadioButton_baby.isChecked():
        self.transparentRadioButton_baby.checked = False
        self.invisibleRadioButton_baby.checked = False
        print('solid')
        self.babyBodyModel.GetDisplayNode().SetOpacity(1)
        self.babyHeadModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_baby.isChecked():
        self.solidRadioButton_baby.checked = False
        self.invisibleRadioButton_baby.checked = False
        print('transparent')
        self.babyBodyModel.GetDisplayNode().SetOpacity(0.5)
        self.babyHeadModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_baby.checked = False
        self.transparentRadioButton_baby.checked = False
        print('invisible')
        self.babyBodyModel.GetDisplayNode().SetOpacity(0)
        self.babyHeadModel.GetDisplayNode().SetOpacity(0)

  def onSelectMotherRealClicked(self):
    try:
      self.motherRealisticModel = slicer.util.getNode('motherRealisticModel')
    except:
      print('motherRealisticModel not found')
    else:
      if self.solidRadioButton_motherReal.isChecked():
        self.transparentRadioButton_motherReal.checked = False
        self.invisibleRadioButton_motherReal.checked = False
        print('solid')
        self.motherRealisticModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_motherReal.isChecked():
        self.solidRadioButton_motherReal.checked = False
        self.invisibleRadioButton_motherReal.checked = False
        print('transparent')
        self.motherRealisticModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_motherReal.checked = False
        self.transparentRadioButton_motherReal.checked = False
        print('invisible')
        self.motherRealisticModel.GetDisplayNode().SetOpacity(0)

  def onSelectPelvisRightClicked(self):
    try:
      self.rightPelvis1Model = slicer.util.getNode('rightPelvis1Model')
      self.rightPelvis2Model = slicer.util.getNode('rightPelvis2Model')
      self.rightPelvis3Model = slicer.util.getNode('rightPelvis3Model')
      self.sacrumRightModel = slicer.util.getNode('sacrumRightModel')
      self.coxisRightModel = slicer.util.getNode('coxisRightModel')
      self.middlePelvisModel = slicer.util.getNode('middlePelvisModel')
    except:
      print('Right Pelvis Models not found')
    else:
      if self.solidRadioButton_pelvisRight.isChecked():
        self.transparentRadioButton_pelvisRight.checked = False
        self.invisibleRadioButton_pelvisRight.checked = False
        print('solid')
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(1)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(1)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(1)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(1)
        self.coxisRightModel.GetDisplayNode().SetOpacity(1)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_pelvisRight.isChecked():
        self.solidRadioButton_pelvisRight.checked = False
        self.invisibleRadioButton_pelvisRight.checked = False
        print('transparent')
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(0.5)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(0.5)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(0.5)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(0.5)
        self.coxisRightModel.GetDisplayNode().SetOpacity(0.5)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_pelvisRight.checked = False
        self.transparentRadioButton_pelvisRight.checked = False
        print('invisible')
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(0)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(0)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(0)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(0)
        self.coxisRightModel.GetDisplayNode().SetOpacity(0)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0)

  def onSelectPelvisLeftClicked(self):
    try:
      self.leftPelvis1Model = slicer.util.getNode('leftPelvis1Model')
      self.leftPelvis2Model = slicer.util.getNode('leftPelvis2Model')
      self.leftPelvis3Model = slicer.util.getNode('leftPelvis3Model')
      self.sacrumLeftModel = slicer.util.getNode('sacrumLeftModel')
      self.coxisLeftModel = slicer.util.getNode('coxisLeftModel')
    except:
      print('left Pelvis Models not found')
    else:
      if self.solidRadioButton_pelvisLeft.isChecked():
        self.transparentRadioButton_pelvisLeft.checked = False
        self.invisibleRadioButton_pelvisLeft.checked = False
        print('solid')
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(1)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(1)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(1)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(1)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(1)
      elif self.transparentRadioButton_pelvisLeft.isChecked():
        self.solidRadioButton_pelvisLeft.checked = False
        self.invisibleRadioButton_pelvisLeft.checked = False
        print('transparent')
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(0.5)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(0.5)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(0.5)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(0.5)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(0.5)
      else:
        self.solidRadioButton_pelvisLeft.checked = False
        self.transparentRadioButton_pelvisLeft.checked = False
        print('invisible')
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(0)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(0)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(0)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(0)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(0)

  def onSaveUserNameButtonClicked(self):
    self.logic.userName = self.userName_textInput.text
    self.configurationCollapsibleButton.collapsed = True

  def onSensibilityCheckBoxClicked(self):
    #cone = slicer.util.getNode('Cone')
    #if cone:
      #slicer.mrmlScene.RemoveNode(cone)
    if self.sensibilityCheckBox.checked:
      # self.errorMargin_dist1 = 3
      # self.errorMargin_dist = 6 #3
      # self.errorMargin_angle = 10 #5
      self.errorMargin_dist1 = 5
      self.errorMargin_dist = 8 #3
      self.errorMargin_angle = 12 #5
      print('Sensibility reduced')
    else:
      # self.errorMargin_dist1 = 0
      # self.errorMargin_dist = 0
      # self.errorMargin_angle = 0
      self.errorMargin_dist1 = 3
      self.errorMargin_dist = 6 #3
      self.errorMargin_angle = 10 #5
      print('Sensibility increased')
    

  def onFreeViewCheckBoxClicked(self):
    import Viewpoint
    viewpointLogic = Viewpoint.ViewpointLogic()
    viewName3 = 'View1'
    cameraTransform_side = slicer.util.getNode('UpCameraToMother')
    viewNode3 = slicer.util.getNode(viewName3)
    viewpointLogic.getViewpointForViewNode(viewNode3).setViewNode(viewNode3)
    viewpointLogic.getViewpointForViewNode(viewNode3).bullseyeSetTransformNode(cameraTransform_side)

    freeViewOn = viewpointLogic.getViewpointForViewNode(viewNode3).getCurrentMode()
    upView = slicer.util.getNode('UpCameraToMother')
    if not self.freeViewCheckBox.checked:
      print('set fixed view')
      motherModelToMother = slicer.util.getNode('MotherModelToMother')
      upView.SetAndObserveTransformNodeID(motherModelToMother.GetID())
    else:
      print('set free view')
      upView.SetAndObserveTransformNodeID(None)
      # Center 3D view
      layoutManager = slicer.app.layoutManager()

      threeDWidget0 = layoutManager.threeDWidget(0)
      threeDView0 = threeDWidget0.threeDView()
      threeDView0.resetFocalPoint()

      threeDWidget1 = layoutManager.threeDWidget(1)
      threeDView1 = threeDWidget1.threeDView()
      threeDView1.resetFocalPoint()

      # threeDWidget2 = layoutManager.threeDWidget(2)
      # threeDView2 = threeDWidget2.threeDView()
      # threeDView2.resetFocalPoint()


  # ------ STEP 1 ------
  def onCheckArrangementClicked(self):
    # error margin (mm)
    margin = 5 +self.errorMargin_dist1
    self.check_arrangement.enabled = False
    res, message = self.logic.checkArrangement(margin)
    if res:
      text = 'CORRECT!'
      self.result_arrangement.setText(text)
      self.next_arrangement.enabled = True
      self.retry_arrangement.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_arrangement.setText(text)
      self.retry_arrangement.enabled = True
    self.logic.recordSoftwareActivity('Arrangement', text.replace('\n','; ')) # Remove new line to write in csv
    self.next_arrangement.enabled = True



  def onRetryArrangementClicked(self):
    self.retry_arrangement.enabled = False
    self.check_arrangement.enabled = True
    self.result_arrangement.setText('')

  def onStartArrangementClicked(self):
    start_stop = self.start_arrangement.text
    toolToReference = slicer.util.getNode('ForcepsLToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_arrangement.setText('Stop')
      self.start_arrangement.setIcon(self.start_arrangement_icon_pause)
      self.check_arrangement.enabled = False
      self.next_arrangement.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_arrangement.setText('Start')
      self.start_arrangement.setIcon(self.start_arrangement_icon_play)
      self.check_arrangement.enabled = True
      self.next_arrangement.enabled = True

  def onNextArrangementClicked(self):
    self.ArrangementGroupBox.collapsed = True
    self.PresentationGroupBox.collapsed = False
    self.check_presentation.enabled = True
    self.onApplyTransformsButtonClicked()
    help_arrangement_text = self.help_arrangement.text
    if help_arrangement_text == 'Hide Help':
      self.help_arrangement.setText('Help')
      self.logic.showHelp(self.forcepsLeftModel_presentation, self.forcepsRightModel_presentation)

  def onHelpArrangementClicked(self):
    help_arrangement_text = self.help_arrangement.text
    if help_arrangement_text == 'Help':
      self.help_arrangement.setText('Hide Help')
    else:
      self.help_arrangement.setText('Help')
    self.logic.showHelp(self.forcepsLeftModel_presentation, self.forcepsRightModel_presentation)

  def onCheckPresentationClicked(self):
    # error in degrees
    margin = 22.5 + self.errorMargin_angle
    marginVertical = 0 + self.errorMargin_dist
    self.check_presentation.enabled = False
    res, message = self.logic.checkPresentation(margin, marginVertical)
    if res:
      text = 'CORRECT!'
      self.result_presentation.setText(text)
      self.next_presentation.enabled = True
      self.retry_presentation.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_presentation.setText(text)
      self.retry_presentation.enabled = True
    self.logic.recordSoftwareActivity('Presentation', text.replace('\n','; '))
    self.next_presentation.enabled = True


  def onRetryPresentationClicked(self):
    self.retry_presentation.enabled = False
    self.check_presentation.enabled = True
    self.result_presentation.setText('')

  def onStartPresentationClicked(self):
    start_stop = self.start_presentation.text
    toolToReference = slicer.util.getNode('ForcepsLToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_presentation.setText('Stop')
      self.start_presentation.setIcon(self.start_presentation_icon_pause)
      self.check_presentation.enabled = False
      self.next_presentation.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_presentation.setText('Start')
      self.start_presentation.setIcon(self.start_presentation_icon_play)
      self.check_presentation.enabled = True
      self.next_presentation.enabled = True

  def onNextPresentationClicked(self):
    self.PresentationGroupBox.collapsed = True
    self.Step1CollapsibleButton.collapsed = True
    self.Step2CollapsibleButton.collapsed = False
    self.InitialPositionLGroupBox.collapsed = False
    self.check_initialPositionL.enabled = True
    self.onApplyTransformsButtonClicked()
    help_presentation_text = self.help_presentation.text
    if help_presentation_text == 'Hide Help':
      self.help_presentation.setText('Help')
      self.logic.showHelp(self.forcepsLeftModel_presentation, self.forcepsRightModel_presentation)


  def onHelpPresentationClicked(self):
    help_presentation_text = self.help_presentation.text
    if help_presentation_text == 'Help':
      self.help_presentation.setText('Hide Help')
    else:
      self.help_presentation.setText('Help')
    self.logic.showHelp(self.forcepsLeftModel_presentation, self.forcepsRightModel_presentation)

  def onCheckInitialPositionLClicked(self):
    # margin in degrees
    marginAngle = 10 + self.errorMargin_angle
    # margin in mm
    marginDistance = 10 + self.errorMargin_dist
    self.check_initialPositionL.enabled = False
    res, message = self.logic.checkInitialPositionL(marginAngle,marginDistance)
    if res:
      text = 'CORRECT!'
      self.result_initialPositionL.setText(text)
      self.next_initialPositionL.enabled = True
      self.retry_initialPositionL.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_initialPositionL.setText(text)
      self.retry_initialPositionL.enabled = True
    self.logic.recordSoftwareActivity('Initial Position Left', text.replace('\n','; '))
    self.next_initialPositionL.enabled = True

  def onRetryInitialPositionLClicked(self):
    self.retry_initialPositionL.enabled = False
    self.check_initialPositionL.enabled = True
    self.result_initialPositionL.setText('')

  def onStartInitialPositionLClicked(self):
    start_stop = self.start_initialPositionL.text
    toolToReference = slicer.util.getNode('ForcepsLToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_initialPositionL.setText('Stop')
      self.start_initialPositionL.setIcon(self.start_initialPositionL_icon_pause)
      self.check_initialPositionL.enabled = False
      self.next_initialPositionL.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_initialPositionL.setText('Start')
      self.start_initialPositionL.setIcon(self.start_initialPositionL_icon_play)
      self.check_initialPositionL.enabled = True
      self.next_initialPositionL.enabled = True

  def onNextInitialPositionLClicked(self):
    self.InitialPositionLGroupBox.collapsed = True
    self.FinalPositionLGroupBox.collapsed = False
    self.check_finalPositionL.enabled = True
    self.onApplyTransformsButtonClicked()
    if self.help_initialPositionL.text  == 'Hide Help':
      self.help_initialPositionL.setText('Help')
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      if cone and line:
        cone.GetDisplayNode().SetOpacity(0)
        line.GetDisplayNode().SetOpacity(0)
      self.logic.showHelp(self.forcepsLeftModel_initialPositionL, None)

  def onHelpInitialPositionLClicked(self):
    help_initialPositionL_text = self.help_initialPositionL.text
    #cone = slicer.util.getNode('Cone')
    #line = slicer.util.getNode('Line')
    marginAngle = 10 + self.errorMargin_angle
    # Show help
    if help_initialPositionL_text == 'Help':
      self.help_initialPositionL.setText('Hide Help')
      try:
        cone = slicer.util.getNode('Cone')
        line = slicer.util.getNode('Line')
      except:
        self.logic.showCone('Cone', marginAngle)
      finally:
        cone = slicer.util.getNode('Cone')
        line = slicer.util.getNode('Line')
        if cone.GetDisplayNode():
          cone.GetDisplayNode().SetOpacity(0.5)
          line.GetDisplayNode().SetOpacity(1)
        else:
          self.logic.showCone('Cone', marginAngle)
        
    # Hide help
    else:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      self.help_initialPositionL.setText('Help')
      cone.GetDisplayNode().SetOpacity(0)
      line.GetDisplayNode().SetOpacity(0)
    self.logic.showHelp(self.forcepsLeftModel_initialPositionL, None)

    # make cone observe head transform if start is not on
    start_stop = self.start_initialPositionL.text
    if start_stop == 'Start':
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      transform = slicer.util.getNode('BabyHeadModelToBabyHead')
      cone.SetAndObserveTransformNodeID(transform.GetID())
      line.SetAndObserveTransformNodeID(transform.GetID())
    else:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      cone.SetAndObserveTransformNodeID(None)
      line.SetAndObserveTransformNodeID(None)
    

  def onCheckFinalPositionLClicked(self):
    # error margins
    #marginAngle = 22.5
    # if self.smallRadioButton.isChecked():
      # marginDistance = 15
      #marginTranslation = 10
    # else:
    marginDistance = 30 + self.errorMargin_dist
    marginDistanceCheek = 10 + self.errorMargin_dist
      #marginTranslation = 20
    self.check_finalPositionL.enabled = False
    res, message = self.logic.checkFinalPositionL(marginDistance, marginDistanceCheek)
    if res:
      text = 'CORRECT!'
      self.result_finalPositionL.setText(text)
      self.next_finalPositionL.enabled = True
      self.retry_finalPositionL.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_finalPositionL.setText(text)
      self.retry_finalPositionL.enabled = True
    self.logic.recordSoftwareActivity('Final Position Left', text.replace('\n','; '))
    self.next_finalPositionL.enabled = True

  def onRetryFinalPositionLClicked(self):
    self.retry_finalPositionL.enabled = False
    self.check_finalPositionL.enabled = True
    self.result_finalPositionL.setText('')

  def onStartFinalPositionLClicked(self):
    start_stop = self.start_finalPositionL.text
    toolToReference = slicer.util.getNode('ForcepsLToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_finalPositionL.setText('Stop')
      self.start_finalPositionL.setIcon(self.start_finalPositionL_icon_pause)
      self.check_finalPositionL.enabled = False
      self.next_finalPositionL.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_finalPositionL.setText('Start')
      self.start_finalPositionL.setIcon(self.start_finalPositionL_icon_play)
      self.check_finalPositionL.enabled = True
      self.next_finalPositionL.enabled = True

  def onNextFinalPositionLClicked(self):
    self.FinalPositionLGroupBox.collapsed = True
    self.Step2CollapsibleButton.collapsed = True
    self.Step3CollapsibleButton.collapsed = False
    self.InitialPositionRGroupBox.collapsed = False
    self.check_initialPositionR.enabled = True
    self.next_initialPositionR.enabled = True
    self.onApplyTransformsButtonClicked()
    if self.help_finalPositionL.text == 'Hide Help':
      self.help_finalPositionL.setText('Help')
      self.logic.showHelp(self.forcepsLeftModel_finalPositionL, None)

  def onHelpFinalPositionLClicked(self):
    help_finalPositionL_text = self.help_finalPositionL.text
    if help_finalPositionL_text == 'Help':
      self.help_finalPositionL.setText('Hide Help')
    else:
      self.help_finalPositionL.setText('Help')
    self.logic.showHelp(self.forcepsLeftModel_finalPositionL, None)

  def onCheckInitialPositionRClicked(self):
    # margin in degrees
    marginAngle = 10 + self.errorMargin_angle
    # margin in mm
    marginDistance = 10 + self.errorMargin_dist
    self.check_initialPositionR.enabled = False
    res, message = self.logic.checkInitialPositionR(marginAngle,marginDistance)
    if res:
      text = 'CORRECT!'
      self.result_initialPositionR.setText(text)
      self.next_initialPositionR.enabled = True
      self.retry_initialPositionR.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_initialPositionR.setText(text)
      self.retry_initialPositionR.enabled = True
    self.logic.recordSoftwareActivity('Initial Position Right', text.replace('\n','; '))
    self.next_initialPositionR.enabled = True

  def onRetryInitialPositionRClicked(self):
    self.retry_initialPositionR.enabled = False
    self.check_initialPositionR.enabled = True
    self.result_initialPositionR.setText('')

  def onStartInitialPositionRClicked(self):
    start_stop = self.start_initialPositionR.text
    toolToReference = slicer.util.getNode('ForcepsRToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_initialPositionR.setText('Stop')
      self.start_initialPositionR.setIcon(self.start_initialPositionR_icon_pause)
      self.check_initialPositionR.enabled = False
      self.next_initialPositionR.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_initialPositionR.setText('Start')
      self.start_initialPositionR.setIcon(self.start_initialPositionR_icon_play)
      self.check_initialPositionR.enabled = True
      self.next_initialPositionR.enabled = True

  def onNextInitialPositionRClicked(self):
    self.InitialPositionRGroupBox.collapsed = True
    self.FinalPositionRGroupBox.collapsed = False
    self.check_finalPositionR.enabled = True
    self.next_finalPositionR.enabled = True
    self.onApplyTransformsButtonClicked()

    if self.help_initialPositionR.text == 'Hide Help':
      self.help_initialPositionR.setText('Help')
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      if cone and line:
        cone.GetDisplayNode().SetOpacity(0)
        line.GetDisplayNode().SetOpacity(0)
      self.logic.showHelp(self.forcepsRightModel_initialPositionR, None)


  def onHelpInitialPositionRClicked(self):
    help_initialPositionR_text = self.help_initialPositionR.text
    #cone = slicer.util.getNode('Cone')
    #line = slicer.util.getNode('Line')
    marginAngle = 10 + self.errorMargin_angle
    # Show help
    if help_initialPositionR_text == 'Help':
      self.help_initialPositionR.setText('Hide Help')
      try:
        cone = slicer.util.getNode('Cone')
        line = slicer.util.getNode('Line')
      except:
        self.logic.showCone('Cone', marginAngle)
      finally:
        cone = slicer.util.getNode('Cone')
        line = slicer.util.getNode('Line')
        if cone.GetDisplayNode():
          cone.GetDisplayNode().SetOpacity(0.5)
          line.GetDisplayNode().SetOpacity(1)
        else:
          self.logic.showCone('Cone', marginAngle)
    # Hide help
    else:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      self.help_initialPositionR.setText('Help')
      cone.GetDisplayNode().SetOpacity(0)
      line.GetDisplayNode().SetOpacity(0)
    self.logic.showHelp(self.forcepsRightModel_initialPositionR, None)

    # make cone observe head transform if start is not on
    start_stop = self.start_initialPositionR.text
    if start_stop == 'Start':
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      transform = slicer.util.getNode('BabyHeadModelToBabyHead')
      cone.SetAndObserveTransformNodeID(transform.GetID())
      line.SetAndObserveTransformNodeID(transform.GetID())
    else:
      cone = slicer.util.getNode('Cone')
      line = slicer.util.getNode('Line')
      cone.SetAndObserveTransformNodeID(None)
      line.SetAndObserveTransformNodeID(None)


  def onCheckFinalPositionRClicked(self):
    # error margins
    # marginAngle = 22.5
    # if self.smallRadioButton.isChecked():
    #   marginDistance = 15
    #   # marginTranslation = 10
    # else:
    marginDistance = 30 + self.errorMargin_dist
    marginDistanceCheek = 10 + self.errorMargin_dist
      # marginTranslation = 20
    self.check_finalPositionR.enabled = False
    res, message = self.logic.checkFinalPositionR(marginDistance, marginDistanceCheek)
    if res:
      text = 'CORRECT!'
      self.result_finalPositionR.setText(text)
      self.next_finalPositionR.enabled = True
      self.retry_finalPositionR.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_finalPositionR.setText(text)
      self.retry_finalPositionR.enabled = True
    self.logic.recordSoftwareActivity('Final Position Right', text.replace('\n','; '))
    self.next_finalPositionR.enabled = True

  def onRetryFinalPositionRClicked(self):
    self.retry_finalPositionR.enabled = False
    self.check_finalPositionR.enabled = True
    self.result_finalPositionR.setText('')

  def onStartFinalPositionRClicked(self):
    start_stop = self.start_finalPositionR.text
    toolToReference = slicer.util.getNode('ForcepsRToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_finalPositionR.setText('Stop')
      self.start_finalPositionR.setIcon(self.start_finalPositionR_icon_pause)
      self.check_finalPositionR.enabled = False
      self.next_finalPositionR.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_finalPositionR.setText('Start')
      self.start_finalPositionR.setIcon(self.start_finalPositionR_icon_play)
      self.check_finalPositionR.enabled = True
      self.next_finalPositionR.enabled = True

  def onNextFinalPositionRClicked(self):
    self.FinalPositionRGroupBox.collapsed = True
    self.Step3CollapsibleButton.collapsed = True
    self.Step4CollapsibleButton.collapsed = False
    self.TractionGroupBox.collapsed = False
    self.check_tractionInit.enabled = True
    self.onApplyTransformsButtonClicked()
    if self.help_finalPositionR.text == 'Hide Help':
      self.help_finalPositionR.setText('Help')
      self.logic.showHelp(self.forcepsRightModel_finalPositionR, None)

  def onHelpFinalPositionRClicked(self):
    help_finalPositionR_text = self.help_finalPositionR.text
    if help_finalPositionR_text == 'Help':
      self.help_finalPositionR.setText('Hide Help')
    else:
      self.help_finalPositionR.setText('Help')
    self.logic.showHelp(self.forcepsRightModel_finalPositionR, None)

  def onCheckTractionInitClicked(self):
    marginDistance = 30 + self.errorMargin_dist
    fingerTip = 10 + self.errorMargin_dist
    fingerBreadth = 20 + self.errorMargin_dist
    self.check_tractionInit.enabled = False
    res, message = self.logic.checkTractionInit(marginDistance, fingerTip, fingerBreadth)
    if res:
      text = 'CORRECT!'
      self.result_tractionInit.setText(text)
      self.next_tractionInit.enabled = True
      self.retry_tractionInit.enabled = True
    else:
      text = 'INCORRECT:\n' + message
      self.result_tractionInit.setText(text)
      self.retry_tractionInit.enabled = True
    self.logic.recordSoftwareActivity('Traction Init', text.replace('\n','; '))
    self.next_tractionInit.enabled = True

  def onRetryTractionInitClicked(self):
    self.retry_tractionInit.enabled = False
    self.check_tractionInit.enabled = True
    self.result_tractionInit.setText('')

  def onStartTractionInitClicked(self):
    start_stop = self.start_tractionInit.text
    toolToReference = slicer.util.getNode('ForcepsRToTracker')
    if start_stop == 'Start':
      self.addActionObserver(toolToReference)
      self.start_tractionInit.setText('Stop')
      self.start_tractionInit.setIcon(self.start_tractionInit_icon_pause)
      self.check_tractionInit.enabled = False
      self.next_tractionInit.enabled = False
    else:
      self.removeActionObserver(toolToReference)
      self.start_tractionInit.setText('Start')
      self.start_tractionInit.setIcon(self.start_tractionInit_icon_play)
      self.check_tractionInit.enabled = True
      self.next_tractionInit.enabled = True
    
  def onNextTractionInitClicked(self):
    self.record_Traction.enabled = True
    self.onApplyTransformsButtonClicked()
    if self.help_tractionInit.text == 'Hide Help':
      self.help_tractionInit.setText('Help')
      self.logic.showHelp(self.forcepsLeftModel_finalPositionL, self.forcepsRightModel_finalPositionR)

  def onHelpTractionInitClicked(self):
    help_tractionInit_text = self.help_tractionInit.text
    if help_tractionInit_text == 'Help':
      self.help_tractionInit.setText('Hide Help')
    else:
      self.help_tractionInit.setText('Help')
    self.logic.showHelp(self.forcepsLeftModel_finalPositionL, self.forcepsRightModel_finalPositionR)

  def onSaveDataButtonClicked(self):
    self.logic.saveSoftwareActivity()
    # self.SaveDataCollapsibleButton.collapsed = True
    print('Data saved!')
  
  def onResetButtonClicked(self):

    # Reset saved information
    self.logic.recordedActivity_action = list()
    self.logic.recordedActivity_timeStamp = list()
    self.logic.recordedActivity_result = list()
    self.logic.userName = 'NoName'
    self.userName_textInput.text = ''

    # Reset buttons
    self.onRetryArrangementClicked()
    self.onNextArrangementClicked()

    self.onRetryPresentationClicked()
    self.onNextPresentationClicked()

    self.onRetryInitialPositionLClicked()
    self.onNextInitialPositionLClicked()
    
    self.onRetryFinalPositionLClicked()
    self.onNextFinalPositionLClicked()

    self.onRetryInitialPositionRClicked()
    self.onNextInitialPositionRClicked()

    self.onRetryFinalPositionRClicked()
    self.onNextFinalPositionRClicked()

    self.onRetryTractionInitClicked()
    self.onNextTractionInitClicked()

    # Apply original transforms
    self.onApplyTransformsButtonClicked()

    # Uncollapse configuration
    self.configurationCollapsibleButton.collapsed = False

    # Collapse last step
    self.Step4CollapsibleButton.collapsed = True
    self.TractionGroupBox.collapsed = True

    # Collapse save
    self.SaveDataCollapsibleButton.collapsed = True

    print('New user')




  def addActionObserver(self, toolToReference):
    if self.callbackObserverTag == -1:
      self.observerTag = toolToReference.AddObserver('ModifiedEvent', self.callbackFunction)
      logging.info('addObserver')

  def removeActionObserver(self, toolToReference):
    self.observerTag = toolToReference.RemoveObserver(self.observerTag)
    self.callbackObserverTag = -1
    # display message correct
    viewNodeID = '2'
    numberOfViews = 2
    id = self.get3DViewIDfromViewNode(viewNodeID, numberOfViews)
    if id == -1:
      print('Error: ViewNode not found')
    else:
      view=slicer.app.layoutManager().threeDWidget(id).threeDView()
      # Set text to "Something"
      view.cornerAnnotation().SetText(vtk.vtkCornerAnnotation.UpperRight,"")
      # Set color to red
      view.cornerAnnotation().GetTextProperty().SetColor(0,1,0)
      # Update the view
      view.forceRender()
      logging.info('removeObserver')


  def callbackFunction(self, transformNode, event = None):
    message = ''
    if self.start_arrangement.text == 'Stop':
      margin = 5 + self.errorMargin_dist
      res, message = self.logic.checkArrangement(margin)
      forcepsLeftModelDisplay = slicer.util.getNode('ForcepsLeftModel').GetModelDisplayNode()
      forcepsRightModelDisplay = slicer.util.getNode('ForcepsRightModel').GetModelDisplayNode()
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
          
    elif self.start_presentation.text == 'Stop':
      # error in degrees
      margin = 22.5 + self.errorMargin_angle
      marginVertical = 0 + self.errorMargin_dist
      res, message = self.logic.checkPresentation(margin, marginVertical)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_initialPositionL.text == 'Stop':
      # margin in degrees
      marginAngle = 10 + self.errorMargin_angle
      # margin in mm
      marginDistance = 10 + self.errorMargin_dist
      res, message = self.logic.checkInitialPositionL(marginAngle,marginDistance)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
      
    elif self.start_finalPositionL.text == 'Stop':
      marginDistance = 30 + self.errorMargin_dist
      marginDistanceCheek = 10 + self.errorMargin_dist
      res, message = self.logic.checkFinalPositionL(marginDistance, marginDistanceCheek)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_initialPositionR.text == 'Stop':
      # margin in degrees
      marginAngle = 10 + self.errorMargin_angle
      # margin in mm
      marginDistance = 10 + self.errorMargin_dist
      res, message = self.logic.checkInitialPositionR(marginAngle,marginDistance)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
    
    elif self.start_finalPositionR.text == 'Stop':
      marginDistance = 30 + self.errorMargin_dist
      marginDistanceCheek = 10 + self.errorMargin_dist
      res, message = self.logic.checkFinalPositionR(marginDistance, marginDistanceCheek)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_tractionInit.text == 'Stop':
      marginDistance = 30 + self.errorMargin_dist
      fingerTip = 10 + self.errorMargin_dist
      fingerBreadth = 20 + self.errorMargin_dist
      res, message = self.logic.checkTractionInit(marginDistance, fingerTip, fingerBreadth)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)


  def get3DViewIDfromViewNode(self, viewNodeID, numberOfViews):
    id = -1
    for i in range(numberOfViews):
      viewNodeID_tmp = slicer.app.layoutManager().threeDWidget(i).mrmlViewNode().GetLayoutName()
      if viewNodeID_tmp == viewNodeID:
        id = i
    return id

  def displayCornerAnnotation(self, correct, message):
    viewNodeID = '2'
    numberOfViews = 2
    id = self.get3DViewIDfromViewNode(viewNodeID, numberOfViews)
    if id == -1:
      print('Error: ViewNode not found')
    else:
      view=slicer.app.layoutManager().threeDWidget(id).threeDView()
      # Set text
      if correct:
        message = 'CORRECT!\n' + message
        view.cornerAnnotation().SetText(vtk.vtkCornerAnnotation.UpperRight,message)
        # Set font scale
        view.cornerAnnotation().SetLinearFontScaleFactor(10)
        # Set color to green
        view.cornerAnnotation().GetTextProperty().SetColor(0,1,0)
        # Update the view
        view.forceRender()
      else:
        message = 'INCORRECT\n' + message
        view.cornerAnnotation().SetText(vtk.vtkCornerAnnotation.UpperRight,message)
        # Set font scale
        view.cornerAnnotation().SetLinearFontScaleFactor(10)
        # Set color to red
        view.cornerAnnotation().GetTextProperty().SetColor(1,0,0)
        # Update the view
        view.forceRender()

#
# DeliveryTrainingNavigation_ModuleLogic
#

class DeliveryTrainingNavigation_ModuleLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  # def createSequence(self, sequenceBrowserNode, sequenceName, transform):
  #   # Create a sequence for a tool and add it to the browser node
  #   sequenceModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode",sequenceName)

  #   sequenceBrowserNode.SetAndObserveMasterSequenceNodeID(sequenceModel.GetID())

  #   sequenceModel.SetDataNodeAtValue(slicer.util.getNode(transform),'0')

  #   # Add sequence and its proxy node
  #   sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
  #   sequenceBrowserLogic.AddSynchronizedNode(sequenceModel, slicer.util.getNode(transform), sequenceBrowserNode)
  #   # Check recording checkbox
  #   sequenceBrowserNode.SetRecording(sequenceModel,True)


  def __init__(self):
    # self.initVector = [0,-4,39]
    # New initVector (more vertical)
    self.initVector = [0,-0.0256326,0.99967143]

    # Activity recording
    self.recordedActivity_action = list()
    self.recordedActivity_timeStamp = list()
    self.recordedActivity_result = list()
    self.userName = 'NoName'

    # Recording Path
    self.DeliveryTrainingPath_record = slicer.modules.deliverytrainingnavigation_module.path.replace("DeliveryTrainingNavigation_Module.py","") + 'Resources/Record/'


  def saveData(self,node_name,path,file_name):
    node = slicer.util.getNode(node_name)
    file_path = os.path.join(path,file_name)
    return slicer.util.saveNode(node,file_path)


  def getDistanceCoordinates(self, fiducials1name,fiducials2name):
    f1 = slicer.util.getNode(fiducials1name)
    f2 = slicer.util.getNode(fiducials2name)
    nfids1 = f1.GetNumberOfFiducials()
    nfids2 = f2.GetNumberOfFiducials()
    if nfids1 != nfids2:
      print('Number of fiducials in both lists doesnt coincide')
    else:
      r = []
      a = []
      s = []
      for i in range(nfids1):
        p1 = [0,0,0,0]
        p2 = [0,0,0,0]
        f1.GetNthFiducialWorldCoordinates(i,p1)
        f2.GetNthFiducialWorldCoordinates(i,p2)
        dist = np.subtract(p1,p2)
        # dist_abs = np.abs(dist)
        # append value for each coordinate in r,a,s
        r.append(dist[0])
        a.append(dist[1])
        s.append(dist[2])
      return r,a,s

  def checkArrangement(self,margin):
    message = ''
    # build transform tree to depend on ForcepsL
    transformName = 'ForcepsLeftModelToForcepsLeft'
    if self.buildTransformTree(transformName):
      # get distances in every axis
      fiducials1name = 'CheckFiducialsL'
      fiducials2name = 'CheckFiducialsR'
      r,a,s = self.getDistanceCoordinates(fiducials1name,fiducials2name)
      # check if coordinates in A are within the margins
      num_fids = np.size(a)
      fidOutOfMargins = False
      # check in AP direction
      for i in range(num_fids):
        if not (-margin)<np.abs(a[i])<=(margin):
        #   print 'Arrangement CORRECT in fiducial ' + str(i) + ' (forwards)'
        # else:
          # print 'Arrangement INCORRECT in fiducial ' + str(i) + ' (forwards)'
          fidOutOfMargins = True
          message = message + 'HANDLES NOT AT THE SAME LEVEL\n'
          break
      for i in range(num_fids-1):
        if not (-margin)<np.abs(r[i])<=(margin):
        #   print 'Arrangement CORRECT in fiducial ' + str(i) + ' (horizontal)'
        # else:
        #   print 'Arrangement INCORRECT in fiducial ' + str(i) + ' (horizontal)'
          fidOutOfMargins = True
          message = message + 'FORCEPS NOT CORRECTLY CLOSED\n'
          break
      if fidOutOfMargins:
        
        return False, message
      else:
        return True, message

  def checkPresentation(self,margin,marginVertical):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      # get distances in every axis
      fiducials1name = 'CheckFiducialsL'
      fiducials2name = 'CheckFiducialsR'
      r,a,s = self.getDistanceCoordinates(fiducials1name,fiducials2name)
      # check if coordinates in A are within the margins
      num_fids = np.size(a)
      fidOutOfMargins = False
      # check in IS direction
      for i in range(num_fids-1):
        if not s[i]<(marginVertical):
        #   print 'Arrangement CORRECT in fiducial ' + str(i) + ' (vertical)'
        # else:
        #   print 'Arrangement INCORRECT in fiducial ' + str(i) + ' (vertical)'
          fidOutOfMargins = True
          message = message + 'FORCEPS UPSIDE DOWN\n'
          break
      # check if rotation in A is bigger than the margin
      fiducials1name_ideal = 'CheckFiducialsL_finalPosition'
      fiducials2name_ideal = 'CheckFiducialsR_finalPosition'
      anglesL, translationL = self.checkRegistrationComponents(fiducials1name, fiducials1name_ideal)
      anglesR, translationR = self.checkRegistrationComponents(fiducials2name, fiducials2name_ideal)
      for i in range(3):
        anglesL[i] = math.degrees(anglesL[i])
        # print 'Angle L ' + str(i) + ': ' + str(anglesL[i])
        anglesR[i] = math.degrees(anglesR[i])
        # print 'Angle R ' + str(i) + ': ' + str(anglesR[i])
      if np.abs(anglesL[1])>margin:
        fidOutOfMargins = True
        # print 'Rotation of Forceps Left of: ' + str(anglesL[1]) + ' degrees in AP'
        message = message + 'LEFT FORCEPS ROTATED\n'
      if np.abs(anglesR[1])>margin:
        fidOutOfMargins = True
        # print 'Rotation of Forceps Right of: ' + str(anglesR[1]) + ' degrees in AP'
        message = message + 'RIGHT FORCEPS ROTATED\n'
      # remove created nodes
      fidsWorld = slicer.util.getNode('FidsWorld')
      slicer.mrmlScene.RemoveNode(fidsWorld)
      fidsWorld = slicer.util.getNode('FidsWorld')
      slicer.mrmlScene.RemoveNode(fidsWorld)
      regL = slicer.util.getNode('RegistrationCheckRotation')
      slicer.mrmlScene.RemoveNode(regL)
      regR = slicer.util.getNode('RegistrationCheckRotation')
      slicer.mrmlScene.RemoveNode(regR)

      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def showHelp(self, model1, model2):
    op = model1.GetDisplayNode().GetOpacity()
    if op==0:
      model1.GetDisplayNode().SetOpacity(0.5)
      if model2:
        model2.GetDisplayNode().SetOpacity(0.5)
    else:
      model1.GetDisplayNode().SetOpacity(0)
      if model2:
        model2.GetDisplayNode().SetOpacity(0)


  def checkInitialPositionL(self, marginAngle, marginDistance):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fiducials1name = 'CheckFiducialsL'
      # Check the angle between the vertical and our fiducials in Forceps
      angle = self.checkVectorsAngle(fiducials1name)
      angle = 180 -angle 
      #print('Angle to ideal direction: ' + str(angle) + '. Margin is ' + str(marginAngle) + ' degrees')
      fidOutOfMargins = False
      if np.abs(angle)>marginAngle:
        fidOutOfMargins = True
        message = message + 'INCORRECT ANGLE\n'
      # Check the tip of the forceps is in contact with the baby's head
      modelName = 'BabyHeadModel'
      dist = self.getDistancePointToModel(fiducials1name,modelName)
      # print 'Distance to baby: ' + str(dist) + '. Margin is ' + str(marginDistance) + ' mm'
      if dist == None:
        print('Error: No intersections found')
        # fidOutOfMargins = True
      elif dist>marginDistance:
        fidOutOfMargins = True
        message = message + 'TIP TOO FAR FROM FETUS\n'
        # print 'Distance out of margin'
      # else:
      #   print 'Distance within margin'
      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def checkFinalPositionL(self, marginDistance, marginDistanceCheek):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fiducials1name = 'CheckFiducialsL'
      # Check the distance between the tip of the forceps and the eye
      dist_eye = self.checkDistanceToEye(fiducials1name, 'left')
      # print 'Distance to eye: ' + str(dist_eye) + '. Margin is ' + str(marginDistance) + ' mm'
      fidOutOfMargins = False
      if not marginDistance<np.abs(dist_eye)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_eye):
          message = message + 'TOO CLOSE TO EYE\n'
        else:
          message = message + 'TOO FAR FROM EYE\n'
      # Check the distance between the tip of the forceps and the ear
      dist_ear = self.checkDistanceToEar(fiducials1name, 'left')
      # print 'Distance to ear: ' + str(dist_ear) + '. Margin is ' + str(marginDistance) + ' mm'
      if not marginDistance<np.abs(dist_ear)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_ear):
          message = message + 'TOO CLOSE TO EAR\n'
        else:
          message = message + 'TOO FAR FROM EAR\n'

      # Check the distance between the tip of the forceps and the cheek
      modelName = 'BabyHeadModel'
      dist = self.getDistancePointToModel(fiducials1name,modelName)
      # print 'Distance to baby: ' + str(dist) + '. Margin is ' + str(marginDistanceCheek) + ' mm'
      if dist == None:
        print('Error: No intersections found')
        # fidOutOfMargins = True
      elif dist>marginDistanceCheek:
        fidOutOfMargins = True
        message = message + 'TOO FAR FROM CHEEKS\n'
        # print 'Distance out of margin'
      # else:
      #   print 'Distance within margin'
      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def checkInitialPositionR(self,marginAngle, marginDistance):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fiducials1name = 'CheckFiducialsR'
      # Check the angle between the vertical and our fiducials in Forceps
      angle = self.checkVectorsAngle(fiducials1name)
      # print 'Angle to ideal direction: ' + str(angle) + '. Margin is ' + str(marginAngle) + ' degrees'
      fidOutOfMargins = False
      if np.abs(angle)>marginAngle:
        fidOutOfMargins = True
        message = message + 'INCORRECT ANGLE\n'
      # Check the tip of the forceps is in contact with the baby's head
      modelName = 'BabyHeadModel'
      dist = self.getDistancePointToModel(fiducials1name,modelName)
      # print 'Distance to baby: ' + str(dist) + '. Margin is ' + str(marginDistance) + ' mm'
      if dist == None:
        print('Error: No intersections found')
        # fidOutOfMargins = True
      elif dist>marginDistance:
        fidOutOfMargins = True
        message = message + 'TIP TOO FAR FROM FETUS\n'
      #   print 'Distance out of margin'
      # else:
      #   print 'Distance within margin'
      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def checkFinalPositionR(self, marginDistance, marginDistanceCheek):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fiducials1name = 'CheckFiducialsR'
      # Check the distance between the tip of the forceps and the eye
      dist_eye = self.checkDistanceToEye(fiducials1name, 'right')
      # print 'Distance to eye: ' + str(dist_eye) + '. Margin is ' + str(marginDistance) + ' mm'
      fidOutOfMargins = False
      if not marginDistance<np.abs(dist_eye)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_eye):
          message = message + 'TOO CLOSE TO EYE\n'
        else:
          message = message + 'TOO FAR FROM EYE\n'
      # Check the distance between the tip of the forceps and the ear
      dist_ear = self.checkDistanceToEar(fiducials1name, 'right')
      # print 'Distance to ear: ' + str(dist_ear) + '. Margin is ' + str(marginDistance) + ' mm'
      if not marginDistance<np.abs(dist_ear)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_ear):
          message = message + 'TOO CLOSE TO EAR\n'
        else:
          message = message + 'TOO FAR FROM EAR\n'

      # Check the distance between the tip of the forceps and the cheek
      modelName = 'BabyHeadModel'
      dist = self.getDistancePointToModel(fiducials1name,modelName)
      # print 'Distance to baby: ' + str(dist) + '. Margin is ' + str(marginDistanceCheek) + ' mm'
      if dist == None:
        print('Error: No intersections found')
        # fidOutOfMargins = True
      elif dist>marginDistanceCheek:
        fidOutOfMargins = True
        message = message + 'TOO FAR FROM CHEEKS\n'
      #   print 'Distance out of margin'
      # else:
      #   print 'Distance within margin'
      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def checkTractionInit(self, marginDistance, fingerTip, fingerBreadth):
    message = ''
    # build transform tree to depend on Baby
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fiducials1name = 'CheckFiducialsL'
      fiducials2name = 'CheckFiducialsR'

      # Check the distance between the tip of the forceps L and the eye
      dist_eye = self.checkDistanceToEye(fiducials1name, 'left')
      # print 'Distance of forcepsL to eye: ' + str(dist_eye)
      fidOutOfMargins = False
      if not marginDistance<np.abs(dist_eye)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_eye):
          message = message + 'LEFT FORCEPS TOO CLOSE TO EYE\n'
        else:
          message = message + 'LEFT FORCEPS TOO FAR FROM EYE\n'

      # Check the distance between the tip of the forceps R and the eye
      dist_eye = self.checkDistanceToEye(fiducials2name, 'right')
      # print 'Distance of forcepsR to eye: ' + str(dist_eye)
      fidOutOfMargins = False
      if not marginDistance<np.abs(dist_eye)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_eye):
          message = message + 'RIGHT FORCEPS TOO CLOSE TO EYE\n'
        else:
          message = message + 'RIGHT FORCEPS TOO FAR FROM EYE\n'


      # Check the distance between the tip of the forceps L and the ear
      dist_ear = self.checkDistanceToEar(fiducials1name, 'left')
      # print 'Distance of forcepsL to ear: ' + str(dist_ear)
      if not marginDistance<np.abs(dist_ear)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_ear):
          message = message + 'LEFT FORCEPS TOO CLOSE TO EAR\n'
        else:
          message = message + 'LEFT FORCEPS TOO FAR FROM EAR\n'

      # Check the distance between the tip of the forceps R and the ear
      dist_ear = self.checkDistanceToEar(fiducials2name, 'right')
      # print 'Distance of forcepsR to ear: ' + str(dist_ear)
      if not marginDistance<np.abs(dist_ear)<(marginDistance*2):
        fidOutOfMargins = True
        if marginDistance>np.abs(dist_ear):
          message = message + 'RIGHT FORCEPS TOO CLOSE TO EAR\n'
        else:
          message = message + 'RIGHT FORCEPS TOO FAR FROM EAR\n'

      # Check the distance between the second CheckFiducialForcepsL and the AP axis
      # dist_edge = 8
      dist_AP = self.checkDistanceToAP(fiducials1name)
      # print 'Distance of forcepsL to AP: ' + str(dist_AP)
      if not -10<=dist_AP<=10:
        # print 'DISTANCE TO AP OF FORCEPSL ABOVE 5mm'
        fidOutOfMargins = True
        message = message + 'LEFT FORCEPS TOO DEVIATED FROM TRACTION DIRECTION\n'
        # Check the distance between the second CheckFiducialForcepsR and the AP axis
      dist_edge = 8
      dist_AP = self.checkDistanceToAP(fiducials2name)
      # print 'Distance of forcepsR to AP: ' + str(dist_AP)
      if not -10<=dist_AP<=10:
        # print 'DISTANCE TO AP OF FORCEPSR ABOVE 5mm'
        fidOutOfMargins = True
        message = message + 'RIGHT FORCEPS TOO DEVIATED FROM TRACTION DIRECTION\n'

      # Check the distance between the first CheckFiducialForceps of both blades
      dist = self.checkDistanceBetweenBlades(fiducials1name, fiducials2name)
      dist_edge = 8
      if dist>(10+dist_edge*2):
        fidOutOfMargins = True
        message = message + 'BLADES ARE TOO SEPARATED\n'

      # Check the distance between the forceps L and the baby
      modelName = 'BabyHeadModel'
      dist = self.getDistancePointToModel(fiducials1name,modelName)
      # print 'Distance of forcepsL to baby: ' + str(dist)
      if dist == None:
        print('Error: No intersections found')
        #fidOutOfMargins = True
      elif dist>fingerTip:
        fidOutOfMargins = True
        message = message + 'LEFT FORCEPS TOO FAR FROM FETUS\n'
      #   print 'Distance of forcepsL out of margin'
      # else:
      #   print 'Distance of forcepsL within margin'
        # Check the distance between the forceps R and the baby
      dist = self.getDistancePointToModel(fiducials2name,modelName)
      # print 'Distance of forcepsR to baby: ' + str(dist)
      if dist == None:
        print('Error: No intersections found')
        #fidOutOfMargins = True
      elif dist>fingerTip:
        fidOutOfMargins = True
        message = message + 'RIGHT FORCEPS TOO FAR FROM FETUS\n'
      #   print 'Distance of forcepsR out of margin'
      # else:
      #   print 'Distance of forcepsR within margin'

      # Check the distance between the fontanelle and the plane defined by the forceps
      fiducialsBaby = 'CheckFiducialsBaby'
      fiducials1name_plane = 'CheckFiducialsL_plane'
      fiducials2name_plane = 'CheckFiducialsR_plane'
      dist_plane = self.checkDistanceToFontanelle(fiducials1name_plane, fiducials2name_plane, fiducialsBaby)
      # print 'Distance to fontanelle: ' + str(dist_plane)
      if dist_plane<fingerBreadth:
        fidOutOfMargins = True
        message = message + 'FORCEPS PLANE TOO CLOSE TO FONTANELLE\n'
      if fidOutOfMargins:
        return False, message
      else:
        return True, message

  def checkDistanceToEye(self, fidsName, left_right):
    fids = slicer.util.getNode(fidsName)
    tip = [0,0,0,0]
    fids.GetNthFiducialWorldCoordinates(3,tip)
    babyFids = slicer.util.getNode('CheckFiducialsBaby')
    eyep = [0,0,0,0]
    if left_right == 'left':
      babyFids.GetNthFiducialWorldCoordinates(3, eyep)
    if left_right == 'right':
      babyFids.GetNthFiducialWorldCoordinates(1, eyep)
    dist_eye = np.linalg.norm(np.subtract(eyep[0:3],tip[0:3]))
    return dist_eye

  def checkDistanceToEar(self, fidsName, left_right):
    fids = slicer.util.getNode(fidsName)
    tip = [0,0,0,0]
    fids.GetNthFiducialWorldCoordinates(3,tip)
    babyFids = slicer.util.getNode('CheckFiducialsBaby')
    earp = [0,0,0,0]
    if left_right == 'left':
      babyFids.GetNthFiducialWorldCoordinates(2, earp)
    if left_right == 'right':
      babyFids.GetNthFiducialWorldCoordinates(0, earp)
    dist_ear = np.linalg.norm(np.subtract(earp[0:3],tip[0:3]))
    return dist_ear

  def checkDistanceToAP(self, fidsName):
    fids = slicer.util.getNode(fidsName)
    handle = [0,0,0,0]
    fids.GetNthFiducialWorldCoordinates(1,handle)
    return handle[0]# we get the coordinate LR

  def checkDistanceBetweenBlades(self, fiducials1Name, fiducials2Name):
    fids1 = slicer.util.getNode(fiducials1Name)
    fids2 = slicer.util.getNode(fiducials2Name)
    f1 = [0,0,0,0]
    f2 = [0,0,0,0]
    fids1.GetNthFiducialWorldCoordinates(0,f1)
    fids2.GetNthFiducialWorldCoordinates(0,f2)
    return np.linalg.norm(np.subtract(f1,f2))


  def checkDistanceToFontanelle(self, fiducials1Name, fiducials2Name, fiducialsBabyName):
    markupsNode1 = slicer.util.getNode(fiducials1Name)
    markupsNode2 = slicer.util.getNode(fiducials2Name)
    # Create plane
    num_f = markupsNode1.GetNumberOfFiducials() -1
    pos = []
    for i in range(num_f):
      p = [0,0,0,0]
      markupsNode1.GetNthFiducialWorldCoordinates(i, p)
      pos.append(p[0:3])
      p2 = [0,0,0,0]
      markupsNode2.GetNthFiducialWorldCoordinates(i, p2)
      pos.append(p2[0:3])
    # convert list to array (for numpy)
    ps = np.array(pos)
    # extraction of mean
    n = num_f*2
    # get mean of points
    m = np.mean(ps, axis=0)
    # mean as matrix
    Mr = np.tile(m, (n, 1))
    Mr2 = np.transpose(Mr)
    A_wom = np.transpose(ps)- Mr2
    Y = np.transpose(A_wom)/np.sqrt(n-1)
    # svd for fiducials
    U, s, V = np.linalg.svd(Y, full_matrices=True)
    # get vector of max variance
    V_maxv = V[0,:]
    # get normal vector
    V_norm = V[2,:]
    # get mean
    m = ps.mean(axis = 0)
    # drawPlane(m,V_norm)

    # get distance point to plane
    fidsBaby = slicer.util.getNode(fiducialsBabyName)
    fontanelleW = [0,0,0,0]
    fidsBaby.GetNthFiducialWorldCoordinates(4,fontanelleW)
    fontanelle = fontanelleW[0:3]
    distPointPlane = distancePointToPlane(fontanelle, m, V_norm)
    return distPointPlane





  def getDistancePointToModel(self, fiducialsName, modelName):
    fids = slicer.util.getNode(fiducialsName)
    model = slicer.util.getNode(modelName)
    p = [0,0,0,0]
    fids.GetNthFiducialWorldCoordinates(3,p)
    closestPoint = self.lineModelIntersection(p[0:3],model)
    if closestPoint == []:
      dist = None
    else:
      dist = np.linalg.norm(np.subtract(p[0:3],closestPoint))
    return dist



  def lineModelIntersection(self, ins, model):

    target = [0,0,0]

    mesh = model.GetPolyData()

    obbTree = vtk.vtkOBBTree()
    obbTree.SetDataSet(mesh)
    obbTree.BuildLocator()

    pointsVTKintersection = vtk.vtkPoints()
    code = obbTree.IntersectWithLine(target, ins, pointsVTKintersection, None)
    
    pointsVTKintersectionData = pointsVTKintersection.GetData()
    number_pointsIntersection = pointsVTKintersectionData.GetNumberOfTuples()

    pointsIntersection_Py = []

    for idx in range(number_pointsIntersection):
      tupla = pointsVTKintersectionData.GetTuple3(idx)
      pointsIntersection_Py.append(tupla) 
 
    # get the closest point to ins from the the list of intersection points
    pointsIntersection_array = np.asarray(pointsIntersection_Py)
    numInter = pointsIntersection_array.size / 3

    diferences_array_norms = np.array([])

    for i in range(int(numInter)):
      dif = np.subtract(ins,pointsIntersection_array[i])
      norm = np.linalg.norm(dif)
      diferences_array_norms = np.append(diferences_array_norms, norm)
      
    #print diferences_array_norms
    closest_insertion_point = []
    if number_pointsIntersection>0:
      closest_insertion_point = pointsIntersection_array[diferences_array_norms.argmin(axis=0)]

    return closest_insertion_point


  def buildTransformTree(self, transformName):
    # get the desired 'root' transform
    try:
      rootTransform = slicer.util.getNode(transformName)
    except:
      print('Error when loading ' + transformName)
      return False
    else:
      # get the inverse
      transform_inverted = self.invertTransform(transformName)
      # get all XToTracker transforms except transformName
      try:
        forcepsLToTracker = slicer.util.getNode('ForcepsLToTracker')
      except:
        print('ForcepsLToTracker not found')
        return False
      try:
        forcepsRToTracker = slicer.util.getNode('ForcepsRToTracker')
      except:
        print('ForcepsRToTracker not found')
        return False
      try:
        babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
      except:
        print('BabyHeadToTracker not found')
        return False
      try:
        babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
      except:
        print('BabyBodyToTracker not found')
        return False
      try:
        motherToTracker = slicer.util.getNode('MotherToTracker')
      except:
        print('MotherToTracker not found')
        return False
      # get the trackerToTool transform for the ToolModelToTool transform
      fidsName = []
      if transformName == 'ForcepsLeftModelToForcepsLeft':
        trackerTransformName_inv = 'TrackerToForcepsL'
        modelName = ['ForcepsLeftModel']
        fidsName = ['CheckFiducialsL','CheckFiducialsL_plane']
      elif transformName == 'ForcepsRightModelToForcepsRight':
        trackerTransformName_inv = 'TrackerToForcepsR'
        modelName = ['ForcepsRightModel']
        fidsName = ['CheckFiducialsR','CheckFiducialsR_plane']
      elif transformName == 'BabyHeadModelToBabyHead':
        trackerTransformName_inv = 'TrackerToBabyHead'
        fidsName = ['CheckFiducialsBaby', 'CheckFiducialsL_finalPosition', 'CheckFiducialsR_finalPosition']
        modelName = ['BabyHeadModel', 'ForcepsLeftModel_presentation', 'ForcepsRightModel_presentation', 'ForcepsLeftModel_initialPositionL',
         'ForcepsLeftModel_finalPositionL', 'ForcepsRightModel_initialPositionR', 'ForcepsRightModel_finalPositionR', 'Cone', 'Line']
      elif transformName == 'BabyBodyModelToBabyBody':
        trackerTransformName_inv = 'TrackerToBabyBody'
        modelName = ['BabyBodyModel']
      elif transformName == 'MotherModelToMother':
        trackerTransformName_inv = 'TrackerToMother'
        modelName = ['MotherModel']
      else:
        print('Input transform for tree not valid')
        return False
      trackerTransform_inv = slicer.util.getNode(trackerTransformName_inv)

      # make the models observe the inverse transform from the tracker
      if transformName != 'ForcepsLeftModelToForcepsLeft':
        forcepsLToTracker.SetAndObserveTransformNodeID(trackerTransform_inv.GetID())
      if transformName != 'ForcepsRightModelToForcepsRight':
        forcepsRToTracker.SetAndObserveTransformNodeID(trackerTransform_inv.GetID())
      if transformName != 'BabyHeadModelToBabyHead':
        babyHeadToTracker.SetAndObserveTransformNodeID(trackerTransform_inv.GetID())
      if transformName != 'BabyBodyModelToBabyBody':
        babyBodyToTracker.SetAndObserveTransformNodeID(trackerTransform_inv.GetID())
      if transformName != 'MotherModelToMother':
        motherToTracker.SetAndObserveTransformNodeID(trackerTransform_inv.GetID())
      # make the inverse transform from the tracker observe the inverse transform of ToolModelToTool
      trackerTransform_inv.SetAndObserveTransformNodeID(transform_inverted.GetID())

      # Get models and fiducials of selected transform and take them out of it
      for name in modelName:
        model = slicer.util.getNode(name)
        if model:
          model.SetAndObserveTransformNodeID(None)
      
      if len(fidsName) > 0:
        num_fids = len(fidsName)
        for i in range(num_fids):
          fids = slicer.util.getNode(fidsName[i])
          fids.SetAndObserveTransformNodeID(None)
      return True


  def invertTransform(self,transformName):
    transform = slicer.util.getNode(transformName)
    transform_matrix = vtk.vtkMatrix4x4()
    # Obtain matrices from tranformation nodes
    transform.GetMatrixTransformToParent(transform_matrix)
    transform_matrix.Invert()
    # create new transform
    name = transformName + '_inverse'
    try:
      transformationNode = slicer.util.getNode(name)
    except:
      transformationNode=slicer.vtkMRMLLinearTransformNode()
      transformationNode.SetName(name)
      slicer.mrmlScene.AddNode(transformationNode)
      transformationNode.SetMatrixTransformToParent(transform_matrix)
    return transformationNode

  def checkRegistrationComponents(self, fids, fidsIdeal):
    # Obtain registration matrix L
    transf = slicer.vtkMRMLLinearTransformNode()
    transf.SetName('RegistrationCheckRotation')
    slicer.mrmlScene.AddNode(transf)
    fiducialsOrig = slicer.util.getNode(fids)
    fiducialsIdeal = slicer.util.getNode(fidsIdeal)
    # create new fiducials using world coordinates
    fiducialsOrig_world = self.fiducialsToWorldCoordinates(fiducialsOrig)
    self.fiducialRegistration(transf, fiducialsIdeal, fiducialsOrig_world, "Rigid")

    # Get rotation L
    transf_matrix = vtk.vtkMatrix4x4() # create vtkmatrix
    # Obtain matrices from tranformation nodes
    transf.GetMatrixTransformToParent(transf_matrix) # copy transform matrix in vtk matrix
    transf_numpyMatrix = self.vtkMatrixToNumpy(transf_matrix) # convert to numpy
    scale, shear, angles, translate, perspective = self.decompose_matrix(transf_numpyMatrix)
    return angles, translate

  def checkVectorsAngle(self, fids1):
    f = slicer.util.getNode(fids1)
    f1 = [0,0,0,0]
    f.GetNthFiducialWorldCoordinates(0,f1)
    f1 = f1[0:3]
    f3 = [0,0,0,0]
    f.GetNthFiducialWorldCoordinates(2,f3)
    f3 = f3[0:3]
    v1 = np.subtract(f1,f3)
    angle = self.angle_between(v1,self.initVector)# old: [0.,0.175,1]
    return angle

  def showCone(self, name, angle):
    # pos0 = [-5,20,-40]
    # pos1 = [-5,-20,350]
    # New vertical line for cone
    pos0 = [-5,5,-40]
    pos1 = [-5,5,350]
    line_length = np.linalg.norm(np.array(pos0)-np.array(pos1))
    radius = np.tan(np.deg2rad(angle))*line_length
    self.createCone(pos0, pos1, radius, name)

  def createCone(self, pos0, pos1, radius, name):

    # Create a vtkPoints object and store the points in it
    points = vtk.vtkPoints()
    points.InsertNextPoint(pos0)
    points.InsertNextPoint(pos1)

    # Create line
    line = vtk.vtkLine()
    line.GetPointIds().SetId(0,0)
    line.GetPointIds().SetId(1,1)
    lineCellArray = vtk.vtkCellArray()
    lineCellArray.InsertNextCell(line)

    lineNode = slicer.vtkMRMLModelNode()
    lineNode.SetName('Line')
    linePolyData = vtk.vtkPolyData()
    lineNode.SetAndObservePolyData(linePolyData)
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetSliceIntersectionVisibility(True)
    modelDisplay.SetColor(0,1,0)
    slicer.mrmlScene.AddNode(modelDisplay)

    lineNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())
    slicer.mrmlScene.AddNode(lineNode)

    lineNode.GetPolyData().SetPoints(points)
    lineNode.GetPolyData().SetLines(lineCellArray)
    cone = cone = vtk.vtkConeSource()
    cone = vtk.vtkConeSource()
    cone.SetResolution(50)

    cone.SetRadius(radius)

    vector = np.subtract(pos0,pos1)
    cone.SetDirection([vector[0],vector[1],vector[2]])
    dist = np.linalg.norm(vector)
    cone.SetHeight(dist)

    coneModel = slicer.vtkMRMLModelNode()
    coneModel.SetName(name)

    coneModel.SetPolyDataConnection(cone.GetOutputPort())
    slicer.mrmlScene.AddNode(coneModel)

    modelDisplay1 = slicer.vtkMRMLModelDisplayNode()
    modelDisplay1.SetSliceIntersectionVisibility(True)
    modelDisplay1.SetColor(0,1,1)
    modelDisplay1.SetOpacity(0.30)
    slicer.mrmlScene.AddNode(modelDisplay1)

    coneModel.SetAndObserveDisplayNodeID(modelDisplay1.GetID())
    slicer.mrmlScene.AddNode(coneModel)

    x3 = [(pos1[0]-pos0[0])/2 + pos0[0], (pos1[1]-pos0[1])/2 +pos0[1], (pos1[2]-pos0[2])/2 +pos0[2]]
    cone.SetCenter(x3)



  def fiducialsToWorldCoordinates(self, f):
    f_world = slicer.vtkMRMLMarkupsFiducialNode()
    f_world.SetName('FidsWorld')
    slicer.mrmlScene.AddNode(f_world)
    for i in range(f.GetNumberOfFiducials()):
      p = [0,0,0,0]
      f.GetNthFiducialWorldCoordinates(i,p)
      f_world.AddFiducialFromArray(p[0:3])
    return f_world

  def vtkMatrixToNumpy(self, vtk_matrix):
    numpy_matrix = np.zeros((4,4))
    numpy_matrix[0,0] = vtk_matrix.GetElement(0, 0)
    numpy_matrix[0,1] = vtk_matrix.GetElement(0, 1)
    numpy_matrix[0,2] = vtk_matrix.GetElement(0, 2) 
    numpy_matrix[0,3] = vtk_matrix.GetElement(0, 3) 
    numpy_matrix[1,0] = vtk_matrix.GetElement(1, 0)
    numpy_matrix[1,1] = vtk_matrix.GetElement(1, 1) 
    numpy_matrix[1,2] = vtk_matrix.GetElement(1, 2)
    numpy_matrix[1,3] = vtk_matrix.GetElement(1, 3)
    numpy_matrix[2,0] = vtk_matrix.GetElement(2, 0)  
    numpy_matrix[2,1] = vtk_matrix.GetElement(2, 1)
    numpy_matrix[2,2] = vtk_matrix.GetElement(2, 2)
    numpy_matrix[2,3] = vtk_matrix.GetElement(2, 3)
    numpy_matrix[3,3] = vtk_matrix.GetElement(3, 3)
    return numpy_matrix

  def decompose_matrix(self, matrix):
    _EPS=np.finfo(np.float64).eps;
    M = np.array(matrix, dtype=np.float64, copy=True).T
    if abs(M[3, 3]) < _EPS:
         raise ValueError("M[3, 3] is zero")
    M /= M[3, 3]
    P = M.copy()
    P[:, 3] = 0.0, 0.0, 0.0, 1.0
    if not np.linalg.det(P):
        raise ValueError("matrix is singular")
    scale = np.zeros((3, ))
    shear = [0.0, 0.0, 0.0]
    angles = [0.0, 0.0, 0.0]
    if any(abs(M[:3, 3]) > _EPS):
        perspective = np.dot(M[:, 3], np.linalg.inv(P.T))
        M[:, 3] = 0.0, 0.0, 0.0, 1.0
    else:
        perspective = np.array([0.0, 0.0, 0.0, 1.0])
    translate = M[3, :3].copy()
    M[3, :3] = 0.0
    row = M[:3, :3].copy()
    scale[0] = self.vector_norm(row[0])
    row[0] /= scale[0]
    shear[0] = np.dot(row[0], row[1])
    row[1] -= row[0] * shear[0]
    scale[1] = self.vector_norm(row[1])
    row[1] /= scale[1]
    shear[0] /= scale[1]
    shear[1] = np.dot(row[0], row[2])
    row[2] -= row[0] * shear[1]
    shear[2] = np.dot(row[1], row[2])
    row[2] -= row[1] * shear[2]
    scale[2] = self.vector_norm(row[2])
    row[2] /= scale[2]
    shear[1:] /= scale[2]
    if np.dot(row[0], np.cross(row[1], row[2])) < 0:
        np.negative(scale, scale)
        np.negative(row, row)
    angles[1] = math.asin(-row[0, 2])
    if math.cos(angles[1]):
        angles[0] = math.atan2(row[1, 2], row[2, 2])
        angles[2] = math.atan2(row[0, 1], row[0, 0])
    else:
        #angles[0] = math.atan2(row[1, 0], row[1, 1])
        angles[0] = math.atan2(-row[2, 1], row[1, 1])
        angles[2] = 0.0
    return scale, shear, angles, translate, perspective

  def vector_norm(self, data, axis=None, out=None):
    data = np.array(data, dtype=np.float64, copy=True)
    if out is None:
        if data.ndim == 1:
            return math.sqrt(np.dot(data, data))
        data *= data
        out = np.atleast_1d(np.sum(data, axis=axis))
        np.sqrt(out, out)
        return out
    else:
        data *= data
        np.sum(data, axis=axis, out=out)
        np.sqrt(out, out)

  def unit_vector(self, vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

  def angle_between(self, v1, v2):
    """ Returns the angle in degrees between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = self.unit_vector(v1)
    v2_u = self.unit_vector(v2)
    return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))


  # def fiducialRegistration(self, saveTransform, fixedLandmarks, movingLandmarks, transformType):
  #   logging.info("Fiducial registration starts")
  #   parameters = {}
  #   rms = 0
  #   parameters["fixedLandmarks"] = fixedLandmarks.GetID()
  #   parameters["movingLandmarks"] = movingLandmarks.GetID()
  #   parameters["saveTransform"] = saveTransform.GetID()
  #   parameters["rms"] = rms
  #   parameters["transformType"] = transformType
  #   fidReg = slicer.modules.fiducialregistration
  #   slicer.cli.run(fidReg, None, parameters)
  #   logging.info("Fiducial registration finished")
  #   return True

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
    # print 'Status: ' + status
    # print 'RMSE: ' + str_rms
    return float(str_rms)

  def recordSoftwareActivity(self, actionName, result):
    # Create directory
    path = self.DeliveryTrainingPath_record + '/' + self.userName
    if not os.path.exists(path):
      os.mkdir(path)

    # Store actionName
    self.recordedActivity_action.append(actionName)

    # Store timestamp
    self.recordedActivity_timeStamp.append(time.strftime("%Y-%m-%d_%H-%M-%S"))

    # Store result
    self.recordedActivity_result.append(result)

    self.saveTransform('ForcepsLToTracker', actionName, path)
    self.saveTransform('ForcepsRToTracker', actionName, path)
    self.saveTransform('MotherToTracker', actionName, path)
    self.saveTransform('BabyBodyToTracker', actionName, path)
    self.saveTransform('BabyHeadToTracker', actionName, path)


  def saveTransform(self, node_name, actionName, path):
    # Save transform
    node = slicer.util.getNode(node_name)
    if node:
      file_name = node_name + '_' + actionName + '_' + self.userName + '_' + time.strftime("_%Y-%m-%d_%H-%M-%S") + '.h5'
      self.saveData(node_name, path, file_name)
    else:
      print('ERROR: Unable to find ' + node_name)

  def saveSoftwareActivity(self):

    dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")
    csvFilePath = self.DeliveryTrainingPath_record + 'RecordedActivity_' + self.userName + '_' + dateAndTime + '.csv'
        
    with open(csvFilePath, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([ 'action', 'result', 'timestamp'])

        timestamp_array = np.array(self.recordedActivity_timeStamp) 
        action_array = np.array(self.recordedActivity_action)
        result_array = np.array(self.recordedActivity_result)
      
        for i in range(timestamp_array.shape[0]):
            vector = np.array([action_array[i], result_array[i], timestamp_array[i]]) 
            writer.writerow(vector) 

def drawPlane(m, V_norm):
  scene = slicer.mrmlScene
  #create a plane to cut,here it cuts in the XZ direction (xz normal=(1,0,0);XY =(0,0,1),YZ =(0,1,0)
  planex=vtk.vtkPlane()
  planex.SetOrigin(m[0],m[1],m[2])
  planex.SetNormal(V_norm[0],V_norm[1],V_norm[2])
  renderer = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow().GetRenderers().GetFirstRenderer()
  viewSize = renderer.ComputeVisiblePropBounds()
  planexSample = vtk.vtkSampleFunction()
  planexSample.SetImplicitFunction(planex)
  planexSample.SetModelBounds(viewSize)
  #planexSample.SetSampleDimensions(500,500,500)
  planexSample.ComputeNormalsOff()
  plane1 = vtk.vtkContourFilter()
  plane1.SetInputConnection(planexSample.GetOutputPort())
  # Create model Plane A node
  planeA = slicer.vtkMRMLModelNode()
  planeA.SetScene(scene)
  planeA.SetName("Symmetry Plane")
  planeA.SetAndObservePolyData(plane1.GetOutput())
  # Create display model Plane A node
  planeAModelDisplay = slicer.vtkMRMLModelDisplayNode()
  planeAModelDisplay.SetColor(1,0,0)
  planeAModelDisplay.BackfaceCullingOff()
  planeAModelDisplay.SetScene(scene)
  scene.AddNode(planeAModelDisplay)
  planeA.SetAndObserveDisplayNodeID(planeAModelDisplay.GetID())
  #Add to scene
  planeAModelDisplay.SetInputPolyDataConnection(plane1.GetOutputPort())
  scene.AddNode(planeA)
  # adjust center of 3d view to plane
  layoutManager = slicer.app.layoutManager()
  threeDWidget = layoutManager.threeDWidget(0)
  threeDView = threeDWidget.threeDView()
  threeDView.resetFocalPoint()

def distancePointToPlane(point,plane_mean,plane_normal):
  #m: point in plane
  #n: normal of plane
  v=np.subtract(point,plane_mean)
  num = np.abs(plane_normal[0]*v[0]+plane_normal[1]*v[1]+plane_normal[2]*v[2])
  denom = np.sqrt(np.square(plane_normal[0])+np.square(plane_normal[1])+np.square(plane_normal[2]))
  d = num/denom
  return d


class DeliveryTrainingNavigation_ModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_DeliveryTrainingNavigation_Module1()

  def test_DeliveryTrainingNavigation_Module1(self):
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
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = DeliveryTrainingNavigation_ModuleLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
