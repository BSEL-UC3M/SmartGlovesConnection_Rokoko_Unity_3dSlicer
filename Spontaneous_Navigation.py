from email import message
import os
import unittest
from unittest import result

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import math
import time
import csv


#import vtkSlicerRtCommonPython #SlicerRT must be installed
#
# Spontaneous_Navigation
#

class Spontaneous_Navigation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Spontaneous_Navigation"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["DeliveryTraining"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = [""]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#Spontaneous_Navigation">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

#
# Spontaneous_NavigationWidget
#

class Spontaneous_NavigationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    #VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = Spontaneous_NavigationLogic()
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    #Variables
    self.logic = Spontaneous_NavigationLogic()
    self.nonLoadedModels = 0
    self.connect = True
    self.browserName = ''
    self.recording = False
    self.firstTime = True
    self.observerTag = None
    self.retry_enabled = False
    self.callbackObserverTag = -1


    #Hide Slicer logo
    slicer.util.findChild(slicer.util.mainWindow(), "LogoLabel").visible = False

    #Error margin
    self.errorMargin = 5 # mm
    
    #Paths
    self.DeliveryTrainingSetupPath_models = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/'
    self.DeliveryTrainingSetupPath_realisticModels = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Models/RealSize/Realistic/'
    self.DeliveryTrainingSetupPath_data = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/RealSize/'
    self.DeliveryTrainingPath_record = slicer.modules.spontaneous_navigation.path.replace("Spontaneous_Navigation.py","") + 'Resources/Record/'
    self.DeliveryTrainingSetupPath_dataViews = slicer.modules.deliverytrainingsetup.path.replace("DeliveryTrainingSetup.py","") + 'Resources/Data/ViewPoints/'
    self.DeliveryTrainingNavigation_ModulePath_dataIcons = slicer.modules.deliverytrainingnavigation_module.path.replace("DeliveryTrainingNavigation_Module.py","") + 'Resources/Data/Icons/'
    self.DeliveryTrainingSpontaneousSetupPath_helpModels = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Models/Help/'
    self.DeliveryTrainingSpontaneousSetupPath_models = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Models/'
    self.DeliveryTrainingSpontaneousSetupPath_data = slicer.modules.deliverytrainingspontaneoussetup.path.replace("DeliveryTrainingSpontaneousSetup.py","") + 'Resources/Data/'

    # ICONS
    iconPlayPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'play.png')
    iconPausePath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'pause.png')
    iconRetryPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'retry.png')
    iconNextPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'next.png')
    iconHelpPath = os.path.join(self.DeliveryTrainingNavigation_ModulePath_dataIcons,'info.png')

    # Triple 3D layout
    self.layoutManager= slicer.app.layoutManager()
    layoutLogic = self.layoutManager.layoutLogic()
    customLayout = (
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

    # make SequenceBrowser Toolbar visible
    try:
      slicer.modules.sequences.setToolBarVisible(1) #4.11 version
    except:
      try:
        slicer.modules.sequencebrowser.setToolBarVisible(1) #4.10.2 version
      except:
        print('SequenceBrowser not found')
      pass



    ##LOAD
    self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
    self.loadCollapsibleButton.text = 'LOAD'
    self.layout.addWidget(self.loadCollapsibleButton)

    self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

    self.loadButtons = qt.QHBoxLayout()
    self.loadFormLayout.addRow(self.loadButtons)

    #load models and data
    self.loadDataButton = qt.QPushButton('Load Data')
    self.loadDataButton.enabled = True
    self.loadButtons.addWidget(self.loadDataButton)

    #Connect to plus
    self.connectToPlusButton = qt.QPushButton('Connect To Plus')
    self.connectToPlusButton.enabled = False
    self.loadButtons.addWidget(self.connectToPlusButton)

    #Apply transforms
    self.applyTransformsButton = qt.QPushButton('Apply Transforms')
    self.applyTransformsButton.enabled = False
    self.loadButtons.addWidget(self.applyTransformsButton)



    ##CONFIGURATION
    self.configurationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.configurationCollapsibleButton.text = 'CONFIGURATION'
    self.configurationCollapsibleButton.collapsed = False
    self.layout.addWidget(self.configurationCollapsibleButton)

    self.configurationFormLayout = qt.QFormLayout(self.configurationCollapsibleButton)

    #User name
    self.userNameLayout = qt.QHBoxLayout()
    self.configurationFormLayout.addRow(self.userNameLayout)
    self.userName_label = qt.QLabel('User Name: ')
    self.userName_textInput = qt.QLineEdit()
    self.userName_saveButton = qt.QPushButton('Save')
    self.userNameLayout.addWidget(self.userName_label)
    self.userNameLayout.addWidget(self.userName_textInput)
    self.userNameLayout.addWidget(self.userName_saveButton)

    #Right/left handed
    self.userHandLayout = qt.QHBoxLayout()
    self.configurationFormLayout.addRow(self.userHandLayout)
    self.rightHandedRadioButton = qt.QRadioButton('Right-handed')
    self.rightHandedRadioButton.checked = True
    self.userHandLayout.addWidget(self.rightHandedRadioButton)
    self.leftHandedRadioButton = qt.QRadioButton('Left-handed')
    self.leftHandedRadioButton.checked = False
    self.userHandLayout.addWidget(self.leftHandedRadioButton)

    #System's sensibility
    self.sensibilitySelection = qt.QHBoxLayout()
    self.configurationFormLayout.addRow(self.sensibilitySelection)
    self.sensibilityCheckBox = qt.QCheckBox('Decrease sensibility')
    self.sensibilityCheckBox.checkable = True
    self.sensibilityCheckBox.checked = False
    self.sensibilitySelection.addWidget(self.sensibilityCheckBox)



    ##VISUALIZATION
    self.visualizationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.visualizationCollapsibleButton.text = 'VISUALIZATION'
    self.visualizationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.visualizationCollapsibleButton)

    visualizationFormLayout = qt.QFormLayout(self.visualizationCollapsibleButton)

    #--Manikin
    self.visualizationManikinGroupBox = ctk.ctkCollapsibleGroupBox()
    self.visualizationManikinGroupBox.setTitle('Manikins')
    self.visualizationManikinGroupBox.collapsed = True
    visualizationFormLayout.addRow(self.visualizationManikinGroupBox)
    visualizationManikin_GroupBox_Layout = qt.QFormLayout(self.visualizationManikinGroupBox)

    #Belly visualization
    self.bellyViewSelection = qt.QHBoxLayout()
    visualizationManikin_GroupBox_Layout.addRow(self.bellyViewSelection)
    self.bellyViewLabel = qt.QLabel('Belly:')
    self.bellyViewSelection.addWidget(self.bellyViewLabel)
    #NEW TO MAKE THE RADIO BUTTONS MUTUALLY EXCLUSIVE
    self.bellyButtonGroup = qt.QButtonGroup()
    self.bellyButtonGroup.setExclusive(True)

    self.solidRadioButton_belly = qt.QRadioButton('Solid')
    self.solidRadioButton_belly.checked = False
    self.bellyViewSelection.addWidget(self.solidRadioButton_belly)
    self.bellyButtonGroup.addButton(self.solidRadioButton_belly)

    self.transparentRadioButton_belly = qt.QRadioButton('Transparent')
    self.transparentRadioButton_belly.checked = False
    self.bellyViewSelection.addWidget(self.transparentRadioButton_belly)
    self.bellyButtonGroup.addButton(self.transparentRadioButton_belly)

    self.invisibleRadioButton_belly = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_belly.checked = True
    self.bellyViewSelection.addWidget(self.invisibleRadioButton_belly)
    self.bellyButtonGroup.addButton(self.invisibleRadioButton_belly)

    #Mother visualization 
    self.motherViewSelection = qt.QHBoxLayout()
    visualizationManikin_GroupBox_Layout.addRow(self.motherViewSelection)
    self.motherViewLabel = qt.QLabel('Mother:')
    self.motherViewSelection.addWidget(self.motherViewLabel)
    #NEW
    self.motherButtonGroup = qt.QButtonGroup()
    self.motherButtonGroup.setExclusive(True)

    self.solidRadioButton_mother = qt.QRadioButton('Solid')
    self.solidRadioButton_mother.checked = False
    self.motherViewSelection.addWidget(self.solidRadioButton_mother)
    self.motherButtonGroup.addButton(self.solidRadioButton_mother)

    self.transparentRadioButton_mother = qt.QRadioButton('Transparent')
    self.transparentRadioButton_mother.checked = False
    self.motherViewSelection.addWidget(self.transparentRadioButton_mother)
    self.motherButtonGroup.addButton(self.transparentRadioButton_mother)

    self.invisibleRadioButton_mother = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_mother.checked = True
    self.motherViewSelection.addWidget(self.invisibleRadioButton_mother)
    self.motherButtonGroup.addButton(self.invisibleRadioButton_mother)

    #Baby visualization
    self.babyViewSelection = qt.QHBoxLayout()
    visualizationManikin_GroupBox_Layout.addRow(self.babyViewSelection)
    self.babyViewLabel = qt.QLabel('Baby:')
    self.babyViewSelection.addWidget(self.babyViewLabel)
    #NEW 
    self.babyButtonGroup = qt.QButtonGroup()
    self.babyButtonGroup.setExclusive(True)

    self.solidRadioButton_baby = qt.QRadioButton('Solid')
    self.solidRadioButton_baby.checked = True
    self.babyViewSelection.addWidget(self.solidRadioButton_baby)
    self.babyButtonGroup.addButton(self.solidRadioButton_baby)

    self.transparentRadioButton_baby = qt.QRadioButton('Transparent')
    self.transparentRadioButton_baby.checked = False
    self.babyViewSelection.addWidget(self.transparentRadioButton_baby)
    self.babyButtonGroup.addButton(self.transparentRadioButton_baby)

    self.invisibleRadioButton_baby = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_baby.checked = False
    self.babyViewSelection.addWidget(self.invisibleRadioButton_baby)
    self.babyButtonGroup.addButton(self.invisibleRadioButton_baby)


    #--Realistic
    self.visualizationRealistiGroupBox = ctk.ctkCollapsibleGroupBox()
    self.visualizationRealistiGroupBox.setTitle('Realistic')
    self.visualizationRealistiGroupBox.collapsed = True
    visualizationFormLayout.addRow(self.visualizationRealistiGroupBox)
    visualizationRealistic_GroupBox_Layout = qt.QFormLayout(self.visualizationRealistiGroupBox)

    #Mother real visualization
    self.motherRealViewSelection = qt.QHBoxLayout()
    visualizationRealistic_GroupBox_Layout.addRow(self.motherRealViewSelection)
    self.motherRealViewLabel = qt.QLabel('Mother:')
    self.motherRealViewSelection.addWidget(self.motherRealViewLabel)
    self.motherRealButtonGroup = qt.QButtonGroup()
    self.motherRealButtonGroup.setExclusive(True)

    self.solidRadioButton_motherReal = qt.QRadioButton('Solid')
    self.solidRadioButton_motherReal.checked = True
    self.motherRealViewSelection.addWidget(self.solidRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.solidRadioButton_motherReal)

    self.transparentRadioButton_motherReal = qt.QRadioButton('Transparent')
    self.transparentRadioButton_motherReal.checked = False
    self.motherRealViewSelection.addWidget(self.transparentRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.transparentRadioButton_motherReal)

    self.invisibleRadioButton_motherReal = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_motherReal.checked = False
    self.motherRealViewSelection.addWidget(self.invisibleRadioButton_motherReal)
    self.motherRealButtonGroup.addButton(self.invisibleRadioButton_motherReal)

    #Right pelvis visualization
    self.pelvisRightViewSelection = qt.QHBoxLayout()
    visualizationRealistic_GroupBox_Layout.addRow(self.pelvisRightViewSelection)
    self.pelvisRightViewLabel = qt.QLabel('Right Pelvis:')    
    self.pelvisRightViewSelection.addWidget(self.pelvisRightViewLabel)
    self.pelvisRightButtonGroup = qt.QButtonGroup()
    self.pelvisRightButtonGroup.setExclusive(True)

    self.solidRadioButton_pelvisRight = qt.QRadioButton('Solid')
    self.solidRadioButton_pelvisRight.checked = True
    self.pelvisRightViewSelection.addWidget(self.solidRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.solidRadioButton_pelvisRight)

    self.transparentRadioButton_pelvisRight = qt.QRadioButton('Transparent')
    self.transparentRadioButton_pelvisRight.checked = False
    self.pelvisRightViewSelection.addWidget(self.transparentRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.transparentRadioButton_pelvisRight)

    self.invisibleRadioButton_pelvisRight = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_pelvisRight.checked = False
    self.pelvisRightViewSelection.addWidget(self.invisibleRadioButton_pelvisRight)
    self.pelvisRightButtonGroup.addButton(self.invisibleRadioButton_pelvisRight)

    #Left pelvis visualization
    self.pelvisLeftViewSelection = qt.QHBoxLayout()
    visualizationRealistic_GroupBox_Layout.addRow(self.pelvisLeftViewSelection)
    self.pelvisLeftViewLabel = qt.QLabel('Left Pelvis:')    
    self.pelvisLeftViewSelection.addWidget(self.pelvisLeftViewLabel)
    self.pelvisLeftButtonGroup = qt.QButtonGroup()
    self.pelvisLeftButtonGroup.setExclusive(True)

    self.solidRadioButton_pelvisLeft = qt.QRadioButton('Solid')
    self.solidRadioButton_pelvisLeft.checked = True
    self.pelvisLeftViewSelection.addWidget(self.solidRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.solidRadioButton_pelvisLeft)

    self.transparentRadioButton_pelvisLeft = qt.QRadioButton('Transparent')
    self.transparentRadioButton_pelvisLeft.checked = False
    self.pelvisLeftViewSelection.addWidget(self.transparentRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.transparentRadioButton_pelvisLeft)

    self.invisibleRadioButton_pelvisLeft = qt.QRadioButton('Invisible')
    self.invisibleRadioButton_pelvisLeft.checked = False
    self.pelvisLeftViewSelection.addWidget(self.invisibleRadioButton_pelvisLeft)
    self.pelvisLeftButtonGroup.addButton(self.invisibleRadioButton_pelvisLeft)


    #Free/fixed view
    self.freeViewSelection = qt.QHBoxLayout()
    visualizationFormLayout.addRow(self.freeViewSelection)

    self.freeViewCheckBox = qt.QCheckBox('Free View')
    self.freeViewCheckBox.checkable = True
    self.freeViewCheckBox.checked = False
    self.freeViewSelection.addWidget(self.freeViewCheckBox)


    ### FETAL POSITION AND STATION ###
    self.fetalCollapsibleButton = ctk.ctkCollapsibleButton()
    self.fetalCollapsibleButton.text = 'Fetal Position and Station'
    self.fetalCollapsibleButton.setStyleSheet("font-size: 14px; font-weight: bold;")
    self.fetalCollapsibleButton.collapsed = True
    self.layout.addWidget(self.fetalCollapsibleButton)

    fetalFormLayout = qt.QFormLayout(self.fetalCollapsibleButton)
    
    #Position
    self.positionText = qt.QLabel('Select the correct fetal position:')
    self.positionText.setStyleSheet('font-size: 14px; font-weight: bold;')
    fetalFormLayout.addRow(self.positionText)

    self.positionSelectionLayout = qt.QHBoxLayout()
    fetalFormLayout.addRow(self.positionSelectionLayout)

    self.position1Selector = qt.QComboBox()
    self.position1Selector.addItems([' ','Direct', 'Right', 'Left'])
    self.position1Selector.setStyleSheet('font-size: 14px; font-weight: normal;')
    self.position1Selector.setView(qt.QListView()) #to avoid overlapping of items in the dropdown menu
    self.positionSelectionLayout.addWidget(self.position1Selector)

    self.occiputText = qt.QLabel('Occiput')
    self.occiputText.setStyleSheet('font-size: 14px; font-weight: normal;')
    self.positionSelectionLayout.addWidget(self.occiputText)


    self.position2Selector = qt.QComboBox()
    self.position2Selector.addItems([' ','Anterior', 'Posterior', 'Transverse'])
    self.position2Selector.setStyleSheet('font-size: 14px; font-weight: normal;')
    self.position2Selector.setView(qt.QListView()) #to avoid overlapping of items in the dropdown menu
    self.positionSelectionLayout.addWidget(self.position2Selector)


    self.positionResultHorizontalLayout = qt.QHBoxLayout()
    fetalFormLayout.addRow(self.positionResultHorizontalLayout)

    self.result_position_text = qt.QLabel('Result: ')
    self.result_position_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.positionResultHorizontalLayout.addWidget(self.result_position_text)

    self.result_position = qt.QLabel()
    self.result_position.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.positionResultHorizontalLayout.addWidget(self.result_position)

    #Help
    self.help_position = qt.QPushButton('Help')
    self.help_position.enabled = True
    self.help_position_icon = qt.QIcon(iconHelpPath)
    self.help_position.setIcon(self.help_position_icon)
    self.help_position.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.positionResultHorizontalLayout.addWidget(self.help_position)

    #Station
    self.stationText = qt.QLabel('Select the correct fetal station:')
    self.stationText.setStyleSheet('font-size: 14px; font-weight: bold;')
    fetalFormLayout.addRow(self.stationText)

    self.stationSelectionLayout = qt.QHBoxLayout()
    fetalFormLayout.addRow(self.stationSelectionLayout)

    self.stationSelector = qt.QComboBox()
    self.stationSelector.addItems([' ','-3', '-2', '-1', '0', '+1', '+2', '+3'])
    self.stationSelector.setStyleSheet('font-size: 14px; font-weight: normal;')
    self.stationSelector.setView(qt.QListView()) #to avoid overlapping of items in the dropdown menu
    self.stationSelectionLayout.addWidget(self.stationSelector)

    

    self.stationResultHorizontalLayout = qt.QHBoxLayout()
    fetalFormLayout.addRow(self.stationResultHorizontalLayout)

    self.result_station_text = qt.QLabel('Result: ')
    self.result_station_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.stationResultHorizontalLayout.addWidget(self.result_station_text)

    self.result_station = qt.QLabel()
    self.result_station.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.stationResultHorizontalLayout.addWidget(self.result_station)

    #Help
    self.help_station = qt.QPushButton('Help')
    self.help_station.enabled = True
    self.help_station_icon = qt.QIcon(iconHelpPath)
    self.help_station.setIcon(self.help_station_icon)
    self.help_station.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.stationResultHorizontalLayout.addWidget(self.help_station)

    # Show answers
    self.showAnswersButton = qt.QPushButton('Show Answers')
    self.showAnswersButton.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.showAnswersButton.enabled = False
    fetalFormLayout.addRow(self.showAnswersButton)

    # Save answers
    self.saveAnswerButton = qt.QPushButton('Save Answers')
    self.saveAnswerButton.setStyleSheet("font-size: 14px; font-weight: normal; background-color: blue")
    self.saveAnswerButton.enabled = True
    fetalFormLayout.addRow(self.saveAnswerButton)


    # #show station continuously
    # self.showStation = qt.QLabel('Station')
    # self.showStation.setStyleSheet('font-size: 24px; font-weight: bold; ')
    
    # fetalFormLayout.addRow(self.showStation)
    

    ### STEPS ###

    #---Step 1---#
    self.step1CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step1CollapsibleButton.text = 'STEP 1: Delivery of the head'
    self.step1CollapsibleButton.setStyleSheet("font-size: 14px; font-weight: bold;")
    self.step1CollapsibleButton.collapsed = True
    self.layout.addWidget(self.step1CollapsibleButton)

    step1FormLayout = qt.QFormLayout(self.step1CollapsibleButton)

    # CONTROL DEFLEXION
    self.deflexionGroupBox = ctk.ctkCollapsibleGroupBox()
    self.deflexionGroupBox.setTitle('Control deflexion')
    self.deflexionGroupBox.collapsed = True
    self.deflexionGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step1FormLayout.addRow(self.deflexionGroupBox)
    deflexionGroupBox_layout = qt.QFormLayout(self.deflexionGroupBox)

    self.step1Text = qt.QLabel('Place non-dominant hand on the fetal head to control deflexion')
    self.step1Text.setStyleSheet("font-size: 14px; font-weight: normal;")
    deflexionGroupBox_layout.addRow(self.step1Text)

    self.step1HorizontalLayout = qt.QHBoxLayout()
    deflexionGroupBox_layout.addRow(self.step1HorizontalLayout)

    #Check
    self.check_deflexion = qt.QPushButton('Check')
    self.check_deflexion.enabled = False
    self.check_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1HorizontalLayout.addWidget(self.check_deflexion)

    #Start 
    self.start_deflexion = qt.QPushButton('Start')
    self.start_deflexion.enabled = False
    self.start_deflexion_icon_play = qt.QIcon(iconPlayPath)
    self.start_deflexion_icon_pause = qt.QIcon(iconPausePath)
    self.start_deflexion.setIcon(self.start_deflexion_icon_play)
    self.start_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1HorizontalLayout.addWidget(self.start_deflexion)

    #Retry
    self.retry_deflexion = qt.QPushButton('Retry')
    self.retry_deflexion.enabled = False
    self.retry_deflexion_icon = qt.QIcon(iconRetryPath)
    self.retry_deflexion.setIcon(self.retry_deflexion_icon)
    self.retry_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1HorizontalLayout.addWidget(self.retry_deflexion)

    #Next
    self.next_deflexion = qt.QPushButton('Next')
    self.next_deflexion.enabled = False
    self.next_deflexion_icon = qt.QIcon(iconNextPath)
    self.next_deflexion.setIcon(self.next_deflexion_icon)
    self.next_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1HorizontalLayout.addWidget(self.next_deflexion)

    #Help
    self.help_deflexion = qt.QPushButton('Help')
    self.help_deflexion.enabled = False
    self.help_deflexion_icon = qt.QIcon(iconHelpPath)
    self.help_deflexion.setIcon(self.help_deflexion_icon)
    self.help_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1HorizontalLayout.addWidget(self.help_deflexion)
    
    # Result
    self.step1ResultHorizontalLayout = qt.QHBoxLayout()
    deflexionGroupBox_layout.addRow(self.step1ResultHorizontalLayout)

    self.result_deflexion_text = qt.QLabel('Result: ')
    self.result_deflexion_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1ResultHorizontalLayout.addWidget(self.result_deflexion_text)

    self.result_deflexion = qt.QLabel()
    self.result_deflexion.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step1ResultHorizontalLayout.addWidget(self.result_deflexion)


    # PROTECT PERINEUM
    self.protectGroupBox = ctk.ctkCollapsibleGroupBox()
    self.protectGroupBox.setTitle('Guard perineum')
    self.protectGroupBox.collapsed = True
    self.protectGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step1FormLayout.addRow(self.protectGroupBox)
    protectGroupBox_layout = qt.QFormLayout(self.protectGroupBox)

    self.protectText = qt.QLabel('Place dominant hand against the perineum')
    self.protectText.setStyleSheet("font-size: 14px; font-weight: normal;")
    protectGroupBox_layout.addRow(self.protectText)

    self.protectHorizontalLayout = qt.QHBoxLayout()
    protectGroupBox_layout.addRow(self.protectHorizontalLayout)

    #Check
    self.check_protect = qt.QPushButton('Check')
    self.check_protect.enabled = False
    self.check_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectHorizontalLayout.addWidget(self.check_protect)

    #Start 
    self.start_protect = qt.QPushButton('Start')
    self.start_protect.enabled = False
    self.start_protect_icon_play = qt.QIcon(iconPlayPath)
    self.start_protect_icon_pause = qt.QIcon(iconPausePath)
    self.start_protect.setIcon(self.start_protect_icon_play)
    self.start_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectHorizontalLayout.addWidget(self.start_protect)

    #Retry
    self.retry_protect = qt.QPushButton('Retry')
    self.retry_protect.enabled = False
    self.retry_protect_icon = qt.QIcon(iconRetryPath)
    self.retry_protect.setIcon(self.retry_protect_icon)
    self.retry_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectHorizontalLayout.addWidget(self.retry_protect)

    #Next
    self.next_protect = qt.QPushButton('Next')
    self.next_protect.enabled = False
    self.next_protect_icon = qt.QIcon(iconNextPath)
    self.next_protect.setIcon(self.next_protect_icon)
    self.next_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectHorizontalLayout.addWidget(self.next_protect)

    #Help
    self.help_protect = qt.QPushButton('Help')
    self.help_protect.enabled = False
    self.help_protect_icon = qt.QIcon(iconHelpPath)
    self.help_protect.setIcon(self.help_protect_icon)
    self.help_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectHorizontalLayout.addWidget(self.help_protect)
    
    # Result
    self.protectResultHorizontalLayout = qt.QHBoxLayout()
    protectGroupBox_layout.addRow(self.protectResultHorizontalLayout)

    self.result_protect_text = qt.QLabel('Result: ')
    self.result_protect_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectResultHorizontalLayout.addWidget(self.result_protect_text)

    self.result_protect = qt.QLabel()
    self.result_protect.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protectResultHorizontalLayout.addWidget(self.result_protect)




    #---Step 2---#
    self.step2CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step2CollapsibleButton.text = 'STEP 2: Delivery of the anterior shoulder'
    self.step2CollapsibleButton.setStyleSheet("font-size: 14px; font-weight: bold;")
    self.step2CollapsibleButton.collapsed = True
    self.layout.addWidget(self.step2CollapsibleButton)

    step2FormLayout = qt.QFormLayout(self.step2CollapsibleButton)

    # HOLD HEAD
    self.holdGroupBox = ctk.ctkCollapsibleGroupBox()
    self.holdGroupBox.setTitle('Hold head')
    self.holdGroupBox.collapsed = True
    self.holdGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step2FormLayout.addRow(self.holdGroupBox)
    holdGroupBox_layout = qt.QFormLayout(self.holdGroupBox)

    self.holdText = qt.QLabel('Use non-dominant hand to hold head')
    self.holdText.setStyleSheet("font-size: 14px; font-weight: normal;")
    holdGroupBox_layout.addRow(self.holdText)

    self.holdHorizontalLayout = qt.QHBoxLayout()
    holdGroupBox_layout.addRow(self.holdHorizontalLayout)

    #Check
    self.check_hold = qt.QPushButton('Check')
    self.check_hold.enabled = False
    self.check_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdHorizontalLayout.addWidget(self.check_hold)

    #Start 
    self.start_hold = qt.QPushButton('Start')
    self.start_hold.enabled = False
    self.start_hold_icon_play = qt.QIcon(iconPlayPath)
    self.start_hold_icon_pause = qt.QIcon(iconPausePath)
    self.start_hold.setIcon(self.start_hold_icon_play)
    self.start_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdHorizontalLayout.addWidget(self.start_hold)

    #Retry
    self.retry_hold = qt.QPushButton('Retry')
    self.retry_hold.enabled = False
    self.retry_hold_icon = qt.QIcon(iconRetryPath)
    self.retry_hold.setIcon(self.retry_hold_icon)
    self.retry_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdHorizontalLayout.addWidget(self.retry_hold)

    #Next
    self.next_hold = qt.QPushButton('Next')
    self.next_hold.enabled = False
    self.next_hold_icon = qt.QIcon(iconNextPath)
    self.next_hold.setIcon(self.next_hold_icon)
    self.next_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdHorizontalLayout.addWidget(self.next_hold)

    #Help
    self.help_hold = qt.QPushButton('Help')
    self.help_hold.enabled = False
    self.help_hold_icon = qt.QIcon(iconHelpPath)
    self.help_hold.setIcon(self.help_hold_icon)
    self.help_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdHorizontalLayout.addWidget(self.help_hold)
    
    # Result
    self.holdResultHorizontalLayout = qt.QHBoxLayout()
    holdGroupBox_layout.addRow(self.holdResultHorizontalLayout)

    self.result_hold_text = qt.QLabel('Result: ')
    self.result_hold_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdResultHorizontalLayout.addWidget(self.result_hold_text)

    self.result_hold = qt.QLabel()
    self.result_hold.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.holdResultHorizontalLayout.addWidget(self.result_hold)

    # # REMOVE HAND FROM PERINEUM -> incorporated in hold head step
    # self.removeGroupBox = ctk.ctkCollapsibleGroupBox()
    # self.removeGroupBox.setTitle('Remove hand')
    # self.removeGroupBox.collapsed = True
    # self.removeGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    # step2FormLayout.addRow(self.removeGroupBox)
    # removeGroupBox_layout = qt.QFormLayout(self.removeGroupBox)

    # self.step2Text = qt.QLabel('Remove hand from perineum')
    # self.step2Text.setStyleSheet("font-size: 14px; font-weight: normal;")
    # removeGroupBox_layout.addRow(self.step2Text)

    # self.step2HorizontalLayout = qt.QHBoxLayout()
    # removeGroupBox_layout.addRow(self.step2HorizontalLayout)

    # #Check
    # self.check_step2 = qt.QPushButton('Check')
    # self.check_step2.enabled = False
    # self.check_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2HorizontalLayout.addWidget(self.check_step2)

    # #Start 
    # self.start_step2 = qt.QPushButton('Start')
    # self.start_step2.enabled = False
    # self.start_step2_icon_play = qt.QIcon(iconPlayPath)
    # self.start_step2_icon_pause = qt.QIcon(iconPausePath)
    # self.start_step2.setIcon(self.start_step2_icon_play)
    # self.start_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2HorizontalLayout.addWidget(self.start_step2)

    # #Retry
    # self.retry_step2 = qt.QPushButton('Retry')
    # self.retry_step2.enabled = False
    # self.retry_step2_icon = qt.QIcon(iconRetryPath)
    # self.retry_step2.setIcon(self.retry_step2_icon)
    # self.retry_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2HorizontalLayout.addWidget(self.retry_step2)

    # #Next
    # self.next_step2 = qt.QPushButton('Next')
    # self.next_step2.enabled = False
    # self.next_step2_icon = qt.QIcon(iconNextPath)
    # self.next_step2.setIcon(self.next_step2_icon)
    # self.next_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2HorizontalLayout.addWidget(self.next_step2)

    # #Help
    # self.help_step2 = qt.QPushButton('Help')
    # self.help_step2.enabled = True
    # self.help_step2_icon = qt.QIcon(iconHelpPath)
    # self.help_step2.setIcon(self.help_step2_icon)
    # self.help_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2HorizontalLayout.addWidget(self.help_step2)

    # # Result
    # self.step2ResultHorizontalLayout = qt.QHBoxLayout()
    # removeGroupBox_layout.addRow(self.step2ResultHorizontalLayout)

    # self.result_step2_text = qt.QLabel('Result: ')
    # self.result_step2_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2ResultHorizontalLayout.addWidget(self.result_step2_text)

    # self.result_step2 = qt.QLabel()
    # self.result_step2.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step2ResultHorizontalLayout.addWidget(self.result_step2)


    # DESCENT VECTOR??
    self.descentGroupBox = ctk.ctkCollapsibleGroupBox()
    self.descentGroupBox.setTitle('Descent vector')
    self.descentGroupBox.collapsed = True
    self.descentGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step2FormLayout.addRow(self.descentGroupBox)
    descentGroupBox_layout = qt.QFormLayout(self.descentGroupBox)

    self.descentText = qt.QLabel('Apply gentle traction downwards and forwards')
    self.descentText.setStyleSheet("font-size: 14px; font-weight: normal;")
    descentGroupBox_layout.addRow(self.descentText)

    self.descentHorizontalLayout = qt.QHBoxLayout()
    descentGroupBox_layout.addRow(self.descentHorizontalLayout)

    # #Check
    # self.check_descent = qt.QPushButton('Check')
    # self.check_descent.enabled = False
    # self.check_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.descentHorizontalLayout.addWidget(self.check_descent)

    # #Start 
    # self.start_descent = qt.QPushButton('Start')
    # self.start_descent.enabled = False
    # self.start_descent_icon_play = qt.QIcon(iconPlayPath)
    # self.start_descent_icon_pause = qt.QIcon(iconPausePath)
    # self.start_descent.setIcon(self.start_descent_icon_play)
    # self.start_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.descentHorizontalLayout.addWidget(self.start_descent)

    # #Retry
    # self.retry_descent = qt.QPushButton('Retry')
    # self.retry_descent.enabled = False
    # self.retry_descent_icon = qt.QIcon(iconRetryPath)
    # self.retry_descent.setIcon(self.retry_descent_icon)
    # self.retry_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.descentHorizontalLayout.addWidget(self.retry_descent)

    #Next
    self.next_descent = qt.QPushButton('Next')
    self.next_descent.enabled = False
    self.next_descent_icon = qt.QIcon(iconNextPath)
    self.next_descent.setIcon(self.next_descent_icon)
    self.next_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.descentHorizontalLayout.addWidget(self.next_descent)

    #Help
    self.help_descent = qt.QPushButton('Help')
    self.help_descent.enabled = False
    self.help_descent_icon = qt.QIcon(iconHelpPath)
    self.help_descent.setIcon(self.help_descent_icon)
    self.help_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.descentHorizontalLayout.addWidget(self.help_descent)
    
    # # Result
    # self.descentResultHorizontalLayout = qt.QHBoxLayout()
    # descentGroupBox_layout.addRow(self.descentResultHorizontalLayout)

    # self.result_descent_text = qt.QLabel('Result: ')
    # self.result_descent_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.descentResultHorizontalLayout.addWidget(self.result_descent_text)

    # self.result_descent = qt.QLabel()
    # self.result_descent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.descentResultHorizontalLayout.addWidget(self.result_protect)

    #---Step 3---#
    self.step3CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step3CollapsibleButton.text = 'STEP 3: Delivery of the posterior shoulder'
    self.step3CollapsibleButton.setStyleSheet("font-size: 14px; font-weight: bold;")
    self.step3CollapsibleButton.collapsed = True
    self.layout.addWidget(self.step3CollapsibleButton)

    step3FormLayout = qt.QFormLayout(self.step3CollapsibleButton)

    # PROTECT PERINEUM 2
    self.protect2GroupBox = ctk.ctkCollapsibleGroupBox()
    self.protect2GroupBox.setTitle('Guard perineum')
    self.protect2GroupBox.collapsed = True
    self.protect2GroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step3FormLayout.addRow(self.protect2GroupBox)
    protect2GroupBox_layout = qt.QFormLayout(self.protect2GroupBox)

    self.protect2Text = qt.QLabel('Place dominant hand against the perineum')
    self.protect2Text.setStyleSheet("font-size: 14px; font-weight: normal;")
    protect2GroupBox_layout.addRow(self.protect2Text)

    self.protect2HorizontalLayout = qt.QHBoxLayout()
    protect2GroupBox_layout.addRow(self.protect2HorizontalLayout)

    #Check
    self.check_protect2 = qt.QPushButton('Check')
    self.check_protect2.enabled = False
    self.check_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2HorizontalLayout.addWidget(self.check_protect2)

    #Start 
    self.start_protect2 = qt.QPushButton('Start')
    self.start_protect2.enabled = False
    self.start_protect2_icon_play = qt.QIcon(iconPlayPath)
    self.start_protect2_icon_pause = qt.QIcon(iconPausePath)
    self.start_protect2.setIcon(self.start_protect2_icon_play)
    self.start_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2HorizontalLayout.addWidget(self.start_protect2)

    #Retry
    self.retry_protect2 = qt.QPushButton('Retry')
    self.retry_protect2.enabled = False
    self.retry_protect2_icon = qt.QIcon(iconRetryPath)
    self.retry_protect2.setIcon(self.retry_protect2_icon)
    self.retry_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2HorizontalLayout.addWidget(self.retry_protect2)

    #Next
    self.next_protect2 = qt.QPushButton('Next')
    self.next_protect2.enabled = False
    self.next_protect2_icon = qt.QIcon(iconNextPath)
    self.next_protect2.setIcon(self.next_protect2_icon)
    self.next_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2HorizontalLayout.addWidget(self.next_protect2)

    #Help
    self.help_protect2 = qt.QPushButton('Help')
    self.help_protect2.enabled = False
    self.help_protect2_icon = qt.QIcon(iconHelpPath)
    self.help_protect2.setIcon(self.help_protect2_icon)
    self.help_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2HorizontalLayout.addWidget(self.help_protect2)
    
    # Result
    self.protect2ResultHorizontalLayout = qt.QHBoxLayout()
    protect2GroupBox_layout.addRow(self.protect2ResultHorizontalLayout)

    self.result_protect2_text = qt.QLabel('Result: ')
    self.result_protect2_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2ResultHorizontalLayout.addWidget(self.result_protect2_text)

    self.result_protect2 = qt.QLabel()
    self.result_protect2.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.protect2ResultHorizontalLayout.addWidget(self.result_protect2)

    # ASCENT VECTOR??
    self.ascentGroupBox = ctk.ctkCollapsibleGroupBox()
    self.ascentGroupBox.setTitle('Ascent vector')
    self.ascentGroupBox.collapsed = True
    self.ascentGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step3FormLayout.addRow(self.ascentGroupBox)
    ascentGroupBox_layout = qt.QFormLayout(self.ascentGroupBox)

    self.ascentText = qt.QLabel('Apply gentle traction upwards')
    self.ascentText.setStyleSheet("font-size: 14px; font-weight: normal;")
    ascentGroupBox_layout.addRow(self.ascentText)

    self.step3HorizontalLayout = qt.QHBoxLayout()
    ascentGroupBox_layout.addRow(self.step3HorizontalLayout)

    # #Check
    # self.check_ascent = qt.QPushButton('Check')
    # self.check_ascent.enabled = False
    # self.check_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step3HorizontalLayout.addWidget(self.check_ascent)

    # #Start 
    # self.start_ascent = qt.QPushButton('Start')
    # self.start_ascent.enabled = False
    # self.start_ascent_icon_play = qt.QIcon(iconPlayPath)
    # self.start_ascent_icon_pause = qt.QIcon(iconPausePath)
    # self.start_ascent.setIcon(self.start_ascent_icon_play)
    # self.start_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step3HorizontalLayout.addWidget(self.start_ascent)

    # #Retry
    # self.retry_ascent = qt.QPushButton('Retry')
    # self.retry_ascent.enabled = False
    # self.retry_ascent_icon = qt.QIcon(iconRetryPath)
    # self.retry_ascent.setIcon(self.retry_ascent_icon)
    # self.retry_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step3HorizontalLayout.addWidget(self.retry_ascent)

    #Next
    self.next_ascent = qt.QPushButton('Next')
    self.next_ascent.enabled = False
    self.next_ascent_icon = qt.QIcon(iconNextPath)
    self.next_ascent.setIcon(self.next_ascent_icon)
    self.next_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step3HorizontalLayout.addWidget(self.next_ascent)

    #Help
    self.help_ascent = qt.QPushButton('Help')
    self.help_ascent.enabled = False
    self.help_ascent_icon = qt.QIcon(iconHelpPath)
    self.help_ascent.setIcon(self.help_ascent_icon)
    self.help_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step3HorizontalLayout.addWidget(self.help_ascent)

    # # Result
    # self.step3ResultHorizontalLayout = qt.QHBoxLayout()
    # ascentGroupBox_layout.addRow(self.step3ResultHorizontalLayout)

    # self.result_ascent_text = qt.QLabel('Result: ')
    # self.result_ascent_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step3ResultHorizontalLayout.addWidget(self.result_ascent_text)

    # self.result_ascent = qt.QLabel()
    # self.result_ascent.setStyleSheet("font-size: 14px; font-weight: normal;")
    # self.step3ResultHorizontalLayout.addWidget(self.result_ascent)



    #---Step 4---#
    self.step4CollapsibleButton = ctk.ctkCollapsibleButton()
    self.step4CollapsibleButton.text = 'STEP 4: Delivery of the body'
    self.step4CollapsibleButton.setStyleSheet("font-size: 14px; font-weight: bold;")
    self.step4CollapsibleButton.collapsed = True
    self.layout.addWidget(self.step4CollapsibleButton)

    step4FormLayout = qt.QFormLayout(self.step4CollapsibleButton)

    # GRAB BODY
    self.grabBodyGroupBox = ctk.ctkCollapsibleGroupBox()
    self.grabBodyGroupBox.setTitle('Grab the body')
    self.grabBodyGroupBox.collapsed = True
    self.grabBodyGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step4FormLayout.addRow(self.grabBodyGroupBox)
    grabBodyGroupBox_layout = qt.QFormLayout(self.grabBodyGroupBox)

    self.step4Text = qt.QLabel('Grab the fetal body with both hands')
    self.step4Text.setStyleSheet("font-size: 14px; font-weight: normal;")
    grabBodyGroupBox_layout.addRow(self.step4Text)

    self.step4HorizontalLayout = qt.QHBoxLayout()
    grabBodyGroupBox_layout.addRow(self.step4HorizontalLayout)

    #Check
    self.check_body = qt.QPushButton('Check')
    self.check_body.enabled = False
    self.check_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4HorizontalLayout.addWidget(self.check_body)

    #Start 
    self.start_body = qt.QPushButton('Start')
    self.start_body.enabled = False
    self.start_body_icon_play = qt.QIcon(iconPlayPath)
    self.start_body_icon_pause = qt.QIcon(iconPausePath)
    self.start_body.setIcon(self.start_body_icon_play)
    self.start_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4HorizontalLayout.addWidget(self.start_body)

    #Retry
    self.retry_body = qt.QPushButton('Retry')
    self.retry_body.enabled = False
    self.retry_body_icon = qt.QIcon(iconRetryPath)
    self.retry_body.setIcon(self.retry_body_icon)
    self.retry_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4HorizontalLayout.addWidget(self.retry_body)

    #Next
    self.next_body = qt.QPushButton('Next')
    self.next_body.enabled = False
    self.next_body_icon = qt.QIcon(iconNextPath)
    self.next_body.setIcon(self.next_body_icon)
    self.next_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4HorizontalLayout.addWidget(self.next_body)

    #Help
    self.help_body = qt.QPushButton('Help')
    self.help_body.enabled = False
    self.help_body_icon = qt.QIcon(iconHelpPath)
    self.help_body.setIcon(self.help_body_icon)
    self.help_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4HorizontalLayout.addWidget(self.help_body)

    # Result
    self.step4ResultHorizontalLayout = qt.QHBoxLayout()
    grabBodyGroupBox_layout.addRow(self.step4ResultHorizontalLayout)

    self.result_body_text = qt.QLabel('Result: ')
    self.result_body_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4ResultHorizontalLayout.addWidget(self.result_body_text)

    self.result_body = qt.QLabel()
    self.result_body.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.step4ResultHorizontalLayout.addWidget(self.result_body)

    # PLACE BABY ON TOP OF MOTHER
    self.placeOnMotherGroupBox = ctk.ctkCollapsibleGroupBox()
    self.placeOnMotherGroupBox.setTitle('Place the baby')
    self.placeOnMotherGroupBox.collapsed = True
    self.placeOnMotherGroupBox.setStyleSheet("font-size: 14px; font-weight: bold;")
    step4FormLayout.addRow(self.placeOnMotherGroupBox)
    placeOnMotherGroupBox_layout = qt.QFormLayout(self.placeOnMotherGroupBox)

    self.placeOnMotherText = qt.QLabel('Place baby on top of the mother')
    self.placeOnMotherText.setStyleSheet("font-size: 14px; font-weight: bold;")
    placeOnMotherGroupBox_layout.addRow(self.placeOnMotherText)

    self.placeOnMotherHorizontalLayout = qt.QHBoxLayout()
    placeOnMotherGroupBox_layout.addRow(self.placeOnMotherHorizontalLayout)

    # Check
    self.check_placeOnMother = qt.QPushButton('Check')
    self.check_placeOnMother.enabled = False
    self.check_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherHorizontalLayout.addWidget(self.check_placeOnMother)

    # Start
    self.start_placeOnMother = qt.QPushButton('Start')
    self.start_placeOnMother.enabled = False
    self.start_placeOnMother_icon_play = qt.QIcon(iconPlayPath)
    self.start_placeOnMother_icon_pause = qt.QIcon(iconPausePath)
    self.start_placeOnMother.setIcon(self.start_placeOnMother_icon_play)
    self.start_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherHorizontalLayout.addWidget(self.start_placeOnMother)

    # Retry
    self.retry_placeOnMother = qt.QPushButton('Retry')
    self.retry_placeOnMother.enabled = False
    self.retry_placeOnMother_icon = qt.QIcon(iconRetryPath)
    self.retry_placeOnMother.setIcon(self.retry_placeOnMother_icon)
    self.retry_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherHorizontalLayout.addWidget(self.retry_placeOnMother)

    # Next
    self.next_placeOnMother = qt.QPushButton('Next')
    self.next_placeOnMother.enabled = False
    self.next_placeOnMother_icon = qt.QIcon(iconNextPath)
    self.next_placeOnMother.setIcon(self.next_placeOnMother_icon)
    self.next_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherHorizontalLayout.addWidget(self.next_placeOnMother)

    # Help
    self.help_placeOnMother = qt.QPushButton('Help')
    self.help_placeOnMother.enabled = False
    self.help_placeOnMother_icon = qt.QIcon(iconHelpPath)
    self.help_placeOnMother.setIcon(self.help_placeOnMother_icon)
    self.help_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherHorizontalLayout.addWidget(self.help_placeOnMother)

    # Result
    self.placeOnMotherResultHorizontalLayout = qt.QHBoxLayout()
    placeOnMotherGroupBox_layout.addRow(self.placeOnMotherResultHorizontalLayout)

    self.result_placeOnMother_text = qt.QLabel('Result: ')
    self.result_placeOnMother_text.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherResultHorizontalLayout.addWidget(self.result_placeOnMother_text)

    self.result_placeOnMother = qt.QLabel()
    self.result_placeOnMother.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.placeOnMotherResultHorizontalLayout.addWidget(self.result_placeOnMother)



    #---SAVE---#
    self.saveDataCollapsibleButton = ctk.ctkCollapsibleButton()
    self.saveDataCollapsibleButton.text = 'SAVE DATA'
    self.saveDataCollapsibleButton.collapsed = False
    self.saveDataCollapsibleButton.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.layout.addWidget(self.saveDataCollapsibleButton)
    saveDataFormLayout = qt.QFormLayout(self.saveDataCollapsibleButton)
    self.saveDataButton = qt.QPushButton('Save')
    self.saveDataButton.setStyleSheet("font-size: 14px; font-weight: normal;")
    self.saveDataButton.enabled = True
    saveDataFormLayout.addRow(self.saveDataButton)
    self.resetButton = qt.QPushButton('Reset')
    self.resetButton.enabled = True
    saveDataFormLayout.addRow(self.resetButton)


    #CONNECTIONS
    self.loadDataButton.connect('clicked(bool)', self.onLoadDataButtonClicked)
    self.connectToPlusButton.connect('clicked(bool)', self.onConnectToPlusButtonClicked)
    self.applyTransformsButton.connect('clicked(bool)', self.onApplyTransformsButtonClicked)

    self.userName_saveButton.connect('clicked(bool)', self.onUserNameSaveButtonCLicked)
    self.sensibilityCheckBox.connect('clicked(bool)', self.onSensibilityCheckBoxClicked)
    self.rightHandedRadioButton.connect('clicked(bool)', self.onSelectHandClicked)
    self.leftHandedRadioButton.connect('clicked(bool)', self.onSelectHandClicked)

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
    self.solidRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.transparentRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.invisibleRadioButton_pelvisRight.connect('clicked(bool)', self.onSelectPelvisRightClicked)
    self.solidRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.transparentRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.invisibleRadioButton_pelvisLeft.connect('clicked(bool)', self.onSelectPelvisLeftClicked)
    self.freeViewCheckBox.connect('clicked(bool)', self.onFreeViewCheckBoxClicked)

    self.position1Selector.connect('currentIndexChanged(int)', self.onPositionSelectionClicked)
    self.position2Selector.connect('currentIndexChanged(int)', self.onPositionSelectionClicked)
    self.stationSelector.connect('currentIndexChanged(int)', self.onStationSelectionClicked)
    self.showAnswersButton.connect('clicked(bool)', self.onShowAnswersButtonClicked)
    self.saveAnswerButton.connect('clicked(bool)',self.onSaveAnswerButtonClicked)

    self.help_position.connect('clicked(bool)', self.onHelpPositionClicked)
    self.help_station.connect('clicked(bool)', self.onHelpStationClicked)

    self.check_deflexion.connect('clicked(bool)', self.onCheckDeflexionClicked)
    self.start_deflexion.connect('clicked(bool)', self.onStartDeflexionClicked)
    self.retry_deflexion.connect('clicked(bool)', self.onRetryDeflexionClicked)
    self.next_deflexion.connect('clicked(bool)', self.onNextDeflexionClicked)
    self.help_deflexion.connect('clicked(bool)', self.onHelpDeflexionClicked)

    self.check_protect.connect('clicked(bool)', self.onCheckProtectClicked)
    self.start_protect.connect('clicked(bool)', self.onStartProtectClicked)
    self.retry_protect.connect('clicked(bool)', self.onRetryProtectClicked)
    self.next_protect.connect('clicked(bool)', self.onNextProtectClicked)
    self.help_protect.connect('clicked(bool)', self.onHelpProtectClicked)
    
    self.check_hold.connect('clicked(bool)', self.onCheckHoldClicked)
    self.start_hold.connect('clicked(bool)', self.onStartHoldClicked)
    self.retry_hold.connect('clicked(bool)', self.onRetryHoldClicked)
    self.next_hold.connect('clicked(bool)', self.onNextHoldClicked)
    self.help_hold.connect('clicked(bool)', self.onHelpHoldClicked)

    # self.check_step2.connect('clicked(bool)', self.onCheckStep2Clicked)
    # self.start_step2.connect('clicked(bool)', self.onStartStep2Clicked)
    # self.retry_step2.connect('clicked(bool)', self.onRetryStep2Clicked)
    # self.next_step2.connect('clicked(bool)', self.onNextStep2Clicked)
    # self.help_step2.connect('clicked(bool)', self.onHelpStep2Clicked)

    # self.check_descent.connect('clicked(bool)', self.onCheckDescentClicked)
    # self.start_descent.connect('clicked(bool)', self.onStartDescentClicked)
    # self.retry_descent.connect('clicked(bool)', self.onRetryDescentClicked)
    self.next_descent.connect('clicked(bool)', self.onNextDescentClicked)
    self.help_descent.connect('clicked(bool)', self.onHelpDescentClicked)

    # self.check_ascent.connect('clicked(bool)', self.onCheckAscentClicked)
    # self.start_ascent.connect('clicked(bool)', self.onStartAscentClicked)
    # self.retry_ascent.connect('clicked(bool)', self.onRetryAscentClicked)
    self.next_ascent.connect('clicked(bool)', self.onNextAscentClicked)
    self.help_ascent.connect('clicked(bool)', self.onHelpAscentClicked)

    self.check_protect2.connect('clicked(bool)', self.onCheckProtect2Clicked)
    self.start_protect2.connect('clicked(bool)', self.onStartProtect2Clicked)
    self.retry_protect2.connect('clicked(bool)', self.onRetryProtect2Clicked)
    self.next_protect2.connect('clicked(bool)', self.onNextProtect2Clicked)
    self.help_protect2.connect('clicked(bool)', self.onHelpProtect2Clicked)

    self.check_body.connect('clicked(bool)', self.onCheckBodyClicked)
    self.start_body.connect('clicked(bool)', self.onStartBodyClicked)
    self.retry_body.connect('clicked(bool)', self.onRetryBodyClicked)
    self.next_body.connect('clicked(bool)', self.onNextBodyClicked)
    self.help_body.connect('clicked(bool)', self.onHelpBodyClicked)

    self.check_placeOnMother.connect('clicked(bool)', self.onCheckPlaceOnMotherClicked)
    self.start_placeOnMother.connect('clicked(bool)', self.onStartPlaceOnMotherClicked)
    self.retry_placeOnMother.connect('clicked(bool)', self.onRetryPlaceOnMotherClicked)
    self.next_placeOnMother.connect('clicked(bool)', self.onNextPlaceOnMotherClicked)
    self.help_placeOnMother.connect('clicked(bool)', self.onHelpPlaceOnMotherClicked)

    self.saveDataButton.connect('clicked(bool)', self.onSaveDataButtonClicked)
    self.resetButton.connect('clicked(bool)', self.onResetButtonClicked)


    self.layout.addStretch(1)





  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    pass



  def onLoadDataButtonClicked(self):
    logging.debug('Loading transforms')



    try:
      self.cameraTransform_front = slicer.util.getNode('FrontCameraToMother')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'FrontCameraToMother.h5')
        self.cameraTransform_front = slicer.util.getNode(pattern='FrontCameraToMother')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Front camera transform not found')



    try:
      self.cameraTransform_side = slicer.util.getNode('SideCameraMother')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'SideCameraToMother.h5')
        self.cameraTransform_side = slicer.util.getNode(pattern='SideCameraToMother')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Side camera transform not found')



    try:
      self.cameraTransform_up = slicer.util.getNode('UpCameraToMother')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSetupPath_dataViews + 'UpCameraToMother.h5')
        self.cameraTransform_up = slicer.util.getNode(pattern='UpCameraToMother')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Up camera tranform not found')



    try:
      self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'BabyHeadModelToBabyHead.h5')
        self.babyHeadModelToBabyHead = slicer.util.getNode('BabyHeadModelToBabyHead')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('BabyHeadModelToBabyHead transform not found')



    try:
      self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
    except:
      try: 
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'BabyBodyModelToBabyBody.h5')
        self.babyBodyModelToBabyBody = slicer.util.getNode('BabyBodyModelToBabyBody')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('BabyBodyModelToBabyBody transform not found')

    

    try:
      self.motherModelToMother = slicer.util.getNode('MotherModelToMother')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'MotherModelToMother.h5')
        self.motherModelToMother = slicer.util.getNode('MotherModelToMother')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('MotherModelToMother transform not found')


    try:
      self.handLModelToHandL = slicer.util.getNode('HandLModelToHandL')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'HandLModelToHandL.h5')
        self.handLModelToHandL = slicer.util.getNode('HandLModelToHandL')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLeftModelToHandLeft transform not found')


    try:
      self.handRModelToHandR = slicer.util.getNode('HandRModelToHandR')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'HandRModelToHandR.h5')
        self.handRModelToHandR = slicer.util.getNode('HandRModelToHandR')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRightModelToHandRight transform not found')



    try:
      self.thumbLModelToThumbL = slicer.util.getNode('ThumbLModelToThumbL')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'ThumbLModelToThumbL.h5')
        self.thumbLModelToThumbL = slicer.util.getNode('ThumbLModelToThumbL')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLeftModelToThumbLeft transform not found')



    try:
      self.thumbRModelToThumbR = slicer.util.getNode('ThumbRModelToThumbR')
    except:
      try:
        slicer.util.loadTransform(self.DeliveryTrainingSpontaneousSetupPath_data + 'ThumbRModelToThumbR.h5')
        self.thumbRModelToThumbR = slicer.util.getNode('ThumbRModelToThumbR')
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRightModelToThumbRight transform not found')



    logging.debug('Loading models')

    leftHandColor = np.divide(np.array([99.0,204.0,202.0]),255)
    rightHandColor = np.divide(np.array([214.0,64.0,69.0]),255)

    try:
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyBodyModel.stl')
        self.babyBodyModel = slicer.util.getNode(pattern='BabyBodyModel')
        self.babyBodyModelDisplay = self.babyBodyModel.GetModelDisplayNode()
        self.babyBodyModelDisplay.SetColor([1,0.68,0.62])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Baby Body model not found')



    try:
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'BabyHeadModel.stl')
        self.babyHeadModel = slicer.util.getNode(pattern='BabyHeadModel')
        self.babyHeadModelDisplay = self.babyHeadModel.GetModelDisplayNode()
        self.babyHeadModelDisplay.SetColor([1,0.68,0.62])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Baby Head model not found')

    

    try: 
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherModel.stl')
        self.motherModel = slicer.util.getNode(pattern='MotherModel')
        self.motherModelDisplay = self.motherModel.GetModelDisplayNode()
        self.motherModelDisplay.SetColor([1,0.68,0.62])
        #self.motherModel.GetDisplayNode().SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Mother model not found')



    try:
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_models + 'MotherTummyModel.stl')
        self.motherTummyModel = slicer.util.getNode(pattern='MotherTummyModel')
        self.motherTummyModelDisplay = self.motherTummyModel.GetModelDisplayNode()
        self.motherTummyModelDisplay.SetColor([1,0.68,0.62])
        #self.motherTummyModel.GetDisplayNode().SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Mother tummy model not found')



    try:
      self.rightPelvis1Model = slicer.util.getNode('rightPelvis1Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis1Model.stl')
        self.rightPelvis1Model = slicer.util.getNode(pattern='rightPelvis1Model')
        self.rightPelvis1ModelDisplay = self.rightPelvis1Model.GetModelDisplayNode()
        self.rightPelvis1ModelDisplay.SetColor(np.array([221,130,101])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right pelvis 1 model not found')



    try:
      self.rightPelvis2Model = slicer.util.getNode('rightPelvis2Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis2Model.stl')
        self.rightPelvis2Model = slicer.util.getNode(pattern='rightPelvis2Model')
        self.rightPelvis2ModelDisplay = self.rightPelvis2Model.GetModelDisplayNode()
        self.rightPelvis2ModelDisplay.SetColor(np.array([144,238,144])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right pelvis 2 model not found')



    try:
      self.rightPelvis3Model = slicer.util.getNode('rightPelvis3Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'rightPelvis3Model.stl')
        self.rightPelvis3Model = slicer.util.getNode(pattern='rightPelvis3Model')
        self.rightPelvis3ModelDisplay = self.rightPelvis3Model.GetModelDisplayNode()
        self.rightPelvis3ModelDisplay.SetColor(np.array([47,150,103])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right pelvis model not found')



    try:
      self.leftPelvis1Model = slicer.util.getNode('leftPelvis1Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis1Model.stl')
        self.leftPelvis1Model = slicer.util.getNode(pattern='leftPelvis1Model')
        self.leftPelvis1ModelDisplay = self.leftPelvis1Model.GetModelDisplayNode()
        self.leftPelvis1ModelDisplay.SetColor(np.array([85,188,255])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Left pelvis model not found')



    try:
      self.leftPelvis2Model = slicer.util.getNode('leftPelvis2Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis2Model.stl')
        self.leftPelvis2Model = slicer.util.getNode(pattern='leftPelvis2Model')
        self.leftPelvis2ModelDisplay = self.leftPelvis2Model.GetModelDisplayNode()
        self.leftPelvis2ModelDisplay.SetColor(np.array([253,135,192])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Left pelvis model not found')



    try:
      self.leftPelvis3Model = slicer.util.getNode('leftPelvis3Model')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'leftPelvis3Model.stl')
        self.leftPelvis3Model = slicer.util.getNode(pattern='leftPelvis3Model')
        self.leftPelvis3ModelDisplay = self.leftPelvis3Model.GetModelDisplayNode()
        self.leftPelvis3ModelDisplay.SetColor(np.array([47,150,103])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Left pelvis model not found')



    try:
      self.coxisRightModel = slicer.util.getNode('coxisRightModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'coxisRightModel.stl')
        self.coxisRightModel = slicer.util.getNode('coxisRightModel')
        self.coxisRightModelDisplay = self.coxisRightModel.GetModelDisplayNode()
        self.coxisRightModelDisplay.SetColor(np.array([255,255,220])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right coxis model not found')


    
    try:
      self.coxisLeftModel = slicer.util.getNode('coxisLeftModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'coxisLeftModel.stl')
        self.coxisLeftModel = slicer.util.getNode('coxisLeftModel')
        self.coxisLeftModelDisplay = self.coxisLeftModel.GetModelDisplayNode()
        self.coxisLeftModelDisplay.SetColor(np.array([255,255,220])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Left coxis model not found')



    try:
      self.middlePelvisModel = slicer.util.getNode('middlePelvisModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'middlePelvisModel.stl')
        self.middlePelvisModel = slicer.util.getNode(pattern='middlePelvisModel')
        self.middlePelvisModelDisplay = self.middlePelvisModel.GetModelDisplayNode()
        self.middlePelvisModelDisplay.SetColor(np.array([188,135,166])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Middle pelvis model not found')



    try:
      self.sacrumRightModel = slicer.util.getNode('sacrumRightModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'sacrumRightModel.stl')
        self.sacrumRightModel = slicer.util.getNode(pattern='sacrumRightModel')
        self.sacrumRightModelDisplay = self.sacrumRightModel.GetModelDisplayNode()
        self.sacrumRightModelDisplay.SetColor(np.array([255,255,220])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right sacrum model not found')



    try:
      self.sacrumLeftModel = slicer.util.getNode('sacrumLeftModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'sacrumLeftModel.stl')
        self.sacrumLeftModel = slicer.util.getNode(pattern='sacrumLeftModel')
        self.sacrumLeftModelDisplay = self.sacrumLeftModel.GetModelDisplayNode()
        self.sacrumLeftModelDisplay.SetColor(np.array([255,255,220])/255.0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Left sacrum model not found')



    try:
      self.motherRealisticModel = slicer.util.getNode('motherRealisticModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSetupPath_realisticModels + 'motherRealisticModel.stl')
        self.motherRealisticModel = slicer.util.getNode(pattern='motherRealisticModel')
        self.motherRealisticModelDisplay = self.motherRealisticModel.GetModelDisplayNode()
        self.motherRealisticModelDisplay.SetColor([1,0.68,0.62])
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Realistic mother model not found')



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
        print('Left hand model not found')


    
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
        print('Left thumb model not found')


    
    try:
      self.handRModel = slicer.util.getNode('HandRModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'HandRModel.vtk')
        self.handRModel = slicer.util.getNode(pattern="HandRModel")
        self.handRModelDisplay=self.handRModel.GetModelDisplayNode()
        self.handRModelDisplay.SetColor(rightHandColor)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right hand model not found')
      
        
    
    try:
      self.thumbRModel = slicer.util.getNode('ThumbRModel')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ThumbRModel.vtk')
        self.thumbRModel = slicer.util.getNode(pattern="ThumbRModel")
        self.thumbRModelDisplay=self.thumbRModel.GetModelDisplayNode()
        self.thumbRModelDisplay.SetColor(rightHandColor)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Right thumb model not found')


  

    #Load fiducials
    try:
      self.occiputFiducials = slicer.util.getNode('OcciputFiducials')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'OcciputFiducials.fcsv')
        self.occiputFiducials = slicer.util.getNode('OcciputFiducials')
        self.occiputFiducials.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Occiput Fiducials not found')

    
    try:
      self.checkFiducialsMother = slicer.util.getNode('CheckFiducialsMother')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'CheckFiducialsMother.fcsv')
        self.checkFiducialsMother = slicer.util.getNode('CheckFiducialsMother')
        self.checkFiducialsMother.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('CheckFiducialsMother not found')

      
    
    try:
      self.checkFiducialsHandL = slicer.util.getNode('CheckFiducialsHandL')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'CheckFiducialsHandL.fcsv')
        self.checkFiducialsHandL = slicer.util.getNode('CheckFiducialsHandL')
        self.checkFiducialsHandL.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('CheckFiducialsHandL not found')
    
    try:
      self.checkFiducialsHandR = slicer.util.getNode('CheckFiducialsHandR')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'CheckFiducialsHandR.fcsv')
        self.checkFiducialsHandR = slicer.util.getNode('CheckFiducialsHandR')
        self.checkFiducialsHandR.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('CheckFiducialsHandR not found')
    
    try:
      self.checkFiducialsThumbL = slicer.util.getNode('CheckFiducialsThumbL')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'CheckFiducialsThumbL.fcsv')
        self.checkFiducialsThumbL = slicer.util.getNode('CheckFiducialsThumbL')
        self.checkFiducialsThumbL.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('CheckFiducialsThumbL not found')

    

    try:
      self.checkFiducialsThumbR = slicer.util.getNode('CheckFiducialsThumbR')
    except:
      try:
        slicer.util.loadMarkupsFiducialList(self.DeliveryTrainingSpontaneousSetupPath_data + 'CheckFiducialsThumbR.fcsv')
        self.checkFiducialsThumbR = slicer.util.getNode('CheckFiducialsThumbR')
        self.checkFiducialsThumbR.SetDisplayVisibility(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('CheckFiducialsThumbR not found')

    # # Green - Yellow gradient
    # color_3 = np.divide([0.0, 127.0, 95.0], 255)
    # color_2 = np.divide([43.0, 147.0, 72.0], 255)
    # color_1 = np.divide([85.0, 166.0, 48.0], 255)
    # color0 = np.divide([128.0, 185.0, 24.0], 255)
    # color3 = np.divide([170.0, 204.0, 0.0], 255)
    # color2 = np.divide([191.0, 210.0, 0.0], 255)
    # color1 = np.divide([255.0, 255.0, 63.0], 255)

    # Green - Red gradient
    color_3 = np.divide([13.0, 50.0, 44.0], 255)
    color_2 = np.divide([30.0, 118.0, 98.0], 255)
    color_1 = np.divide([40.0, 183.0, 159.0], 255)
    color0 = np.divide([161.0, 220.0, 235.0], 255)
    color3 = np.divide([237.0, 25.0, 46.0], 255)
    color2 = np.divide([206.0, 22.0, 40.0], 255)
    color1 = np.divide([166.0, 17.0, 32.0], 255)

    # Load planes
    try:
      self.ischialPlane = slicer.util.getNode('IschialPlane')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane.vtk')
        self.ischialPlane = slicer.util.getNode('IschialPlane')
        self.ischialPlane.GetModelDisplayNode().SetColor(color0)
        self.ischialPlane.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane 0 not found')
    

    try:
      self.ischialPlane_1 = slicer.util.getNode('IschialPlane_1')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_1.vtk')
        self.ischialPlane_1 = slicer.util.getNode('IschialPlane_1')
        self.ischialPlane_1.GetModelDisplayNode().SetColor(color1)
        self.ischialPlane_1.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_1.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +1 not found')

    
    try:
      self.ischialPlane_minus1 = slicer.util.getNode('IschialPlane_-1')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-1.vtk')
        self.ischialPlane_minus1 = slicer.util.getNode('IschialPlane_-1')
        self.ischialPlane_minus1.GetModelDisplayNode().SetColor(color_1)
        self.ischialPlane_minus1.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus1.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -1 not found')

    
    try:
      self.ischialPlane_2 = slicer.util.getNode('IschialPlane_2')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_2.vtk')
        self.ischialPlane_2 = slicer.util.getNode('IschialPlane_2')
        self.ischialPlane_2.GetModelDisplayNode().SetColor(color2)
        self.ischialPlane_2.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_2.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +2 not found')
    

    try:
      self.ischialPlane_minus2 = slicer.util.getNode('IschialPlane_-2')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-2.vtk')
        self.ischialPlane_minus2 = slicer.util.getNode('IschialPlane_-2')
        self.ischialPlane_minus2.GetModelDisplayNode().SetColor(color_2)
        self.ischialPlane_minus2.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus2.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -2 not found')
    
    try:
      self.ischialPlane_3 = slicer.util.getNode('IschialPlane_3')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_3.vtk')
        self.ischialPlane_3 = slicer.util.getNode('IschialPlane_3')
        self.ischialPlane_3.GetModelDisplayNode().SetColor(color3)
        self.ischialPlane_3.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_3.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +3 not found')


    try:
      self.ischialPlane_minus3 = slicer.util.getNode('IschialPlane_-3')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-3.vtk')
        self.ischialPlane_minus3 = slicer.util.getNode('IschialPlane_-3')
        self.ischialPlane_minus3.GetModelDisplayNode().SetColor(color_3)
        self.ischialPlane_minus3.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus3.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -3 not found')



    try:
      self.ischialPlane_minusMiddle = slicer.util.getNode('IschialPlane_-middle')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-middle.vtk')
        self.ischialPlane_minusMiddle = slicer.util.getNode('IschialPlane_-middle')
        self.ischialPlane_minusMiddle.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_minusMiddle.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minusMiddle.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -middle not found')

    
    try:
      self.ischialPlane_middle = slicer.util.getNode('IschialPlane_middle')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_middle.vtk')
        self.ischialPlane_middle = slicer.util.getNode('IschialPlane_middle')
        self.ischialPlane_middle.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_middle.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_middle.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +middle not found')

    # Intermediate planes
    try:
      self.ischialPlane_05 = slicer.util.getNode('IschialPlane_05')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_05.vtk')
        self.ischialPlane_05 = slicer.util.getNode('IschialPlane_05')
        self.ischialPlane_05.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_05.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_05.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +0.5 not found')

    
    try:
      self.ischialPlane_minus05 = slicer.util.getNode('IschialPlane_-05')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-05.vtk')
        self.ischialPlane_minus05 = slicer.util.getNode('IschialPlane_-05')
        self.ischialPlane_minus05.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_minus05.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus05.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -0.5 not found')



    try:
      self.ischialPlane_15 = slicer.util.getNode('IschialPlane_15')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_15.vtk')
        self.ischialPlane_15 = slicer.util.getNode('IschialPlane_15')
        self.ischialPlane_15.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_15.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_15.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +1.5 not found')

    
    try:
      self.ischialPlane_minus15 = slicer.util.getNode('IschialPlane_-15')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-15.vtk')
        self.ischialPlane_minus15 = slicer.util.getNode('IschialPlane_-15')
        self.ischialPlane_minus15.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_minus15.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus15.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -1.5 not found')


    try:
      self.ischialPlane_25 = slicer.util.getNode('IschialPlane_25')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_25.vtk')
        self.ischialPlane_25 = slicer.util.getNode('IschialPlane_25')
        self.ischialPlane_25.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_25.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_25.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane +2.5 not found')

    
    try:
      self.ischialPlane_minus25 = slicer.util.getNode('IschialPlane_-25')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'IschialPlane_-25.vtk')
        self.ischialPlane_minus25 = slicer.util.getNode('IschialPlane_-25')
        self.ischialPlane_minus25.GetModelDisplayNode().SetColor(1,1,1)
        self.ischialPlane_minus25.GetModelDisplayNode().SetOpacity(0)
        self.ischialPlane_minus25.GetModelDisplayNode().BackfaceCullingOff()
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Ischial Plane -2.5 not found')


    # Help arrows
    try:
      self.arrow1 = slicer.util.getNode('Arrow1')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'Arrow1.stl')
        self.arrow1 = slicer.util.getNode(pattern="Arrow1")
        self.arrow1Display=self.arrow1.GetModelDisplayNode()
        self.arrow1Display.SetColor(1,0,0)
        self.arrow1Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Arrow1 model not found')

    
    try:
      self.arrow2 = slicer.util.getNode('Arrow2')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'Arrow2.stl')
        self.arrow2 = slicer.util.getNode(pattern="Arrow2")
        self.arrow2Display=self.arrow2.GetModelDisplayNode()
        self.arrow2Display.SetColor(1,0,0)
        self.arrow2Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Arrow2 model not found')

    
    try:
      self.arrow3 = slicer.util.getNode('Arrow3')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'Arrow3.stl')
        self.arrow3 = slicer.util.getNode(pattern="Arrow3")
        self.arrow3Display=self.arrow3.GetModelDisplayNode()
        self.arrow3Display.SetColor(1,0,0)
        self.arrow3Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Arrow3 model not found')


    try:
      self.arrow4 = slicer.util.getNode('Arrow4')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'Arrow4.stl')
        self.arrow4 = slicer.util.getNode(pattern="Arrow4")
        self.arrow4Display=self.arrow4.GetModelDisplayNode()
        self.arrow4Display.SetColor(1,0,0)
        self.arrow4Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('Arrow4 model not found')



    # Help down arrows
    try:
      self.arrowDown1 = slicer.util.getNode('ArrowDown1')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ArrowDown1.stl')
        self.arrowDown1 = slicer.util.getNode(pattern="ArrowDown1")
        self.arrowDown1Display=self.arrowDown1.GetModelDisplayNode()
        self.arrowDown1Display.SetColor(1,0,0)
        self.arrowDown1Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ArrowDown1 model not found')

    
    try:
      self.arrowDown2 = slicer.util.getNode('ArrowDown2')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ArrowDown2.stl')
        self.arrowDown2 = slicer.util.getNode(pattern="ArrowDown2")
        self.arrowDown2Display=self.arrowDown2.GetModelDisplayNode()
        self.arrowDown2Display.SetColor(1,0,0)
        self.arrowDown2Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ArrowDown2 model not found')

    
    try:
      self.arrowDown3 = slicer.util.getNode('ArrowDown3')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ArrowDown3.stl')
        self.arrowDown3 = slicer.util.getNode(pattern="ArrowDown3")
        self.arrowDown3Display=self.arrowDown3.GetModelDisplayNode()
        self.arrowDown3Display.SetColor(1,0,0)
        self.arrowDown3Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ArrowDown3 model not found')


    try:
      self.arrowDown4 = slicer.util.getNode('ArrowDown4')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_models + 'ArrowDown4.stl')
        self.arrowDown4 = slicer.util.getNode(pattern="ArrowDown4")
        self.arrowDown4Display=self.arrowDown4.GetModelDisplayNode()
        self.arrowDown4Display.SetColor(1,0,0)
        self.arrowDown4Display.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ArrowDown4 model not found')

    
    # HELP MODELS
    try:
      self.handLModelHoldHelpL = slicer.util.getNode('HandLModelHoldHelpL')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelHoldHelpL.stl')
        self.handLModelHoldHelpL = slicer.util.getNode('HandLModelHoldHelpL')
        self.handLModelHoldHelpLDisplay = self.handLModelHoldHelpL.GetModelDisplayNode()
        self.handLModelHoldHelpLDisplay.SetColor(leftHandColor)
        self.handLModelHoldHelpLDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLModelHoldHelpL not found')

    try:
      self.thumbLModelHoldHelpL = slicer.util.getNode('ThumbLModelHoldHelpL')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelHoldHelpL.stl')
        self.thumbLModelHoldHelpL = slicer.util.getNode('ThumbLModelHoldHelpL')
        self.thumbLModelHoldHelpLDisplay = self.thumbLModelHoldHelpL.GetModelDisplayNode()
        self.thumbLModelHoldHelpLDisplay.SetColor(leftHandColor)
        self.thumbLModelHoldHelpLDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelHoldHelpL not found')

    
    try:
      self.handLModelHoldHelpR = slicer.util.getNode('HandLModelHoldHelpR')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelHoldHelpR.stl')
        self.handLModelHoldHelpR = slicer.util.getNode('HandLModelHoldHelpR')
        self.handLModelHoldHelpRDisplay = self.handLModelHoldHelpR.GetModelDisplayNode()
        self.handLModelHoldHelpRDisplay.SetColor(leftHandColor)
        self.handLModelHoldHelpRDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLModelHoldHelpR not found')

    try:
      self.thumbLModelHoldHelpR = slicer.util.getNode('ThumbLModelHoldHelpR')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelHoldHelpR.stl')
        self.thumbLModelHoldHelpR = slicer.util.getNode('ThumbLModelHoldHelpR')
        self.thumbLModelHoldHelpRDisplay = self.thumbLModelHoldHelpR.GetModelDisplayNode()
        self.thumbLModelHoldHelpRDisplay.SetColor(leftHandColor)
        self.thumbLModelHoldHelpRDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelHoldHelpR not found')

    
    try:
      self.handRModelGuardHelp = slicer.util.getNode('HandRModelGuardHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelGuardHelp.stl')
        self.handRModelGuardHelp = slicer.util.getNode('HandRModelGuardHelp')
        self.handRModelGuardHelpDisplay = self.handRModelGuardHelp.GetModelDisplayNode()
        self.handRModelGuardHelpDisplay.SetColor(rightHandColor)
        self.handRModelGuardHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelGuardHelp not found')

    try:
      self.thumbRModelGuardHelp = slicer.util.getNode('ThumbRModelGuardHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelGuardHelp.stl')
        self.thumbRModelGuardHelp = slicer.util.getNode('ThumbRModelGuardHelp')
        self.thumbRModelGuardHelpDisplay = self.thumbRModelGuardHelp.GetModelDisplayNode()
        self.thumbRModelGuardHelpDisplay.SetColor(rightHandColor)
        self.thumbRModelGuardHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelGuardHelp not found')

    
    try:
      self.handLModelDeflexionHelp = slicer.util.getNode('HandLModelDeflexionHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelDeflexionHelp.stl')
        self.handLModelDeflexionHelp = slicer.util.getNode('HandLModelDeflexionHelp')
        self.handLModelDeflexionHelpDisplay = self.handLModelDeflexionHelp.GetModelDisplayNode()
        self.handLModelDeflexionHelpDisplay.SetColor(leftHandColor)
        self.handLModelDeflexionHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLModelDeflexionHelp not found')

    try:
      self.thumbLModelDeflexionHelp = slicer.util.getNode('ThumbLModelDeflexionHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelDeflexionHelp.stl')
        self.thumbLModelDeflexionHelp = slicer.util.getNode('ThumbLModelDeflexionHelp')
        self.thumbLModelDeflexionHelpDisplay = self.thumbLModelDeflexionHelp.GetModelDisplayNode()
        self.thumbLModelDeflexionHelpDisplay.SetColor(leftHandColor)
        self.thumbLModelDeflexionHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelDeflexionHelp not found')


    
    try:
      self.handLModelGrabHelp = slicer.util.getNode('HandLModelGrabHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelGrabHelp.stl')
        self.handLModelGrabHelp = slicer.util.getNode('HandLModelGrabHelp')
        self.handLModelGrabHelpDisplay = self.handLModelGrabHelp.GetModelDisplayNode()
        self.handLModelGrabHelpDisplay.SetColor(leftHandColor)
        self.handLModelGrabHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLModelGrabHelp not found')

    try:
      self.thumbLModelGrabHelp = slicer.util.getNode('ThumbLModelGrabHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelGrabHelp.stl')
        self.thumbLModelGrabHelp = slicer.util.getNode('ThumbLModelGrabHelp')
        self.thumbLModelGrabHelpDisplay = self.thumbLModelGrabHelp.GetModelDisplayNode()
        self.thumbLModelGrabHelpDisplay.SetColor(leftHandColor)
        self.thumbLModelGrabHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelGrabHelp not found')

    
    try:
      self.handRModelGrabHelp = slicer.util.getNode('HandRModelGrabHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelGrabHelp.stl')
        self.handRModelGrabHelp = slicer.util.getNode('HandRModelGrabHelp')
        self.handRModelGrabHelpDisplay = self.handRModelGrabHelp.GetModelDisplayNode()
        self.handRModelGrabHelpDisplay.SetColor(rightHandColor)
        self.handRModelGrabHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelGrabHelp not found')

    try:
      self.thumbRModelGrabHelp = slicer.util.getNode('ThumbRModelGrabHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelGrabHelp.stl')
        self.thumbRModelGrabHelp = slicer.util.getNode('ThumbRModelGrabHelp')
        self.thumbRModelGrabHelpDisplay = self.thumbRModelGrabHelp.GetModelDisplayNode()
        self.thumbRModelGrabHelpDisplay.SetColor(rightHandColor)
        self.thumbRModelGrabHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelGrabHelp not found')

    
    # Help for left-handed
    try:
      self.handLModelGuardHelp = slicer.util.getNode('HandLModelGuardHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelGuardHelp.stl')
        self.handLModelGuardHelp = slicer.util.getNode('HandLModelGuardHelp')
        self.handLModelGuardHelpDisplay = self.handLModelGuardHelp.GetModelDisplayNode()
        self.handLModelGuardHelpDisplay.SetColor(leftHandColor)
        self.handLModelGuardHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandLModelGuardHelp not found')

    try:
      self.thumbLModelGuardHelp = slicer.util.getNode('ThumbLModelGuardHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelGuardHelp.stl')
        self.thumbLModelGuardHelp = slicer.util.getNode('ThumbLModelGuardHelp')
        self.thumbLModelGuardHelpDisplay = self.thumbLModelGuardHelp.GetModelDisplayNode()
        self.thumbLModelGuardHelpDisplay.SetColor(leftHandColor)
        self.thumbLModelGuardHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelGuardHelp not found')

    
    try:
      self.handRModelHoldHelpL = slicer.util.getNode('HandRModelHoldHelpL')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelHoldHelpL.stl')
        self.handRModelHoldHelpL = slicer.util.getNode('HandRModelHoldHelpL')
        self.handRModelHoldHelpLDisplay = self.handRModelHoldHelpL.GetModelDisplayNode()
        self.handRModelHoldHelpLDisplay.SetColor(rightHandColor)
        self.handRModelHoldHelpLDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelHoldHelpL not found')

    try:
      self.thumbRModelHoldHelpL = slicer.util.getNode('ThumbRModelHoldHelpL')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelHoldHelpL.stl')
        self.thumbRModelHoldHelpL = slicer.util.getNode('ThumbRModelHoldHelpL')
        self.thumbRModelHoldHelpLDisplay = self.thumbRModelHoldHelpL.GetModelDisplayNode()
        self.thumbRModelHoldHelpLDisplay.SetColor(rightHandColor)
        self.thumbRModelHoldHelpLDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelHoldHelpL not found')

    
    try:
      self.handRModelHoldHelpR = slicer.util.getNode('HandRModelHoldHelpR')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelHoldHelpR.stl')
        self.handRModelHoldHelpR = slicer.util.getNode('HandRModelHoldHelpR')
        self.handRModelHoldHelpRDisplay = self.handRModelHoldHelpR.GetModelDisplayNode()
        self.handRModelHoldHelpRDisplay.SetColor(rightHandColor)
        self.handRModelHoldHelpRDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelHoldHelpR not found')

    try:
      self.thumbRModelHoldHelpR = slicer.util.getNode('ThumbRModelHoldHelpR')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelHoldHelpR.stl')
        self.thumbRModelHoldHelpR = slicer.util.getNode('ThumbRModelHoldHelpR')
        self.thumbRModelHoldHelpRDisplay = self.thumbRModelHoldHelpR.GetModelDisplayNode()
        self.thumbRModelHoldHelpRDisplay.SetColor(rightHandColor)
        self.thumbRModelHoldHelpRDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelHoldHelpR not found')


    
    try:
      self.handRModelDeflexionHelp = slicer.util.getNode('HandRModelDeflexionHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelDeflexionHelp.stl')
        self.handRModelDeflexionHelp = slicer.util.getNode('HandRModelDeflexionHelp')
        self.handRModelDeflexionHelpDisplay = self.handRModelDeflexionHelp.GetModelDisplayNode()
        self.handRModelDeflexionHelpDisplay.SetColor(rightHandColor)
        self.handRModelDeflexionHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelDeflexionHelp not found')

    try:
      self.thumbRModelDeflexionHelp = slicer.util.getNode('ThumbRModelDeflexionHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelDeflexionHelp.stl')
        self.thumbRModelDeflexionHelp = slicer.util.getNode('ThumbRModelDeflexionHelp')
        self.thumbRModelDeflexionHelpDisplay = self.thumbRModelDeflexionHelp.GetModelDisplayNode()
        self.thumbRModelDeflexionHelpDisplay.SetColor(rightHandColor)
        self.thumbRModelDeflexionHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelDeflexionHelp not found')

    try:
      self.thumbRModelPlaceHelp = slicer.util.getNode('ThumbRModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbRModelPlaceHelp.stl')
        self.thumbRModelPlaceHelp = slicer.util.getNode('ThumbRModelPlaceHelp')
        self.thumbRModelPlaceHelpDisplay = self.thumbRModelPlaceHelp.GetModelDisplayNode()
        self.thumbRModelPlaceHelpDisplay.SetColor(rightHandColor)
        self.thumbRModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbRModelPlaceHelp not found')

    
    try:
      self.thumbLModelPlaceHelp = slicer.util.getNode('ThumbLModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'ThumbLModelPlaceHelp.stl')
        self.thumbLModelPlaceHelp = slicer.util.getNode('ThumbLModelPlaceHelp')
        self.thumbLModelPlaceHelpDisplay = self.thumbLModelPlaceHelp.GetModelDisplayNode()
        self.thumbLModelPlaceHelpDisplay.SetColor(leftHandColor)
        self.thumbLModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelPlaceHelp not found')



    try:
      self.handRModelPlaceHelp = slicer.util.getNode('HandRModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandRModelPlaceHelp.stl')
        self.handRModelPlaceHelp = slicer.util.getNode('HandRModelPlaceHelp')
        self.handRModelPlaceHelpDisplay = self.handRModelPlaceHelp.GetModelDisplayNode()
        self.handRModelPlaceHelpDisplay.SetColor(rightHandColor)
        self.handRModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('HandRModelPlaceHelp not found')

    
    try:
      self.handLModelPlaceHelp = slicer.util.getNode('HandLModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'HandLModelPlaceHelp.stl')
        self.handLModelPlaceHelp = slicer.util.getNode('HandLModelPlaceHelp')
        self.handLModelPlaceHelpDisplay = self.handLModelPlaceHelp.GetModelDisplayNode()
        self.handLModelPlaceHelpDisplay.SetColor(leftHandColor)
        self.handLModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('ThumbLModelPlaceHelp not found')




    try:
        self.babyBodyModelPlaceHelp = slicer.util.getNode('BabyBodyModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'BabyBodyModelPlaceHelp.stl')
        self.babyBodyModelPlaceHelp = slicer.util.getNode(pattern='BabyBodyModelPlaceHelp')
        self.babyBodyModelPlaceHelpDisplay = self.babyBodyModelPlaceHelp.GetModelDisplayNode()
        self.babyBodyModelPlaceHelpDisplay.SetColor([1,0.68,0.62])
        self.babyBodyModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('BabyBodyModelPlaceHelp not found')



    try:
      self.babyHeadModelPlaceHelp = slicer.util.getNode('BabyHeadModelPlaceHelp')
    except:
      try:
        slicer.util.loadModel(self.DeliveryTrainingSpontaneousSetupPath_helpModels + 'BabyHeadModelPlaceHelp.stl')
        self.babyHeadModelPlaceHelp = slicer.util.getNode(pattern='BabyHeadModelPlaceHelp')
        self.babyHeadModelPlaceHelpDisplay = self.babyHeadModelPlaceHelp.GetModelDisplayNode()
        self.babyHeadModelPlaceHelpDisplay.SetColor([1,0.68,0.62])
        self.babyHeadModelPlaceHelpDisplay.SetOpacity(0)
      except:
        self.nonLoadedModels = self.nonLoadedModels + 1
        print('BabyHeadModelPlaceHelp not found')
    

    # Create baby plane
    origin = [0]*4
    self.occiputFiducials.GetNthFiducialWorldCoordinates(0,origin)
    p2 = [0]*4
    self.occiputFiducials.GetNthFiducialWorldCoordinates(1,p2)
    p3 = [0]*4
    self.occiputFiducials.GetNthFiducialWorldCoordinates(2,p3)
    self.logic.drawPlane(origin,self.logic.findPlaneNormal(origin,p2,p3),'Baby','BabyHead',50) #draw baby plane passing through occiput
    self.babyPlane = slicer.mrmlScene.GetFirstNodeByName('BabyPlane')
    self.babyPlane.GetModelDisplayNode().SetOpacity(0)
    self.babyPlane.GetModelDisplayNode().SetColor([0, 0, 1])



    redSlice = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
    redSlice.SetSliceVisible(False)

    if self.nonLoadedModels > 0:
      print("Non loaded models: " + str(self.nonLoadedModels))
    else:
      self.loadDataButton.enabled = False
      self.connectToPlusButton.enabled = True

    self.setupViews()

    #TO MAKE INVISIBLE SOME MODELS
    try:
      self.motherModel = slicer.util.getNode('MotherModel')
      self.motherModel.GetDisplayNode().SetOpacity(0)
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
      self.motherTummyModel.GetDisplayNode().SetOpacity(0)
    except:
      print('Unable to change opacity of models')



  def setupViews(self):
    import Viewpoint
    viewpointLogic = Viewpoint.ViewpointLogic()

    cameraTransform_front = slicer.util.getNode('FrontCameraToMother')
    cameraTransform_side = slicer.util.getNode('SideCameraToMother')
    cameraTransform_up = slicer.util.getNode('UpCameraToMother')

    viewName1 = 'View1'
    viewName2 = 'View2'

    viewNode1 = slicer.util.getNode(viewName1)
    viewNode2 = slicer.util.getNode(viewName2)

    viewNode1.SetBoxVisible(False)
    viewNode1.SetAxisLabelsVisible(False)
    viewNode2.SetBoxVisible(False)
    viewNode2.SetAxisLabelsVisible(False)

    viewpointLogic.getViewpointForViewNode(viewNode1).setViewNode(viewNode1)
    viewpointLogic.getViewpointForViewNode(viewNode2).setViewNode(viewNode2)

    viewpointLogic.getViewpointForViewNode(viewNode1).bullseyeSetTransformNode(cameraTransform_front)
    viewpointLogic.getViewpointForViewNode(viewNode2).bullseyeSetTransformNode(cameraTransform_side)

    viewpointLogic.getViewpointForViewNode(viewNode1).bullseyeStart()
    viewpointLogic.getViewpointForViewNode(viewNode2).bullseyeStart()


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
    logging.debug('Connecting to plus')

    if self.connect:
      try: 
        cnode = slicer.util.getNode('IGTLConnector')
      except:
        cnode = slicer.vtkMRMLIGTLConnectorNode()
        slicer.mrmlScene.AddNode(cnode)
        cnode.SetName('IGTLConnector')
      correct = cnode.SetTypeClient('localhost',18944)

      if correct == 1:
        cnode.Start()
        logging.debug('Successful connection')
        self.connect = False
        self.connectToPlusButton.setText('Disconnect from Plus')
        self.applyTransformsButton.enabled = True
      else:
        print('Unable to connect to Plus')
        logging.debug('Unable to connect to Plus')
    else:
      cnode = slicer.util.getNode('IGTLConnector')
      cnode.Stop()
      self.connect = True
      self.connectToPlusButton.setText('Connect to Plus')



  def onApplyTransformsButtonClicked(self):
    logging.debug('Loding transforms to apply them')

    nonLoadedTransforms = 0

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

    # try:
    #   self.handLToTracker = slicer.util.getNode('HandLToTracker')
    # except:
    #   print('Unable to receive HandLToTracker transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1
    # else:
    #   if self.firstTime:
    #     # self.addWatchdog(self.handLToTracker, warningMessage='HandL is out of view', playSound=True)
    #     self.addWatchedNode(wd, self.handLToTracker, warningMessage = 'HandL is out of view', playSound = True)


    # try:
    #   self.thumbLToTracker = slicer.util.getNode('ThumbLToTracker')
    # except:
    #   print('Unable to receive ThumbLToTracker transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1 
    # else:
    #   if self.firstTime:
    #     # self.addWatchdog(self.thumbLToTracker, warningMessage='ThumbL is out of view', playSound=True)
    #     self.addWatchedNode(wd, self.thumbLToTracker, warningMessage = 'ThumbL is out of view', playSound = True)

    # try:
    #   self.handRToTracker = slicer.util.getNode('HandRToTracker')
    # except:
    #   print('Unable to receive HandRToTracker transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1
    # else:
    #   if self.firstTime:
    #     # self.addWatchdog(self.handRToTracker, warningMessage='HandR is out of view', playSound=True)
    #     self.addWatchedNode(wd, self.handRToTracker, warningMessage = 'HandR is out of view', playSound = True)


    # try:
    #   self.thumbRToTracker = slicer.util.getNode('ThumbRToTracker')
    # except:
    #   print('Unable to receive HandRToTracker transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1
    # else:
    #   if self.firstTime:
    #     # self.addWatchdog(self.thumbRToTracker, warningMessage='ThumbR out of view', playSound=True)
    #     self.addWatchedNode(wd, self.thumbRToTracker, warningMessage = 'ThumbR is out of view', playSound = True)


    try:
      self.motherToTracker = slicer.util.getNode('MotherToTracker')
    except:
      print('Unable to receive MotherToTracker transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # self.addWatchdog(self.motherToTracker, warningMessage='Mother out of view', playSound=True)
        self.addWatchedNode(wd, self.motherToTracker, warningMessage = 'Mother is out of view', playSound = True)



    try:
      self.babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
    except:
      print('Unable to receive BabyHeadToTracker transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # self.addWatchdog(self.babyHeadToTracker, warningMessage='BabyHead out of view', playSound=True)
        self.addWatchedNode(wd, self.babyHeadToTracker, warningMessage = 'BabyHead is out of view', playSound = True)


    try:
      self.babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
    except:
      print('Unable to receive BabyHeadToTracker transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1
    else:
      if self.firstTime:
        # self.addWatchdog(self.babyBodyToTracker, warningMessage='BabyBody out of view', playSound=True)
        self.addWatchedNode(wd, self.babyBodyToTracker, warningMessage = 'BabyBody is out of view', playSound = True)


    # try:
    #   self.trackerToHandL = slicer.util.getNode('TrackerToHandL')
    # except:
    #   print('Unable to receive TrackerToHandL transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1

    
    # try:
    #   self.trackerToThumbL = slicer.util.getNode('TrackerToThumbL')
    # except:
    #   print('Unable to receive TrackerToThumbL transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1
    

    # try:
    #   self.trackerToHandR = slicer.util.getNode('TrackerToHandR')
    # except:
    #   print('Unable to receive TrackerToHandR transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1


    # try:
    #   self.trackerToThumbR = slicer.util.getNode('TrackerToThumbR')
    # except:
    #   print('Unable to receive TrackerToThumbR transform from Plus')
    #   nonLoadedTransforms = nonLoadedTransforms +1


    try:
      self.trackerToMother = slicer.util.getNode('TrackerToMother')
    except:
      print('Unable to receive TrackerToMother transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1


    try:
      self.trackerToBabyHead = slicer.util.getNode('TrackerToBabyHead')
    except:
      print('Unable to receive TrackerToBabyHead transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1


    try:
      self.trackerToBabyBody = slicer.util.getNode('TrackerToBabyBody')
    except:
      print('Unable to receive TrackerToBabyHead transform from Plus')
      nonLoadedTransforms = nonLoadedTransforms +1

    

    if nonLoadedTransforms == 0:
      logging.debug('Setting transform tree')
      # # Hand L
      # self.handLModel.SetAndObserveTransformNodeID(self.handLModelToHandL.GetID())
      # self.checkFiducialsHandL.SetAndObserveTransformNodeID(self.handLModelToHandL.GetID())
      # self.handLModelToHandL.SetAndObserveTransformNodeID(self.handLToTracker.GetID())

      # # Thumb L
      # self.thumbLModel.SetAndObserveTransformNodeID(self.thumbLModelToThumbL.GetID())
      # self.checkFiducialsThumbL.SetAndObserveTransformNodeID(self.thumbLModelToThumbL.GetID())
      # self.thumbLModelToThumbL.SetAndObserveTransformNodeID(self.thumbLToTracker.GetID())

      # # Hand R
      # self.handRModel.SetAndObserveTransformNodeID(self.handRModelToHandR.GetID())
      # self.checkFiducialsHandR.SetAndObserveTransformNodeID(self.handRModelToHandR.GetID())
      # self.handRModelToHandR.SetAndObserveTransformNodeID(self.handRToTracker.GetID())

      # # Thumb R
      # self.thumbRModel.SetAndObserveTransformNodeID(self.thumbRModelToThumbR.GetID())
      # self.checkFiducialsThumbR.SetAndObserveTransformNodeID(self.thumbRModelToThumbR.GetID())
      # self.thumbRModelToThumbR.SetAndObserveTransformNodeID(self.thumbRToTracker.GetID())

      # Baby body
      self.babyBodyModel.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      # Help
      self.handLModelGrabHelp.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.handRModelGrabHelp.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.thumbLModelGrabHelp.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.thumbRModelGrabHelp.SetAndObserveTransformNodeID(self.babyBodyModelToBabyBody.GetID())
      self.babyBodyModelToBabyBody.SetAndObserveTransformNodeID(self.babyBodyToTracker.GetID())

      #Baby head
      self.babyHeadModel.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.babyPlane.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      # Fiducials
      self.occiputFiducials.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      # Help models
      # Right-handed
      self.handLModelHoldHelpL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbLModelHoldHelpL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.handLModelHoldHelpR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbLModelHoldHelpR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.handLModelDeflexionHelp.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbLModelDeflexionHelp.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      
      # Left-handed
      self.handRModelHoldHelpL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbRModelHoldHelpL.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.handRModelHoldHelpR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbRModelHoldHelpR.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.handRModelDeflexionHelp.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())
      self.thumbRModelDeflexionHelp.SetAndObserveTransformNodeID(self.babyHeadModelToBabyHead.GetID())

      self.babyHeadModelToBabyHead.SetAndObserveTransformNodeID(self.babyHeadToTracker.GetID())

      # Mother
      self.motherModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.motherTummyModel.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      # Fiducials
      self.checkFiducialsMother.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      # Help models
      # Right-handed
      self.handRModelGuardHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.thumbRModelGuardHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      # Left-handed
      self.handLModelGuardHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.thumbLModelGuardHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      # Help models place baby on mother
      self.handLModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.handRModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.thumbLModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.thumbRModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.babyHeadModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.babyBodyModelPlaceHelp.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      #Cameras
      self.cameraTransform_front.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.cameraTransform_side.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.cameraTransform_up.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      #Realistic models
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
      # Planes
      self.ischialPlane.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_1.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus1.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_2.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus2.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_3.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus3.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minusMiddle.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_middle.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_05.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus05.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_15.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus15.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_25.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.ischialPlane_minus25.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      # Arrows
      self.arrow1.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrow2.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrow3.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrow4.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      self.arrowDown1.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrowDown2.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrowDown3.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())
      self.arrowDown4.SetAndObserveTransformNodeID(self.motherModelToMother.GetID())

      self.motherModelToMother.SetAndObserveTransformNodeID(self.motherToTracker.GetID())

      # self.handRToTracker.SetAndObserveTransformNodeID(None)
      # self.thumbRToTracker.SetAndObserveTransformNodeID(None)
      # self.handLToTracker.SetAndObserveTransformNodeID(None)
      # self.thumbLToTracker.SetAndObserveTransformNodeID(None)
      self.babyBodyToTracker.SetAndObserveTransformNodeID(None)
      self.babyHeadToTracker.SetAndObserveTransformNodeID(None)
      self.motherToTracker.SetAndObserveTransformNodeID(None)

      # self.trackerToHandR.SetAndObserveTransformNodeID(None)
      # self.trackerToThumbR.SetAndObserveTransformNodeID(None)
      # self.trackerToHandL.SetAndObserveTransformNodeID(None)
      # self.trackerToThumbL.SetAndObserveTransformNodeID(None)
      self.trackerToBabyBody.SetAndObserveTransformNodeID(None)
      self.trackerToBabyHead.SetAndObserveTransformNodeID(None)
      self.trackerToMother.SetAndObserveTransformNodeID(None)

      # Enable buttons
      if self.firstTime:
        self.firstTime = False
        self.loadCollapsibleButton.collapsed = True
        self.step1CollapsibleButton.collapsed = False
        self.deflexionGroupBox.collapsed = False

        self.check_deflexion.enabled = True
        self.check_protect.enabled = True
        self.check_hold.enabled = True
        self.check_protect2.enabled = True
        self.check_body.enabled = True
        self.check_placeOnMother.enabled = True

        self.start_deflexion.enabled = True
        self.start_protect.enabled = True
        self.start_hold.enabled = True
        self.start_protect2.enabled = True
        self.check_body.enabled = True
        self.start_placeOnMother.enabled = True

        self.next_deflexion.enabled = True
        self.next_protect.enabled = True
        self.next_hold.enabled = True
        self.next_descent.enabled = True
        self.next_protect2.enabled = True
        self.next_ascent.enabled = True
        self.next_body.enabled = True
        self.next_placeOnMother.enabled = True


        self.help_deflexion.enabled = True
        self.help_protect.enabled = True
        self.help_hold.enabled = True
        self.help_descent.enabled = True
        self.help_protect2.enabled = True
        self.help_ascent.enabled = True
        self.help_body.enabled = True
        self.help_placeOnMother.enabled = True

        self.showAnswersButton.enabled = True
        self.saveAnswerButton.enabled = True

        


  def onUserNameSaveButtonCLicked(self):
    self.logic.userName = self.userName_textInput.text
    self.configurationCollapsibleButton.collapsed = True
    if self.rightHandedRadioButton.isChecked():
      self.logic.handedness = 'right'
      print('Right-handed user')
    else:
      self.logic.handedness = 'left'
      print('Left-handed user')
  


  def onSensibilityCheckBoxClicked(self):
    if self.sensibilityCheckBox.isChecked():
      print('Sensibility reduced')
      self.errorMargin = 10 #mm
    else:
      print('Sensibility increased')
      self.errorMargin = 5



  def onSelectHandClicked(self):
    if self.rightHandedRadioButton.isChecked():
      self.logic.handedness = 'right'
      print('Right-handed user')
    else:
      self.logic.handedness = 'left'
      print('Left-handed user')



  def onSelectBellyClicked(self):
    try:
      self.motherTummyModel = slicer.util.getNode('MotherTummyModel')
    except:
      print('MotherTummyModel not found')
    else:
      if self.solidRadioButton_belly.isChecked():
        self.transparentRadioButton_belly.checked = False
        self.invisibleRadioButton_belly.checked = False
        self.motherTummyModel.GetDisplayNode().SetOpacity(1)
        print('Solid belly')
      elif self.transparentRadioButton_belly.isChecked():
        self.solidRadioButton_belly.checked = False
        self.invisibleRadioButton_belly.checked = False
        self.motherTummyModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent belly')
      else:
        self.solidRadioButton_belly.checked = False
        self.transparentRadioButton_belly.checked = False
        self.motherTummyModel.GetDisplayNode().SetOpacity(0)
        print('Invisible belly')




  def onSelectMotherClicked(self):
    try:
      self.motherModel = slicer.util.getNode('MotherModel')
    except:
      print('MotherModel not found')
    else:
      if self.solidRadioButton_mother.isChecked():
        self.transparentRadioButton_mother.checked = False
        self.invisibleRadioButton_mother.checked = False
        self.motherModel.GetDisplayNode().SetOpacity(1)
        print('Solid mother model')
      elif self.transparentRadioButton_mother.isChecked():
        self.solidRadioButton_mother.checked = False
        self.invisibleRadioButton_mother.checked = False
        self.motherModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent mother model')
      else:
        self.solidRadioButton_mother.checked = False
        self.transparentRadioButton_mother.checked = False
        self.motherModel.GetDisplayNode().SetOpacity(0)
        print('Invisible mother model')



  def onSelectBabyClicked(self):
    try:
      self.babyHeadModel = slicer.util.getNode('BabyHeadModel')
      self.babyBodyModel = slicer.util.getNode('BabyBodyModel')
    except:
      print('Baby model not found')
    else:
      if self.solidRadioButton_baby.isChecked():
        self.transparentRadioButton_baby.checked = False
        self.invisibleRadioButton_baby.checked = False
        self.babyHeadModel.GetDisplayNode().SetOpacity(1)
        self.babyBodyModel.GetDisplayNode().SetOpacity(1)
        print('Solid baby model')
      elif self.transparentRadioButton_baby.isChecked():
        self.solidRadioButton_baby.checked = False
        self.invisibleRadioButton_baby.checked = False
        self.babyHeadModel.GetDisplayNode().SetOpacity(0.5)
        self.babyBodyModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent baby model')
      else:
        self.solidRadioButton_baby.checked = False
        self.transparentRadioButton_baby.checked = False
        self.babyHeadModel.GetDisplayNode().SetOpacity(0)
        self.babyBodyModel.GetDisplayNode().SetOpacity(0)
        print('Invisible baby model')




  def onSelectMotherRealClicked(self):
    try:
      self.motherRealisticModel = slicer.util.getNode('motherRealisticModel')
    except:
      print('Realistic mother model not found')
    else:
      if self.solidRadioButton_motherReal.isChecked():
        self.transparentRadioButton_motherReal.checked = False
        self.invisibleRadioButton_motherReal.checked = False
        self.motherRealisticModel.GetDisplayNode().SetOpacity(1)
        print('Solid realistic mother model')
      elif self.transparentRadioButton_motherReal.isChecked():
        self.solidRadioButton_motherReal.checked = False
        self.invisibleRadioButton_motherReal.checked = False
        self.motherRealisticModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent realistic mother model')
      else:
        self.solidRadioButton_motherReal.checked = False
        self.transparentRadioButton_motherReal.checked = False
        self.motherRealisticModel.GetDisplayNode().SetOpacity(0)
        print('Invisible realistic mother model')
      



  def onSelectPelvisRightClicked(self):
    try:
      self.rightPelvis1Model = slicer.util.getNode('rightPelvis1Model')
      self.rightPelvis2Model = slicer.util.getNode('rightPelvis2Model')
      self.rightPelvis3Model = slicer.util.getNode('rightPelvis3Model')
      self.sacrumRightModel = slicer.util.getNode('sacrumRightModel')
      self.coxisRightModel = slicer.util.getNode('coxisRightModel')
      self.middlePelvisModel = slicer.util.getNode('middlePelvisModel')
    except:
      print('Pelvis models not found')
    else:
      if self.solidRadioButton_pelvisRight.isChecked():
        self.transparentRadioButton_pelvisRight.checked = False
        self.invisibleRadioButton_pelvisRight.checked = False
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(1)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(1)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(1)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(1)
        self.coxisRightModel.GetDisplayNode().SetOpacity(1)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(1)
        print('Solid right pelvis model')
      elif self.transparentRadioButton_pelvisRight.isChecked():
        self.solidRadioButton_pelvisRight.checked = False
        self.invisibleRadioButton_pelvisRight.checked = False
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(0.5)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(0.5)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(0.5)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(0.5)
        self.coxisRightModel.GetDisplayNode().SetOpacity(0.5)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent right pelvis')
      else:
        self.solidRadioButton_pelvisRight.checked = False
        self.transparentRadioButton_pelvisRight.checked = False
        self.rightPelvis1Model.GetDisplayNode().SetOpacity(0)
        self.rightPelvis2Model.GetDisplayNode().SetOpacity(0)
        self.rightPelvis3Model.GetDisplayNode().SetOpacity(0)
        self.sacrumRightModel.GetDisplayNode().SetOpacity(0)
        self.coxisRightModel.GetDisplayNode().SetOpacity(0)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0)
        print('Invisible right pelvis')



  def onSelectPelvisLeftClicked(self):
    try:
      self.leftPelvis1Model = slicer.util.getNode('leftPelvis1Model')
      self.leftPelvis2Model = slicer.util.getNode('leftPelvis2Model')
      self.leftPelvis3Model = slicer.util.getNode('leftPelvis3Model')
      self.sacrumLeftModel = slicer.util.getNode('sacrumLeftModel')
      self.coxisLeftModel = slicer.util.getNode('coxisLeftModel')
      self.middlePelvisModel = slicer.util.getNode('middlePelvisModel')
    except:
      print('Pelvis models not found')
    else:
      if self.solidRadioButton_pelvisLeft.isChecked():
        self.transparentRadioButton_pelvisLeft.checked = False
        self.invisibleRadioButton_pelvisLeft.checked = False
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(1)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(1)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(1)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(1)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(1)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(1)
        print('Solid left pelvis model')
      elif self.transparentRadioButton_pelvisLeft.isChecked():
        self.solidRadioButton_pelvisLeft.checked = False
        self.invisibleRadioButton_pelvisLeft.checked = False
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(0.5)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(0.5)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(0.5)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(0.5)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(0.5)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0.5)
        print('Transparent left pelvis')
      else:
        self.solidRadioButton_pelvisLeft.checked = False
        self.transparentRadioButton_pelvisLeft.checked = False
        self.leftPelvis1Model.GetDisplayNode().SetOpacity(0)
        self.leftPelvis2Model.GetDisplayNode().SetOpacity(0)
        self.leftPelvis3Model.GetDisplayNode().SetOpacity(0)
        self.sacrumLeftModel.GetDisplayNode().SetOpacity(0)
        self.coxisLeftModel.GetDisplayNode().SetOpacity(0)
        self.middlePelvisModel.GetDisplayNode().SetOpacity(0)
        print('Invisible left pelvis')



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
      print('Set fixed view')
      motherModelToMother = slicer.util.getNode('MotherModelToMother')
      upView.SetAndObserveTransformNodeID(motherModelToMother.GetID())
    else:
      print('Set free view')
      upView.SetAndObserveTransformNodeID(None)
      # Center 3D view
      layoutManager = slicer.app.layoutManager()

      threeDWidget0 = layoutManager.threeDWidget(0)
      threeDView0 = threeDWidget0.threeDView()
      threeDView0.resetFocalPoint()

      threeDWidget1 = layoutManager.threeDWidget(1)
      threeDView1 = threeDWidget1.threeDView()
      threeDView1.resetFocalPoint()


  ###---STEP 1---###

  # DEFLEXION

  def onCheckDeflexionClicked(self):
    self.check_deflexion.enabled = False #to check again press retry
    self.retry_deflexion.enabled = True 
    self.next_deflexion.enabled = True
    self.retry_enabled = self.retry_deflexion.enabled #save state of button

    margin = 30 + self.errorMargin
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkDeflexion(margin,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_deflexion.setText(text)
    self.logic.recordSoftwareActivity('Control deflexion',text.replace('\n','; '))



  def onStartDeflexionClicked(self):
    state = self.start_deflexion.text
    if self.rightHandedRadioButton.isChecked():
      toolToReference = 'HandLToTracker' # Non-dominant hand
    else:
      toolToReference = 'HandRToTracker'

    if state == 'Start':
      self.start_deflexion.setText('Stop')
      self.start_deflexion.setIcon(self.start_deflexion_icon_pause)
      self.check_deflexion.enabled = False
      self.next_deflexion.enabled = False
      self.retry_deflexion.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_deflexion.setText('Start')
      self.start_deflexion.setIcon(self.start_deflexion_icon_play)
      self.next_deflexion.enabled = True
      if self.retry_enabled:
        self.retry_deflexion.enabled = True #if was previously enabled, enable again retry. Otherwise stay unenabled
      else:
        self.check_deflexion.enabled = True




  def onRetryDeflexionClicked(self):
    self.retry_deflexion.enabled = False
    self.check_deflexion.enabled = True
    self.result_deflexion.setText('')
    self.retry_enabled = self.retry_deflexion.enabled #save state of button



  def onNextDeflexionClicked(self):
    self.deflexionGroupBox.collapsed = True
    self.protectGroupBox.collapsed = False
    self.check_protect.enabled = True
    self.start_protect.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False #next retry button is still unenabled

    help_text = self.help_deflexion.text

    if help_text == 'Hide help': #close help if open
      self.onHelpDeflexionClicked()



  def onHelpDeflexionClicked(self):
    help_text = self.help_deflexion.text
    if help_text == 'Help':
      self.help_deflexion.setText('Hide help')
      if self.rightHandedRadioButton.isChecked():
        # Right-handed -> control deflexion with left hand
        self.handLModelDeflexionHelpDisplay.SetOpacity(0.5)
        self.thumbLModelDeflexionHelpDisplay.SetOpacity(0.5)
      else:
        # Left-handed -> control deflexion with right hand
        self.handRModelDeflexionHelpDisplay.SetOpacity(0.5)
        self.thumbRModelDeflexionHelpDisplay.SetOpacity(0.5)
    else:
      self.help_deflexion.setText('Help')
      self.handLModelDeflexionHelpDisplay.SetOpacity(0)
      self.thumbLModelDeflexionHelpDisplay.SetOpacity(0)
      self.handRModelDeflexionHelpDisplay.SetOpacity(0)
      self.thumbRModelDeflexionHelpDisplay.SetOpacity(0)


  # GUARD PERINEUM

  def onCheckProtectClicked(self):
    self.check_protect.enabled = False #to check again press retry
    self.retry_protect.enabled = True 
    self.next_protect.enabled = True
    self.retry_enabled = self.retry_protect.enabled #save state of button

    margin = 5 + self.errorMargin
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkProtect(margin,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_protect.setText(text)
    self.logic.recordSoftwareActivity('Guard perineum',text.replace('\n','; '))


  def onStartProtectClicked(self):
    state = self.start_protect.text
    if self.rightHandedRadioButton.isChecked(): 
      toolToReference = 'HandRToTracker' #Dominant hand
    else:
      toolToReference = 'HandLToTracker'

    if state == 'Start':
      self.start_protect.setText('Stop')
      self.start_protect.setIcon(self.start_protect_icon_pause)
      self.check_protect.enabled = False
      self.next_protect.enabled = False
      self.retry_protect.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_protect.setText('Start')
      self.start_protect.setIcon(self.start_protect_icon_play)
      self.next_protect.enabled = True
      if self.retry_enabled:
        self.retry_protect.enabled = True #if was previously enabled, enable again retry. Otherwise stay unenabled
      else:
        self.check_protect.enabled = True


  def onRetryProtectClicked(self):
    self.retry_protect.enabled = False
    self.check_protect.enabled = True
    self.result_protect.setText('')
    self.retry_enabled = self.retry_protect.enabled #save state of button

  
  def onNextProtectClicked(self):
    self.protectGroupBox.collapsed = True
    self.step1CollapsibleButton.collapsed = True
    self.step2CollapsibleButton.collapsed = False
    self.holdGroupBox.collapsed = False
    self.check_hold.enabled = True
    self.start_hold.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False #next retry button is still unenabled

    help_text = self.help_protect.text

    if help_text == 'Hide help': #close help if open
      self.onHelpProtectClicked()


  def onHelpProtectClicked(self):
    help_text = self.help_protect.text
    if help_text == 'Help':
      self.help_protect.setText('Hide help')
      # Use dominant hand
      if self.rightHandedRadioButton.isChecked(): # Right-handed use the right hand
        self.handRModelGuardHelpDisplay.SetOpacity(0.5)
        self.thumbRModelGuardHelpDisplay.SetOpacity(0.5)
      else:
        self.handLModelGuardHelpDisplay.SetOpacity(0.5)
        self.thumbLModelGuardHelpDisplay.SetOpacity(0.5)
    else:
      self.help_protect.setText('Help')
      self.handRModelGuardHelpDisplay.SetOpacity(0)
      self.thumbRModelGuardHelpDisplay.SetOpacity(0)
      self.handLModelGuardHelpDisplay.SetOpacity(0)
      self.thumbLModelGuardHelpDisplay.SetOpacity(0)


  ###---STEP 2---###

  # HOLD HEAD

  def onCheckHoldClicked(self):
    self.check_hold.enabled = False #to check again press retry
    self.retry_hold.enabled = True 
    self.next_hold.enabled = True
    self.retry_enabled = self.retry_hold.enabled #save state of button

    margin1 = 20 + self.errorMargin
    margin2 = 20  # At least 2 cm away from mother
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkHold(margin1,margin2,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_hold.setText(text)
    self.logic.recordSoftwareActivity('Hold head',text.replace('\n','; '))


  def onStartHoldClicked(self):
    state = self.start_hold.text

    if self.rightHandedRadioButton.isChecked():
      toolToReference = 'HandLToTracker' # Non-dominant hand
    else:
      toolToReference = 'HandRToTracker'

    if state == 'Start':
      self.start_hold.setText('Stop')
      self.start_hold.setIcon(self.start_hold_icon_pause)
      self.check_hold.enabled = False
      self.next_hold.enabled = False
      self.retry_hold.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_hold.setText('Start')
      self.start_hold.setIcon(self.start_hold_icon_play)
      self.next_hold.enabled = True
      if self.retry_enabled:
        self.retry_hold.enabled = True #if was previously enabled, enable again retry. Otherwise stay unenabled
      else:
        self.check_hold.enabled = True


  def onRetryHoldClicked(self):
    self.retry_hold.enabled = False
    self.check_hold.enabled = True
    self.result_hold.setText('')
    self.retry_enabled = self.retry_hold.enabled #save state of button

  
  def onNextHoldClicked(self):
    self.holdGroupBox.collapsed = True
    self.descentGroupBox.collapsed = False
    self.next_descent.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False #next retry button is still unenabled

    help_text = self.help_hold.text

    if help_text == 'Hide help': #close help if open
      self.onHelpHoldClicked()


  def onHelpHoldClicked(self):
    help_text = self.help_hold.text
    if help_text == 'Help':
      self.help_hold.setText('Hide help')

      # Check if the baby's head is facing to the right or to the left
      self.logic.buildTransformTree('MotherModelToMother')
      rightEar = self.logic.getCoordinates('OcciputFiducials',3)
      leftEar = self.logic.getCoordinates('OcciputFiducials',4)
      if rightEar[2] > leftEar[2]: # Facing to the left (mother's right tight) -> place hand on the left side of the head
        if self.rightHandedRadioButton.isChecked(): 
          self.handLModelHoldHelpLDisplay.SetOpacity(0.5)
          self.thumbLModelHoldHelpLDisplay.SetOpacity(0.5)
        else:
          self.handRModelHoldHelpLDisplay.SetOpacity(0.5)
          self.thumbRModelHoldHelpLDisplay.SetOpacity(0.5)
      else: # Facing to the right (mother's left tight) -> place hand on the right side of the head
        if self.rightHandedRadioButton.isChecked(): 
          self.handLModelHoldHelpRDisplay.SetOpacity(0.5)
          self.thumbLModelHoldHelpRDisplay.SetOpacity(0.5)
        else:
          self.handRModelHoldHelpRDisplay.SetOpacity(0.5)
          self.thumbRModelHoldHelpRDisplay.SetOpacity(0.5)
      self.onApplyTransformsButtonClicked()
    else:
      self.help_hold.setText('Help')
      self.handLModelHoldHelpLDisplay.SetOpacity(0)
      self.thumbLModelHoldHelpLDisplay.SetOpacity(0)
      self.handRModelHoldHelpLDisplay.SetOpacity(0)
      self.thumbRModelHoldHelpLDisplay.SetOpacity(0)
      self.handLModelHoldHelpRDisplay.SetOpacity(0)
      self.thumbLModelHoldHelpRDisplay.SetOpacity(0)
      self.handRModelHoldHelpRDisplay.SetOpacity(0)
      self.thumbRModelHoldHelpRDisplay.SetOpacity(0)



  # def onCheckStep2Clicked(self):
  #   self.check_step2.enabled = False #to check again press retry
  #   self.retry_step2.enabled = True 
  #   self.next_step2.enabled = True
  #   self.retry_enabled = self.retry_step2.enabled #save the state of the button



  # def onStartStep2Clicked(self):
  #   state = self.start_step2.text

  #   if self.logic.handedness == 'right':
  #     pass
  #   else:
  #     pass

  #   if state == 'Start':
  #     self.start_step2.setText('Stop')
  #     self.start_step2.setIcon(self.start_step2_icon_pause)
  #     self.check_step2.enabled = False
  #     self.next_step2.enabled = False
  #     self.retry_step2.enabled = False
  #   else:
  #     self.start_step2.setText('Start')
  #     self.start_step2.setIcon(self.start_step2_icon_play)
  #     self.next_step2.enabled = True
  #     if self.retry_enabled:
  #       self.retry_step2.enabled = True
  #     else:
  #       self.check_step2.enabled = True



  # def onRetryStep2Clicked(self):
  #   self.retry_step2.enabled = False
  #   self.check_step2.enabled = True
  #   self.result_step2.setText('')
  #   self.retry_enabled = self.retry_step2.enabled



  # def onNextStep2Clicked(self):
  #   self.step2CollapsibleButton.collapsed = True
  #   self.step3CollapsibleButton.collapsed = False
  #   self.check_ascent.enabled = True
  #   self.start_ascent.enabled = True
  #   self.onApplyTransformsButtonClicked()
  #   self.retry_enabled = False

  #   help_text = self.help_step2.text

  #   if help_text == 'Hide help':
  #     self.onHelpStep2Clicked()



  # def onHelpStep2Clicked(self):
  #   help_text = self.help_step2.text
  #   if help_text == 'Help':
  #     self.help_step2.setText('Hide help')
  #   else:
  #     self.help_step2.setText('Help')


  # def onCheckDescentClicked(self):
  #   pass


  # def onStartDescentClicked(self):
  #   pass


  # def onRetryDescentClicked(self):
  #   pass

  
  def onNextDescentClicked(self):
    self.descentGroupBox.collapsed = True
    self.step2CollapsibleButton.collapsed = True
    self.step3CollapsibleButton.collapsed = False
    self.protect2GroupBox.collapsed = False
    self.check_protect2.enabled = True
    self.start_protect2.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False #next retry button is still unenabled

    help_text = self.help_descent.text

    if help_text == 'Hide help': #close help if open
      self.onHelpDescentClicked()


  def onHelpDescentClicked(self):
    help_text = self.help_descent.text
    if help_text == 'Help':
      self.help_descent.setText('Hide help')
      #for i in range(3):
      # self.arrow1Display.SetOpacity(1)
      # slicer.app.processEvents() # Process events to allow screen to refresh
      # time.sleep(1)
      # self.arrow1Display.SetOpacity(0)
      # slicer.app.processEvents()
      # self.arrow2Display.SetOpacity(1)
      # slicer.app.processEvents()
      # time.sleep(1)
      # self.arrow2Display.SetOpacity(0)
      # slicer.app.processEvents()
      # self.arrow3Display.SetOpacity(1)
      # slicer.app.processEvents()
      # time.sleep(1)
      # self.arrow3Display.SetOpacity(0)
      # slicer.app.processEvents()
      # self.arrow4Display.SetOpacity(1)
      # slicer.app.processEvents()
      # time.sleep(1)
      # self.arrow4Display.SetOpacity(0)
      # slicer.app.processEvents()
      # time.sleep(1.2)
      self.arrow1Display.SetOpacity(1)
      self.arrow2Display.SetOpacity(1)
      self.arrow3Display.SetOpacity(1)
      self.arrow4Display.SetOpacity(1)
    else:
      self.help_descent.setText('Help')
      self.arrow1Display.SetOpacity(0)
      self.arrow2Display.SetOpacity(0)
      self.arrow3Display.SetOpacity(0)
      self.arrow4Display.SetOpacity(0)


###---STEP 3---###

  # GUARD PERINEUM 2
  def onCheckProtect2Clicked(self):
    self.check_protect2.enabled = False #to check again press retry
    self.retry_protect2.enabled = True 
    self.next_protect2.enabled = True
    self.retry_enabled = self.retry_protect2.enabled #save state of button

    margin = 5 + self.errorMargin
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkProtect(margin,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_protect2.setText(text)
    self.logic.recordSoftwareActivity('Guard again perineum',text.replace('\n','; '))


  def onStartProtect2Clicked(self):
    state = self.start_protect2.text

    if self.rightHandedRadioButton.isChecked(): 
      toolToReference = 'HandRToTracker' #Dominant hand
    else:
      toolToReference = 'HandLToTracker'

    if state == 'Start':
      self.start_protect2.setText('Stop')
      self.start_protect2.setIcon(self.start_protect2_icon_pause)
      self.check_protect2.enabled = False
      self.next_protect2.enabled = False
      self.retry_protect2.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_protect2.setText('Start')
      self.start_protect2.setIcon(self.start_protect2_icon_play)
      self.next_protect2.enabled = True
      if self.retry_enabled:
        self.retry_protect2.enabled = True #if was previously enabled, enable again retry. Otherwise stay unenabled
      else:
        self.check_protect2.enabled = True


  def onRetryProtect2Clicked(self):
    self.retry_protect2.enabled = False
    self.check_protect2.enabled = True
    self.result_protect2.setText('')
    self.retry_enabled = self.retry_protect2.enabled #save state of button


  def onNextProtect2Clicked(self):
    self.protect2GroupBox.collapsed = True
    self.ascentGroupBox.collapsed = False
    self.next_ascent.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False #next retry button is still unenabled

    help_text = self.help_protect2.text

    if help_text == 'Hide help': #close help if open
      self.onHelpProtect2Clicked()


  def onHelpProtect2Clicked(self):
    help_text = self.help_protect2.text
    if help_text == 'Help':
      self.help_protect2.setText('Hide help')
      # Use dominant hand
      if self.rightHandedRadioButton.isChecked(): # Right-handed use the right hand
        self.handRModelGuardHelpDisplay.SetOpacity(0.5)
        self.thumbRModelGuardHelpDisplay.SetOpacity(0.5)
      else:
        self.handLModelGuardHelpDisplay.SetOpacity(0.5)
        self.thumbLModelGuardHelpDisplay.SetOpacity(0.5)
    else:
      self.help_protect2.setText('Help')
      self.handRModelGuardHelpDisplay.SetOpacity(0)
      self.thumbRModelGuardHelpDisplay.SetOpacity(0)
      self.handLModelGuardHelpDisplay.SetOpacity(0)
      self.thumbLModelGuardHelpDisplay.SetOpacity(0)
# ASCENT

  # def onCheckAscentClicked(self):
  #   self.check_ascent.enabled = False #to check again press retry
  #   self.retry_ascent.enabled = True 
  #   self.next_ascent.enabled = True
  #   self.retry_enabled = self.retry_ascent.enabled



  # def onStartAscentClicked(self):
  #   state = self.start_ascent.text

  #   if self.logic.handedness == 'right':
  #     pass
  #   else:
  #     pass

  #   if state == 'Start':
  #     self.start_ascent.setText('Stop')
  #     self.start_ascent.setIcon(self.start_ascent_icon_pause)
  #     self.check_ascent.enabled = False
  #     self.next_ascent.enabled = False
  #     self.retry_ascent.enabled = False
  #   else:
  #     self.start_ascent.setText('Start')
  #     self.start_ascent.setIcon(self.start_ascent_icon_play)
  #     self.next_ascent.enabled = True
  #     if self.retry_enabled:
  #       self.retry_ascent.enabled = True
  #     else:
  #       self.check_ascent.enabled = True



  # def onRetryAscentClicked(self):
  #   self.retry_ascent.enabled = False
  #   self.check_ascent.enabled = True
  #   self.result_ascent.setText('')
  #   self.retry_enabled = self.retry_ascent.enabled



  def onNextAscentClicked(self):
    self.ascentGroupBox.collapsed = True
    self.step3CollapsibleButton.collapsed = True
    self.step4CollapsibleButton.collapsed = False
    self.grabBodyGroupBox.collapsed = False
    self.check_body.enabled = True
    self.start_body.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False
    
    help_text = self.help_ascent.text

    if help_text == 'Hide help':
      self.onHelpAscentClicked()



  def onHelpAscentClicked(self):
    help_text = self.help_ascent.text
    if help_text == 'Help':
      self.help_ascent.setText('Hide help')
      self.arrowDown1Display.SetOpacity(1)
      self.arrowDown2Display.SetOpacity(1)
      self.arrowDown3Display.SetOpacity(1)
      self.arrowDown4Display.SetOpacity(1)
    else:
      self.help_ascent.setText('Help')
      self.arrowDown1Display.SetOpacity(0)
      self.arrowDown2Display.SetOpacity(0)
      self.arrowDown3Display.SetOpacity(0)
      self.arrowDown4Display.SetOpacity(0)






###---STEP 4---###

  def onCheckBodyClicked(self):
    self.check_body.enabled = False #to check again press retry
    self.retry_body.enabled = True 
    self.next_body.enabled = True
    self.retry_enabled = self.retry_body.enabled

    margin1 = 20 + self.errorMargin
    margin2 = 10 # At least 1 cm away from head
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkBody(margin1,margin2,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_body.setText(text)
    self.logic.recordSoftwareActivity('Grab body',text.replace('\n','; '))



  def onStartBodyClicked(self):
    state = self.start_body.text

    if self.rightHandedRadioButton.isChecked(): 
      toolToReference = 'HandRToTracker' #Dominant hand
    else:
      toolToReference = 'HandLToTracker'

    if state == 'Start':
      self.start_body.setText('Stop')
      self.start_body.setIcon(self.start_body_icon_pause)
      self.check_body.enabled = False
      self.next_body.enabled = False
      self.retry_body.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_body.setText('Start')
      self.start_body.setIcon(self.start_body_icon_play)
      self.next_body.enabled = True
      if self.retry_enabled:
        self.retry_body.enabled = True
      else:
        self.check_body.enabled = True



  def onRetryBodyClicked(self):
    self.retry_body.enabled = False
    self.check_body.enabled = True
    self.result_body.setText('')
    self.retry_enabled = self.retry_body.enabled



  def onNextBodyClicked(self):
    self.grabBodyGroupBox.collapsed = True
    self.placeOnMotherGroupBox.collapsed = False
    self.next_placeOnMother.enabled = True
    self.onApplyTransformsButtonClicked()
    self.retry_enabled = False

    help_text = self.help_body.text

    if help_text == 'Hide help':
      self.onHelpBodyClicked()



  def onHelpBodyClicked(self):
    help_text = self.help_body.text
    if help_text == 'Help':
      self.help_body.setText('Hide help')
      self.handLModelGrabHelpDisplay.SetOpacity(0.5)
      self.handRModelGrabHelpDisplay.SetOpacity(0.5)
      self.thumbLModelGrabHelpDisplay.SetOpacity(0.5)
      self.thumbRModelGrabHelpDisplay.SetOpacity(0.5)
    else:
      self.help_body.setText('Help')
      self.handLModelGrabHelpDisplay.SetOpacity(0)
      self.handRModelGrabHelpDisplay.SetOpacity(0)
      self.thumbLModelGrabHelpDisplay.SetOpacity(0)
      self.thumbRModelGrabHelpDisplay.SetOpacity(0)


  def onCheckPlaceOnMotherClicked(self):
    self.check_placeOnMother.enabled = False #to check again press retry
    self.retry_placeOnMother.enabled = True 
    self.next_placeOnMother.enabled = True
    self.retry_enabled = self.retry_placeOnMother.enabled

    margin1 = 20 + self.errorMargin
    margin2 = 10 
    if self.rightHandedRadioButton.isChecked():
      handedness = 'R'
    else:
      handedness = 'L'
    res, message = self.logic.checkPlaceOnMother(margin1,margin2,handedness)
    if res:
      text = 'CORRECT!'
    else:
      text = 'INCORRECT:\n' + message
    
    self.result_placeOnMother.setText(text)
    self.logic.recordSoftwareActivity('Place on mother',text.replace('\n','; '))

  
  def onStartPlaceOnMotherClicked(self):
    state = self.start_placeOnMother.text

    if self.rightHandedRadioButton.isChecked(): 
      toolToReference = 'HandRToTracker' #Dominant hand
    else:
      toolToReference = 'HandLToTracker'

    if state == 'Start':
      self.start_placeOnMother.setText('Stop')
      self.start_placeOnMother.setIcon(self.start_placeOnMother_icon_pause)
      self.check_placeOnMother.enabled = False
      self.next_placeOnMother.enabled = False
      self.retry_placeOnMother.enabled = False
      self.addActionObserver(toolToReference)
    else:
      self.removeActionObserver(toolToReference)
      self.start_placeOnMother.setText('Start')
      self.start_placeOnMother.setIcon(self.start_placeOnMother_icon_play)
      self.next_placeOnMother.enabled = True
      if self.retry_enabled:
        self.retry_placeOnMother.enabled = True
      else:
        self.check_placeOnMother.enabled = True

  
  def onRetryPlaceOnMotherClicked(self):
    self.retry_placeOnMother.enabled = False
    self.check_placeOnMother.enabled = True
    self.result_placeOnMother.setText('')
    self.retry_enabled = self.retry_placeOnMother.enabled
  

  def onNextPlaceOnMotherClicked(self):
    self.step4CollapsibleButton.collapsed = True
    self.saveDataCollapsibleButton.collapsed = False
    self.onApplyTransformsButtonClicked()

    help_text = self.help_placeOnMother.text

    if help_text == 'Hide help':
      self.onHelpPlaceOnMotherClicked()

  
  def onHelpPlaceOnMotherClicked(self):
    help_text = self.help_body.text
    if help_text == 'Help':
      self.help_body.setText('Hide help')
      self.handLModelPlaceHelpDisplay.SetOpacity(0.5)
      self.handRModelPlaceHelpDisplay.SetOpacity(0.5)
      self.thumbLModelPlaceHelpDisplay.SetOpacity(0.5)
      self.thumbRModelPlaceHelpDisplay.SetOpacity(0.5)
      self.babyHeadModelPlaceHelpDisplay.SetOpacity(0.5)
      self.babyBodyModelPlaceHelpDisplay.SetOpacity(0.5)
    else:
      self.help_body.setText('Help')
      self.handLModelPlaceHelpDisplay.SetOpacity(0)
      self.handRModelPlaceHelpDisplay.SetOpacity(0)
      self.thumbLModelPlaceHelpDisplay.SetOpacity(0)
      self.thumbRModelPlaceHelpDisplay.SetOpacity(0)
      self.babyHeadModelPlaceHelpDisplay.SetOpacity(0)
      self.babyBodyModelPlaceHelpDisplay.SetOpacity(0)



  def onSaveDataButtonClicked(self):
    self.logic.saveSoftwareActivity()
    # self.saveDataCollapsibleButton.collapsed = True
    print('Data saved!')

  def onResetButtonClicked(self):
    self.logic.handedness = 'right' #by default right-handed
    self.logic.userName = 'NoName'
    self.userName_textInput.text = ''
    self.logic.recordedActivity_action = list()
    self.logic.recordedActivity_timeStamp = list()
    self.logic.recordedActivity_result = list()
    self.rightHandedRadioButton.checked = True
    self.leftHandedRadioButton.checked = False

    # Reset buttons
    self.onRetryDeflexionClicked()
    self.onNextDeflexionClicked()

    self.onRetryHoldClicked()
    self.onNextHoldClicked

    self.onRetryProtectClicked()
    self.onNextProtectClicked()
    
    self.onRetryProtect2Clicked()
    self.onNextProtect2Clicked()

    self.onRetryBodyClicked()
    self.onNextBodyClicked()

    self.onRetryPlaceOnMotherClicked()
    self.onNextPlaceOnMotherClicked()

    self.step1CollapsibleButton.collapsed = False
    self.deflexionGroupBox.collapsed = False
    self.step2CollapsibleButton.collapsed = True
    self.holdGroupBox.collapsed = True
    self.placeOnMotherGroupBox.collapsed = True
    self.ascentGroupBox.collapsed = True

    # Apply original transforms
    self.onApplyTransformsButtonClicked()

    # Uncollapse configuration
    self.configurationCollapsibleButton.collapsed = False

    # Collapse save data
    self.saveDataCollapsibleButton.collapsed = True

    print('New user')



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

  #POSITION AND STATION

  def onPositionSelectionClicked(self):
    self.pos1 = self.position1Selector.currentText
    self.pos2 = self.position2Selector.currentText
    self.positionText.setStyleSheet('font-size: 14px; font-weight: bold;')
    if (self.pos1 == 'Direct' and self.pos2 == 'Transverse') or (self.pos1 == ' ' or self.pos2 == ' '):
      self.positionText.setStyleSheet('font-size: 14px; font-weight: bold; background-color: red;')
      self.result_position.setText('Position is not valid')
      print(self.pos1 + ' Occiput ' + self.pos2 +' is not a valid position')
    else:
      #self.logic.buildTransformTree('BabyHeadModelToBabyHead')
      self.logic.buildTransformTree('MotherModelToMother')
      self.occiputFiducials = slicer.mrmlScene.GetFirstNodeByName('OcciputFiducials')
      realPos1, realPos2 = self.logic.checkPosition(self.occiputFiducials) #Returns the actual position
      self.onApplyTransformsButtonClicked()
      if self.pos1 == realPos1 and self.pos2 == realPos2:
        self.result_position.setText('Correct! The position is ' + self.pos1 + ' Occiput ' + self.pos2)
        #self.logic.recordSoftwareActivity('Position','Correct! The position is ' + self.pos1 + ' Occiput ' + self.pos2)
      else:
        self.result_position.setText('Incorrect! The position is not ' + self.pos1 + ' Occiput ' + self.pos2 )
        #self.logic.recordSoftwareActivity('Position','Incorrect! The position is not ' + self.pos1 + ' Occiput ' + self.pos2 + '. It is ' + realPos1 + ' Occiput '  + realPos2)

      

  def onStationSelectionClicked(self):
    self.station = self.stationSelector.currentText
    self.stationText.setStyleSheet('font-size: 14px; font-weight: bold;')
    if self.station == ' ':
      self.stationText.setStyleSheet('font-size: 14px; font-weight: bold; background-color: red;')
      self.result_station.setText('Station is not valid')
      print('Choose a valid station')
    else:
      realStation,accurateStation = self.logic.checkStation() #Returns the actual station
      if self.station == realStation:
        self.result_station.setText('Correct!')
        #self.logic.recordSoftwareActivity('Station','Correct (' + realStation + ')')
      else:
        self.result_station.setText('Incorrect!')
        #self.logic.recordSoftwareActivity('Station','Incorrect. It is ' + realStation + ' and not ' + self.station)


  def onHelpPositionClicked(self):
    if self.help_position.text == 'Help':
      self.help_position.setText('Hide Help')
      if slicer.mrmlScene.GetFirstNodeByName('VerticalPlane'): 
        verticalPlane = slicer.mrmlScene.GetFirstNodeByName('VerticalPlane')
        slicer.mrmlScene.RemoveNode(verticalPlane)

      # Create again vertical plane in actual position
      # origin = [0]*4
      # self.occiputFiducials.GetNthFiducialWorldCoordinates(0,origin)
      # p2 = [0]*4
      # self.occiputFiducials.GetNthFiducialWorldCoordinates(1,p2)
      # p3 = [0]*4
      # self.occiputFiducials.GetNthFiducialWorldCoordinates(2,p3)
      # Transform poly data from baby head
      babyPoints = self.logic.transformPolyData('BabyHead') 
      # Get center model center of mass
      centerMass = vtk.vtkCenterOfMass()
      centerMass.SetInputData(babyPoints)
      # centerMass.SetUseScalarsAsWeights(False)
      centerMass.Update()
      origin = centerMass.GetCenter()
      self.logic.drawPlane(origin,[1,0,0],'Vertical','BabyHead',50) #draw vertical plane
      # self.logic.drawPlane(origin,self.logic.findPlaneNormal(origin,p2,p3),'Baby','BabyHead',50) #draw baby plane passing through occiput
      verticalPlane = slicer.mrmlScene.GetFirstNodeByName('VerticalPlane')
      verticalPlane.GetModelDisplayNode().SetOpacity(0.5)
      verticalPlane.GetModelDisplayNode().SetColor([0,0,1])
      babyPlane = slicer.mrmlScene.GetFirstNodeByName('BabyPlane')
      babyPlane.GetModelDisplayNode().SetOpacity(0.5)
      babyPlane.GetModelDisplayNode().SetColor([0, 0, 1])
    else:
      self.help_position.setText('Help')
      verticalPlane = slicer.mrmlScene.GetFirstNodeByName('VerticalPlane')
      slicer.mrmlScene.RemoveNode(verticalPlane)
      babyPlane = slicer.mrmlScene.GetFirstNodeByName('BabyPlane')
      babyPlane.GetModelDisplayNode().SetOpacity(0)
    # #Changes to the correct solution
    # realPos1, realPos2 = self.logic.checkPosition(self.occiputFiducials) #Returns the actual position
    # self.position1Selector.setCurrentText(realPos1)
    # self.position2Selector.setCurrentText(realPos2)
  
  def onHelpStationClicked(self):
    if self.help_station.text == 'Help':
      self.help_station.setText('Hide Help')
      self.ischialPlane.GetModelDisplayNode().SetOpacity(0.5)
      realStation,accurateStation = self.logic.checkStation()
      
      self.addWatchedNode(wd, None, warningMessage = str(realStation), playSound = False)

    else:
      self.help_station.setText('Help')
      self.ischialPlane.GetModelDisplayNode().SetOpacity(0)
    
    # show continuously the current station
    
    # # Changes to correct solution
    # realStation = self.logic.checkStation() #Returns the actual position
    # self.stationSelector.setCurrentText(realStation)

  def onShowAnswersButtonClicked(self):
    realStation,accurateStation = self.logic.checkStation() #Returns the actual station
    self.logic.buildTransformTree('MotherModelToMother')
    self.occiputFiducials = slicer.mrmlScene.GetFirstNodeByName('OcciputFiducials')
    realPos1, realPos2 = self.logic.checkPosition(self.occiputFiducials) #Returns the actual position
    self.onApplyTransformsButtonClicked()

    if accurateStation:
      self.result_station.setText('The correct station is ' + realStation + ' and it is ' + accurateStation)
    else:
      self.result_station.setText('The correct station is ' + realStation)
    self.result_position.setText('The correct position is ' + realPos1 + ' Occiput ' + realPos2)

  def onSaveAnswerButtonClicked(self):
    self.pos1 = self.position1Selector.currentText
    self.pos2 = self.position2Selector.currentText
    realStation,accurateStation = self.logic.checkStation()
    self.station = self.stationSelector.currentText
    self.logic.buildTransformTree('MotherModelToMother')
    self.occiputFiducials = slicer.mrmlScene.GetFirstNodeByName('OcciputFiducials')
    self.realPos1, self.realPos2 = self.logic.checkPosition(self.occiputFiducials) #Returns the actual position
    self.onApplyTransformsButtonClicked()
    
    self.logic.recordSoftwareActivity('Position',self.pos1 + ' Occiput ' + self.pos2, self.realPos1 + ' Occiput '  + self.realPos2 )
    self.logic.recordSoftwareActivity('Station', self.station, realStation)

    print('Data Saved!')
  
    # if accurateStation:
    #   #self.logic.recordSoftwareActivity('Station','Correct (' + realStation + ')')
    #   self.logic.recordSoftwareActivity('Station', realStation + ',' + realStation)
    #   print('Station', realStation + ',' + realStation)
    # else:
    #   #self.logic.recordSoftwareActivity('Station','Incorrect. The real station is(' + realStation + ') And not ('+ accurateStation+')')
    #   self.logic.recordSoftwareActivity('Station',accurateStation + ',' +  realStation )

    #self.logic.recordSoftwareActivity('Position',' Position guessed: ' + self.pos1 + ' Occiput ' + self.pos2 + '. Real Position ' + self.realPos1 + ' Occiput '  + self.realPos2 )


  
  def addActionObserver(self, toolToReferenceName):
    toolToReference = slicer.util.getNode(toolToReferenceName)
    if self.callbackObserverTag == -1:
      self.observerTag = toolToReference.AddObserver('ModifiedEvent', self.callbackFunction)
      logging.info('addObserver')
  

  def removeActionObserver(self, toolToReferenceName):
    toolToReference = slicer.util.getNode(toolToReferenceName)
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
    if self.start_deflexion.text == 'Stop':
      margin = 30 + self.errorMargin
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkDeflexion(margin,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
          
    elif self.start_protect.text == 'Stop':
      margin = 5 + self.errorMargin
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkProtect(margin,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_hold.text == 'Stop':
      margin1 = 20 + self.errorMargin
      margin2 = 20 # At least 2 cm away from mother
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkHold(margin1,margin2,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
      
    elif self.start_protect2.text == 'Stop':
      margin = 5 + self.errorMargin
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkProtect(margin,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_body.text == 'Stop':
      margin1 = 20 + self.errorMargin
      margin2 = 10
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkBody(margin1,margin2,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)

    elif self.start_placeOnMother.text == 'Stop':
      margin1 = 20 + self.errorMargin
      margin2 = 10 
      if self.rightHandedRadioButton.isChecked():
        handedness = 'R'
      else:
        handedness = 'L'
      res, message = self.logic.checkPlaceOnMother(margin1,margin2,handedness)
      if res:
        self.displayCornerAnnotation(True, message)
      else:
        self.displayCornerAnnotation(False, message)
    
    

#
# Spontaneous_NavigationLogic
#

class Spontaneous_NavigationLogic(ScriptedLoadableModuleLogic):
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

    self.handedness = 'right' #by default right-handed
    self.userName = 'NoName'
    self.recordedActivity_action = list()
    self.recordedActivity_timeStamp = list()
    self.recordedActivity_result = list()
    self.recordedActivity_correct = list()
  

    # Recording Path
    self.DeliveryTrainingPath_record = slicer.modules.spontaneous_navigation.path.replace("Spontaneous_Navigation.py","") + 'Resources/Record/'

  def checkPosition(self,occiputFiducials):
    reference_vector = [0,1] #vectical vector
    posterior_pos = [0]*4 #position of the posterior fontanelle (occiput) -> occiputFiducials[0]
    anterior_pos = [0]*4 #position of the anterior fontanelle -> occiputFiducials[1]
    occiputFiducials = slicer.util.getNode('OcciputFiducials')
    occiputFiducials.GetNthFiducialWorldCoordinates(0,posterior_pos)
    occiputFiducials.GetNthFiducialWorldCoordinates(1,anterior_pos)
    vector = [posterior_pos[0] - anterior_pos[0], posterior_pos[2] - anterior_pos[2]] #vector from anterior fontanelle to occiput in RS (drop anterior-posterior)
    vector_unit = vector / np.linalg.norm(vector)
    reference_vector_unit = reference_vector / np.linalg.norm(reference_vector)
    angle = np.degrees(np.arccos(np.clip(np.dot(reference_vector_unit,vector_unit), -1.0, 1.0)))
    print(vector)
    print(angle)
    if (0 <= angle < 22.5):
      realPos1 = 'Direct'
      realPos2 = 'Anterior'
    elif (22.5 <= angle < 67.5):
      if vector[0] <= 0:
        realPos1 = 'Left'
      else:
        realPos1 = 'Right'
      realPos2 = 'Anterior'
    elif (67.5 <= angle < 112.5):
      if vector[0] <= 0:
        realPos1 = 'Left'
      else:
        realPos1 = 'Right'
      realPos2 = 'Transverse'
    elif (112.5 <= angle < 157.5):
      if vector[0] <= 0:
        realPos1 = 'Left'
      else:
        realPos1 = 'Right'
      realPos2 = 'Posterior'
    elif (157.5 <= angle <= 180):
      realPos1 = 'Direct'
      realPos2 = 'Posterior'

    # realPos1 = 'Direct'
    # realPos2 = 'Anterior'
    return realPos1, realPos2
  
  
  
  def drawPlane(self,origin, normal, name, modelName, padding):
    scene = slicer.mrmlScene
    #create a plane to cut,here it cuts in the XZ direction (xz normal=(1,0,0);XY =(0,0,1),YZ =(0,1,0)
    planex = vtk.vtkPlane()
    planex.SetOrigin(origin[0], origin[1], origin[2])
    planex.SetNormal(normal[0], normal[1], normal[2])
    #renderer = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow().GetRenderers().GetFirstRenderer()
    #viewSize = renderer.ComputeVisiblePropBounds()
    planexSample = vtk.vtkSampleFunction()
    planexSample.SetImplicitFunction(planex)
    bounds = [0] * 6
    model = slicer.util.getNode(modelName + 'Model')
    model.GetRASBounds(bounds) # VTK style [xMin, xMax, yMin, yMax, zMin, zMax]
    boundsArray = np.array(bounds)
    # Add padding
    boundsArray[::2] = boundsArray[::2] - padding  # Get odd indexes (min)
    boundsArray[1::2] = boundsArray[1::2] + padding # Get even indexes (max)
    planexSample.SetModelBounds(boundsArray)
    planexSample.ComputeNormalsOff()
    plane1 = vtk.vtkContourFilter()
    plane1.SetInputConnection(planexSample.GetOutputPort())
    # Create model Plane A node
    planeA = slicer.vtkMRMLModelNode()
    planeA.SetScene(scene)
    planeA.SetName(name + "Plane")
    planeA.SetAndObservePolyData(plane1.GetOutput())
    # Create display model Plane A node
    planeAModelDisplay = slicer.vtkMRMLModelDisplayNode()
    planeAModelDisplay.SetColor(0, 0, 1)
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
    #threeDView.resetFocalPoint()

  def findPlaneNormal(self,point1, point2, point3):
    vect1 = np.array(point1[:3]) - np.array(point2[:3])
    vect2 = np.array(point3[:3]) - np.array(point2[:3])
    normal = np.cross(vect1,vect2)
    normal_unit = normal /np.linalg.norm(normal)
    return normal_unit



  def checkStation(self):
    intersection3 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_3')
    if intersection3 == True:
      realStation = '+3'
      accurateStation = None
      return realStation, accurateStation

    intersection2 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_2')
    if intersection2 == True:
      realStation = '+2'
      intersection25 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_25')
      if intersection25 == True:
        accurateStation = 'closer to +3'
      else:
        accurateStation = 'closer to +2'
      return realStation, accurateStation
    
    intersection1 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_1')
    if intersection1 == True:
      realStation = '+1'
      intersection15 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_15')
      if intersection15 == True:
        accurateStation = 'closer to +2'
      else:
        accurateStation = 'closer to +1'
      return realStation, accurateStation

    intersection0 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane')
    if intersection0 == True:
      realStation = '+0'
      intersection05 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_05')
      if intersection05 == True:
        accurateStation = 'closer to +1'
      else:
        accurateStation = 'closer to 0'
      return realStation, accurateStation
    
 
    intersection_1 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-1')
    if intersection_1 == True:
      realStation = '-1'
      intersection_05 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-05')
      if intersection_05 == True:
        accurateStation = 'closer to 0'
      else:
        accurateStation = 'closer to -1'
      return realStation, accurateStation

    
    intersection_2 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-2')
    if intersection_2 == True:
      realStation = '-2'
      intersection_15 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-15')
      if intersection_15 == True:
        accurateStation = 'closer to -1'
      else:
        accurateStation = 'closer to -2'
      return realStation, accurateStation

    realStation = '-3'
    intersection_25 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-25')
    if intersection_25 == True:
      accurateStation = 'closer to -2'
    else:
      accurateStation = 'closer to -3'
    return realStation, accurateStation

    
    

  # def checkStation(self):
  #   # intersection_3 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-3')
  #   intersection_2 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-2')
  #   intersection_1 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-1')
  #   # intersection0 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane')
  #   intersection1 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_1')
  #   intersection2 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_2')
  #   # intersection3 = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_3')
  #   intersectionMiddle = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_middle')
  #   intersecion_middle = self.checkIntersection('BabyHead', 'Mother', 'IschialPlane_-middle')

  #   # print(intersection3)
  #   print(intersection2)
  #   print(intersection1)
  #   print(intersectionMiddle)
  #   # print(intersection0)
  #   print(intersecion_middle)
  #   print(intersection_1)
  #   print(intersection_2)
  #   # print(intersection_3)
    
  #   if intersection2 == True:
  #     realStation = '+3'
  #   elif intersection1 == True:
  #     realStation = '+2'
  #   elif intersectionMiddle == True:
  #     realStation = '+1'
  #   elif intersecion_middle == True:
  #     realStation = '0'
  #   elif intersection_1 == True:
  #     realStation = '-1'
  #   elif intersection_2 == True:
  #     realStation = '-2'
  #   else:
  #     realStation = '-3'
  #   return realStation


  def transformPolyData(self,model1Name):
    model1ToTracker = slicer.util.getNode(model1Name + 'ToTracker')
    model1ModelToModel1 = slicer.util.getNode(model1Name + 'ModelTo' + model1Name[0].capitalize() + model1Name[1:])

    # VTK matrices to work
    model1ToTrackerMatrix = vtk.vtkMatrix4x4()
    model1ModelToModel1Matrix = vtk.vtkMatrix4x4()

    # Concatenated transforms
    totalModel1 = vtk.vtkMatrix4x4()

    model1ToTracker.GetMatrixTransformToParent(model1ToTrackerMatrix)
    model1ModelToModel1.GetMatrixTransformToParent(model1ModelToModel1Matrix)

    # Multiply transforms
    # Multiply4x4(First transform, second tranform, output)
    vtk.vtkMatrix4x4.Multiply4x4(model1ToTrackerMatrix, model1ModelToModel1Matrix, totalModel1)

    # VTK transform to tranform Poly data from models
    tModel1 = vtk.vtkTransform()

    # Set total transforms that are going to be applied to Poly data (same transforms that are applied to models)
    tModel1.SetMatrix(totalModel1)
    # Transform filters for Poly data
    transformFilterModel1 = vtk.vtkTransformPolyDataFilter()

    input1 = slicer.util.getNode(model1Name + 'Model').GetPolyData()
    # Set Poly data as input
    transformFilterModel1.SetInputData(input1)

    transformFilterModel1.SetTransform(tModel1)

    # Update filters
    transformFilterModel1.Update()

    # Get outputs (transformed poly data)
    input1 = transformFilterModel1.GetOutput()

    return input1


  def checkIntersection(self, model1Name, model2Name, planeName):
    import vtkSlicerRtCommonPython  # SlicerRT must be installed
    # If one of the models to be checked is a plane:
    # Write the name of the plane in the planeName variable and the model name of the corresponding transforms
    # E.g. ishcialPlane model is transformed by motherToTracker and motherModeltoMother -> self.checkIntersection('BabyHead', 'Mother', 'IschialPlane')
    tic = time.time()
    # Load corresponding transforms
    model1ToTracker = slicer.util.getNode(model1Name + 'ToTracker')
    model2ToTracker = slicer.util.getNode(model2Name + 'ToTracker')
    model1ModelToModel1 = slicer.util.getNode(model1Name + 'ModelTo' + model1Name[0].capitalize() + model1Name[1:])
    model2ModelToModel2 = slicer.util.getNode(model2Name + 'ModelTo' + model2Name[0].capitalize() + model2Name[1:])
    toc = time.time()
    # VTK matrices to work
    model1ToTrackerMatrix = vtk.vtkMatrix4x4()
    model1ModelToModel1Matrix = vtk.vtkMatrix4x4()
    model2ToTrackerMatrix = vtk.vtkMatrix4x4()
    model2ModelToModel2Matrix = vtk.vtkMatrix4x4()
    # Concatenated transforms
    totalModel1 = vtk.vtkMatrix4x4()
    totalModel2 = vtk.vtkMatrix4x4()

    model1ToTracker.GetMatrixTransformToParent(model1ToTrackerMatrix)
    model1ModelToModel1.GetMatrixTransformToParent(model1ModelToModel1Matrix)
    model2ToTracker.GetMatrixTransformToParent(model2ToTrackerMatrix)
    model2ModelToModel2.GetMatrixTransformToParent(model2ModelToModel2Matrix)

    # Multiply transforms
    # Multiply4x4(First transform, second tranform, output)
    vtk.vtkMatrix4x4.Multiply4x4(model1ToTrackerMatrix, model1ModelToModel1Matrix, totalModel1)
    vtk.vtkMatrix4x4.Multiply4x4(model2ToTrackerMatrix, model2ModelToModel2Matrix, totalModel2)

    # VTK transform to tranform Poly data from models
    tModel1 = vtk.vtkTransform()
    tModel2 = vtk.vtkTransform()

    # Set total transforms that are going to be applied to Poly data (same transforms that are applied to models)
    tModel1.SetMatrix(totalModel1)
    tModel2.SetMatrix(totalModel2)
    toc2 = time.time()
    # Transform filters for Poly data
    transformFilterModel1 = vtk.vtkTransformPolyDataFilter()
    transformFilterModel2 = vtk.vtkTransformPolyDataFilter()

    input1 = slicer.util.getNode(model1Name + 'Model').GetPolyData()
    if planeName:
      input2 = slicer.util.getNode(planeName).GetPolyData()
    else:
      input2 = slicer.util.getNode(model2Name + 'Model').GetPolyData()

    # Set Poly data as input
    transformFilterModel1.SetInputData(input1)
    transformFilterModel2.SetInputData(input2)

    transformFilterModel1.SetTransform(tModel1)
    transformFilterModel2.SetTransform(tModel2)

    # Update filters
    transformFilterModel1.Update()
    transformFilterModel2.Update()

    # Get outputs (transformed poly data)
    input1 = transformFilterModel1.GetOutput()
    input2 = transformFilterModel2.GetOutput()
    toc3 = time.time()

    #Check for intersections with collision filter (fast ~ 0.15 seconds)
    collisionDetection = vtkSlicerRtCommonPython.vtkCollisionDetectionFilter()
    collisionDetection.SetInputData(0, input1)
    collisionDetection.SetInputData(1, input2)
    matrix1 = vtk.vtkMatrix4x4()
    collisionDetection.SetMatrix(0, matrix1)
    collisionDetection.SetMatrix(1, matrix1)
    collisionDetection.SetBoxTolerance(0.0)
    collisionDetection.SetCellTolerance(0.0)
    collisionDetection.SetNumberOfCellsPerNode(2)
    collisionDetection.Update()
    # print(collisionDetection.GetNumberOfContacts())

    toc4 = time.time()

    # print('Load models ' + str(toc-tic))
    # print('VTK matrices ' + str(toc2-toc))
    # print('Transform ' + str(toc3 - toc2))
    # print('Intersection ' + str(toc4 - toc3))

    if collisionDetection.GetNumberOfContacts() > 0:
      return True  # There is intersection
    else:
      return False
    
    # # Check for intersection with boolean operations (slow ~ 4 seconds)
    # bools = vtk.vtkBooleanOperationPolyDataFilter()
    # bools.SetOperationToIntersection()
    # bools.SetInputData(0, input1)
    # bools.SetInputData(1, input2)
    # bools.Update()
    # i = bools.GetOutput()
    # print(i.GetNumberOfPoints())
    # mass = vtk.vtkMassProperties()
    # mass.SetInputData(i)
    # print(mass.GetVolume())


    
    # if i.GetNumberOfPoints() > 0:
    #   return True # There is intersection
    # else:
    #   return False


  # transform_matrix = vtk.vtkMatrix4x4()
  # transf = slicer.util.getNode('LinearTransform_3')
  # transf.GetMatrixTransformToParent(transform_matrix)

  # t = vtk.vtkTransform()
  # t.SetMatrix(transform_matrix)
  # transformFilter = vtk.vtkTransformPolyDataFilter()
  # input2 = slicer.util.getNode('horizontalPlane_4').GetPolyData()
  # transformFilter.SetInputData(input2)
  # transformFilter.SetTransform(t)
  # transformFilter.Update()
  # input2 = transformFilter.GetOutput()

  # bools = vtk.vtkBooleanOperationPolyDataFilter()
  # input1 = slicer.util.getNode('BabyHeadModel').GetPolyData()
  # bools.SetOperationToIntersection()
  # bools.SetInputData(0,input1)
  # bools.SetInputData(1,input2)
  # bools.Update()

  # i = bools.GetOutput()


  def checkProtect(self,margin,handedness): # Maneuver with dominant hand
    message = ''
    transformName = 'MotherModelToMother'
    if self.buildTransformTree(transformName):
      tipIndex = self.getCoordinates('CheckFiducialsHand'+handedness,0) #not used for 2 sensors
      tipThumb = self.getCoordinates('CheckFiducialsThumb'+handedness,0)
      referenceHand = self.getCoordinates('CheckFiducialsHand'+handedness,1)
      optimal1 = self.getCoordinates('CheckFiducialsMother',1) # Optimal position for tip of index (R) or thumb (L)
      optimal2 = self.getCoordinates('CheckFiducialsMother',2) # Optimal position for tip of thumb (R) or index (L)
      referenceMother = self.getCoordinates('CheckFiducialsMother',4)
      if handedness == 'R':
        diffIndex = np.array(optimal1) - np.array(tipIndex)
        diffThumb = np.array(optimal2) - np.array(tipThumb)
        diffReference = np.array(referenceMother) - np.array(referenceHand)
        rsIndex = np.array([diffIndex[0],diffIndex[2]]) # get R and S coordinates of difference for index
        rsThumb = np.array([diffThumb[0],diffThumb[2]])
        rsReference = np.array([diffReference[0],diffReference[2]])
        # if (np.abs(rsIndex[0]) > margin): # Index is out of margin for Right-Left axis
        #   if rsIndex[0] < 0: # Index is too much to the left
        #     message = message + 'Index finger too close\n'
        #   else:
        #     message = message + 'Index finger too open\n'
        
        # if (np.abs(rsIndex[1]) > margin): # Index is out of margin for Superior-Inferior axis
        #   if rsIndex[1] < 0: # Index is too high
        #     message = message + 'Index finger too high\n'
        #   else:
        #     message = message + 'Index finger too low\n'
        #print(str(np.abs(rsReference[1])) +  ' margin LR hand is ' + str(margin+20))
        if (np.abs(rsReference[0]) > margin+20): # Reference is out of margin for Right-Left axis
          if rsReference[0] < 0: # Reference is too much to the left
            message = message + 'Hand too much to the left\n'
          else:
            message = message + 'Hand too much to the right\n'
        #print(str(np.abs(rsReference[1])) +  ' margin hand is ' + str(margin+30))
        if (np.abs(rsReference[1]) > margin+30): # Reference is out of margin for Superior-Inferior axis
          if rsReference[1] < 0: # Reference is too high
            message = message + 'Hand too high\n'
          else:
            message = message + 'Hand too low\n'
        #print(str(np.abs(rsThumb[1])) +  ' margin thumb is ' + str(margin))
        if (np.abs(rsThumb[0]) > margin): # Thumb is out of margin for Right-Left axis
          if rsThumb[0] < 0: # Thumb is too much to the left
            message = message + 'Thumb too open\n'
          else:
            message = message + 'Thumb too close\n'
        
        if (np.abs(rsThumb[1]) > margin): # Thumb is out of margin for Superior-Inferior axis
          if rsThumb[1] < 0: # Thumb is too high
            message = message + 'Thumb too high\n'
          else:
            message = message + 'Thumb too low\n'

        # if self.checkIntersection('Mother','ThumbR',None) == False:
        #   message = message + 'Thumb is not touching the mother\n'
        
        # if self.checkIntersection('Mother','HandR',None) == False:
        #   message = message + 'Hand is not touching the mother\n'

        dist = self.getDistancePointToModel('CheckFiducialsThumbR', 0, 'Mother') 
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin+40:
          message = message + 'Thumb is not touching the mother\n'


        # dist = self.getDistancePointToModel('CheckFiducialsHandR', 0, 'Mother') 
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist > margin+20:
        #   message = message + 'Index is not touching the mother\n'

        dist = self.getDistancePointToModel('CheckFiducialsHandR', 1, 'Mother') 
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin+40:
          message = message + 'Hand is not touching the mother\n'

      
      else:
        diffIndex = np.array(optimal2) - np.array(tipIndex)
        diffThumb = np.array(optimal1) - np.array(tipThumb)
        diffReference = np.array(referenceMother) - np.array(referenceHand)
        rsIndex = np.array([diffIndex[0],diffIndex[2]]) # get R and S coordinates of difference for index
        rsThumb = np.array([diffThumb[0],diffThumb[2]])
        rsReference = np.array([diffReference[0],diffReference[2]])
        # if (np.abs(rsIndex[0]) > margin): # Index is out of margin for Right-Left axis
        #   if rsIndex[0] < 0: # Index is too much to the left
        #     message = message + 'Index finger too open\n'
        #   else:
        #     message = message + 'Index finger too close\n'
        
        # if (np.abs(rsIndex[1]) > margin): # Index is out of margin for Superior-Inferior axis
        #   if rsIndex[1] < 0: # Index is too high
        #     message = message + 'Index finger too high\n'
        #   else:
        #     message = message + 'Index finger too low\n'

        if (np.abs(rsReference[0]) > margin+20): # Reference is out of margin for Right-Left axis
          if rsReference[0] < 0: # Reference is too much to the left
            message = message + 'Hand is too much to the left\n'
          else:
            message = message + 'Hand is too much to the right\n'
        
        if (np.abs(rsReference[1]) > margin+30): # Reference is out of margin for Superior-Inferior axis
          if rsReference[1] < 0: # Reference is too high
            message = message + 'Hand too high\n'
          else:
            message = message + 'Hand too low\n'
        
        if (np.abs(rsThumb[0]) > margin): # Thumb is out of margin for Right-Left axis
          if rsThumb[0] < 0: # Thumb is too much to the left
            message = message + 'Thumb too close\n'
          else:
            message = message + 'Thumb too open\n'
        
        if (np.abs(rsThumb[1]) > margin): # Thumb is out of margin for Superior-Inferior axis
          if rsThumb[1] < 0: # Thumb is too high
            message = message + 'Thumb too high\n'
          else:
            message = message + 'Thumb too low\n'
        
        # if self.checkIntersection('Mother','ThumbL',None) == False:
        #   message = message + 'Thumb is not touching the mother\n'
        
        # if self.checkIntersection('Mother','HandL',None) == False:
        #   message = message + 'Hand is not touching the mother\n'


        dist = self.getDistancePointToModel('CheckFiducialsThumbL', 0, 'Mother') 
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin+40:
          message = message + 'Thumb is not touching the mother\n'


        # dist = self.getDistancePointToModel('CheckFiducialsHandL', 0, 'Mother') 
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist > margin+20:
        #   message = message + 'Index is not touching the mother\n'


        dist = self.getDistancePointToModel('CheckFiducialsHandL', 1, 'Mother') 
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin+40:
          message = message + 'Hand is not touching the mother\n'

      if message == '': # No errors detected
        return True, message
      else:
        return False, message


  def checkDeflexion(self,margin,handedness): # With non-dominant hand
    message = ''
    transformName = 'BabyHeadModelToBabyHead'
    if self.buildTransformTree(transformName):
      fidHand = self.getCoordinates('CheckFiducialsHand'+handedness,1)
      # fidOcciput = self.getCoordinates('OcciputFiducials',0)
      fidMother = self.getCoordinates('CheckFiducialsMother',3)
      if handedness == 'R':
        # if self.checkIntersection('BabyHead','ThumbL',None) == False: # Non-dominant hand
        #   message = message + 'Thumb is not touching the head\n'
        
        # if self.checkIntersection('BabyHead','HandL',None) == False:
        #   message = message + 'Index is not touching the head\n'

        dist = self.getDistancePointToModel('CheckFiducialsThumbL', 0, 'BabyHead') # Non-dominant hand
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin:
          message = message + 'Hand is not touching the head\n'
        
        # dist = self.getDistancePointToModel('CheckFiducialsHandL', 0, 'BabyHead')
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist > margin:
        #   message = message + 'Index is not touching the head\n'


        # if (fidHand[2] - fidOcciput[2] > margin): # Measure difference in superior-inferior axis
        #   message = message + 'Hand too high\n'
        if (fidMother[2] < fidHand[2] ): # Measure difference in superior-inferior axis
          message = message + 'Hand too high\n'

      else:
        # if self.checkIntersection('BabyHead','ThumbR',None) == False: # Non-dominant hand
        #   message = message + 'Thumb is not touching the head\n'
        
        # if self.checkIntersection('BabyHead','HandR',None) == False:
        #   message = message + 'Index is not touching the head\n'
        
        dist = self.getDistancePointToModel('CheckFiducialsThumbR', 0, 'BabyHead') # Non-dominant hand
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin:
          message = message + 'Thumb is not touching the head\n'
        
        dist = self.getDistancePointToModel('CheckFiducialsHandR', 0, 'BabyHead')
        if dist == None:
          print('Error: No intersections found')
          message = message + ' '
        elif dist > margin:
          message = message + 'Index is not touching the head\n'

        if (fidHand[2] - fidOcciput[2] > margin): 
          message = message + 'Hand too high\n'
      
      if message == '': # No errors detected
        return True, message
      else:
        return False, message


  def checkHold(self,margin1,margin2,handedness): # With non-dominant hand
    message = ''
    transformName = 'MotherModelToMother'
    if self.buildTransformTree(transformName):
      if handedness == 'R':
        if self.checkIntersection('BabyHead','HandL',None) == False: # Non-dominat and must be in contact with the head
          message = message + 'Hand is not touching the head\n'

        # dist = self.getDistancePointToModel('CheckFiducialsHandL', 1, 'BabyHead') # Non-dominat and must be in contact with the head
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist > margin1:
        #   print(dist)
        #   message = message + 'Hand is not touching the head\n'

        # With intersection of models
        if self.checkIntersection('Mother','HandR',None) == True: # Dominant hand must be removed from perineum (i.e. do not touch mother)
          message = message + 'Remove hand from mother\n'
        
        # # With distances
        # dist = self.getDistancePointToModel('CheckFiducialsHandR',1,'Mother') # Dominant hand must be removed from perineum
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist < margin2:
        #   message = message + 'Remove hand from mother\n'

        # print(dist)

      else:
        if self.checkIntersection('BabyHead','HandR',None) == False:
          message = message + 'Hand is not touching the head\n'

        # dist = self.getDistancePointToModel('CheckFiducialsHandR', 1, 'BabyHead') # Non-dominat and must be in contact with the head
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist > margin1:
        #   message = message + 'Hand is not touching the head\n'

        if self.checkIntersection('Mother','HandL',None) == True: 
          message = message + 'Remove hand from mother\n'

        # dist = self.getDistancePointToModel('CheckFiducialsHandL',1,'Mother')
        # if dist == None:
        #   print('Error: No intersections found')
        #   message = message + ' '
        # elif dist < margin2:
        #   message = message + 'Remove hand from mother\n'

      if message == '': # No errors detected
        return True, message
      else:
        return False, message

  
  def checkBody(self,margin1,margin2,handedness):
    message = ''
    # handL = slicer.mrmlScene.GetFirstNodeByName('HandLModel')
    # handR = slicer.mrmlScene.GetFirstNodeByName('HandRModel')
    # thumbL = slicer.mrmlScene.GetFirstNodeByName('ThumbLModel')
    # thumbR = slicer.mrmlScene.GetFirstNodeByName('ThumbRModel')

    if self.checkIntersection('BabyBody','ThumbL',None) == False:
      message = message + 'Left hand is not touching the body\n'
    if self.checkIntersection('BabyBody','ThumbR',None) == False:
      message = message + 'Right hand is not touching the body\n'
    if self.checkIntersection('BabyHead','ThumbR',None) == True:
      message = message + 'Right hand must not touch the head\n'
    if self.checkIntersection('BabyHead','ThumbL',None) == True:
      message = message + 'Left hand must not touch the head\n'


    # dist = self.getDistancePointToModel('CheckFiducialsHandR',1,'BabyBody') # Grab baby by the body
    # if dist == None:
    #   print('Error: No intersections found')
    #   message = message + ' '
    # elif dist > margin1:
    #   message = message + 'Right hand is not touching the body\n'

    
    # dist = self.getDistancePointToModel('CheckFiducialsHandL',1,'BabyBody') # Grab baby by the body
    # if dist == None:
    #   print('Error: No intersections found')
    #   message = message + ' '
    # elif dist > margin1:
    #   message = message + 'Left hand is not touching the body\n'


    # dist = self.getDistancePointToModel('CheckFiducialsThumbL',0,'BabyHead') # Do not grab the baby from the head
    # if dist == None:
    #   print('Error: No intersections found')
    #   message = message + ' '
    # elif dist < margin2:
    #   message = message + 'Left hand must not touch the head\n'

    
    # dist = self.getDistancePointToModel('CheckFiducialsThumbR',0,'BabyHead') # Do not grab the baby from the head
    # if dist == None:
    #   print('Error: No intersections found')
    #   message = message + ' '
    # elif dist < margin2:
    #   message = message + 'Right hand must not touch the head\n'

    
    if message == '': # No errors detected
        return True, message
    else:
        return False, message


  def checkPlaceOnMother(self,margin1,margin2,handedness):
    message = ''

    if self.checkIntersection('BabyBody','ThumbL',None) == True:
      message = message + 'Left hand must not touch the baby\n'
    if self.checkIntersection('BabyBody','ThumbR',None) == True:
      message = message + 'Right hand must not touch the baby\n'
    if self.checkIntersection('BabyBody','Mother',None) == False and self.checkIntersection('BabyBody','MotherTummy',None) == False:
      message = message + 'Baby must be in contact with mother\n'

    if message == '': # No errors detected
        return True, message
    else:
        return False, message


  def getCoordinates(self,fidsName,position):
    fids = slicer.mrmlScene.GetFirstNodeByName(fidsName)
    coor = [0]*4
    fids.GetNthFiducialWorldCoordinates(position,coor)
    return coor[:3]


  def getDistancePointToModel(self, fidsName, position, modelName):
    point = self.getCoordinates(fidsName,position)
    model = slicer.mrmlScene.GetFirstNodeByName(modelName+'Model')
    closestPoint = self.lineModelIntersection(point,model)
    if closestPoint == []:
      dist = None
    else:
      dist = np.linalg.norm(np.subtract(point,closestPoint))
    return dist

  
  def lineModelIntersection(self, endPoint, model):

    startPoint = [0,0,0]

    mesh = model.GetPolyData()

    obbTree = vtk.vtkOBBTree()
    obbTree.SetDataSet(mesh)
    obbTree.BuildLocator()

    pointsVTKintersection = vtk.vtkPoints()
    code = obbTree.IntersectWithLine(startPoint, endPoint, pointsVTKintersection, None)
    
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
      dif = np.subtract(endPoint,pointsIntersection_array[i])
      norm = np.linalg.norm(dif)
      diferences_array_norms = np.append(diferences_array_norms, norm)
      
    #print diferences_array_norms
    closest_insertion_point = []
    if number_pointsIntersection>0:
      closest_insertion_point = pointsIntersection_array[diferences_array_norms.argmin(axis=0)]

    return closest_insertion_point
    
    
      



  def saveData(self,node_name,path,file_name):
    node = slicer.util.getNode(node_name)
    file_path = os.path.join(path,file_name)
    return slicer.util.saveNode(node,file_path)



  def recordSoftwareActivity(self, actionName, result, correct):
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

    # Store correct result
    self.recordedActivity_correct.append(correct)

    # self.saveTransform('HandLToTracker', actionName, path)
    # self.saveTransform('ThumbLToTracker', actionName, path)
    # self.saveTransform('HandRToTracker', actionName, path)
    # self.saveTransform('ThumbRToTracker', actionName, path)
    self.saveTransform('MotherToTracker', actionName, path)
    self.saveTransform('BabyHeadToTracker', actionName, path)
    self.saveTransform('BabyHeadToTracker', actionName, path)


  
  def saveTransform(self, node_name, actionName, path):
    # Save transform
    node = slicer.util.getNode(node_name)
    if node:
      file_name = node_name + '_' + actionName + '_' + self.userName + '_' + time.strftime("_%Y-%m-%d_%H-%M-%S") + '.h5'
      self.saveData(node_name, path, file_name)
    else:
      print('Could not save, unable to find ' + node_name)

  

  def saveSoftwareActivity(self):

    dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")
    csvFilePath = self.DeliveryTrainingPath_record + 'RecordedActivity_' + self.userName + '_' + dateAndTime + '.csv'
        
    with open(csvFilePath, 'w') as csvfile: # Changed 'wb' to 'w'
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([ 'action', 'result', 'correct','timestamp'])

        timestamp_array = np.array(self.recordedActivity_timeStamp) 
        action_array = np.array(self.recordedActivity_action)
        result_array = np.array(self.recordedActivity_result)
        correct_array = np.array(self.recordedActivity_correct)
      
        for i in range(timestamp_array.shape[0]):
            vector = np.array([action_array[i], result_array[i], correct_array[i], timestamp_array[i]]) 
            writer.writerow(vector) 

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
      # try:
      #   handLToTracker = slicer.util.getNode('HandLToTracker')
      # except:
      #   print('HandLToTracker not found')
      #   return False
      # try:
      #   handRToTracker = slicer.util.getNode('HandRToTracker')
      # except:
      #   print('HandRToTracker not found')
      #   return False
      # try:
      #   thumbLToTracker = slicer.util.getNode('ThumbLToTracker')
      # except:
      #   print('ThumbLToTracker not found')
      #   return False
      # try:
      #   thumbRToTracker = slicer.util.getNode('ThumbRToTracker')
      # except:
      #   print('ThumbRToTracker not found')
      #   return False
      try:
        babyHeadToTracker = slicer.util.getNode('BabyHeadToTracker')
      except:
        print('BabyHeadToTracker not found')
        return False
      try:
        babyBodyToTracker = slicer.util.getNode('BabyBodyToTracker')
      except:
        print('BabyHeadToTracker not found')
        return False
      try:
        motherToTracker = slicer.util.getNode('MotherToTracker')
      except:
        print('MotherToTracker not found')
        return False
      # get the trackerToTool transform for the ToolModelToTool transform
      fidsName = []
      if transformName == 'BabyHeadModelToBabyHead':
        trackerTransformName_inv = 'TrackerToBabyHead'
        fidsName = ['OcciputFiducials']
        modelName = ['BabyHeadModel', 'HandLModelHoldHelpL', 'ThumbLModelHoldHelpL','HandLModelHoldHelpR','ThumbLModelDeflexionHelp','HandLModelDeflexionHelp',
                     'ThumbLModelHoldHelpR', 'HandRModelHoldHelpL', 'ThumbRModelHoldHelpL', 'HandRModelHoldHelpR', 'ThumbRModelHoldHelpR', 'HandRModelDeflexionHelp',
                     'ThumbRModelDeflexionHelp']
      elif transformName == 'BabyBodyModelToBabyBody':
        trackerTransformName_inv = 'TrackerToBabyHead'
        modelName = ['BabyBodyModel', 'ThumbRModelGrabHelp', 'HandRModelGrabHelp', 'ThumbLModelGrabHelp', 'HandLModelGrabHelp']
      elif transformName == 'MotherModelToMother':
        trackerTransformName_inv = 'TrackerToMother'
        modelName = ['MotherModel', 'MotherTummyModel', 'IschialPlane', 'motherRealisticModel', 'sacrumLeftModel', 'sacrumRightModel',
                     'middlePelvisModel', 'coxisLeftModel', 'coxisRightModel', 'leftPelvis3Model', 'leftPelvis2Model', 'leftPelvis1Model', 'rightPelvis3Model',
                     'rightPelvis2Model', 'rightPelvis1Model', 'FrontCameraToMother', 'SideCameraToMother', 'UpCameraToMother', 'IschialPlane_1',
                     'IschialPlane_-1', 'IschialPlane_2', 'IschialPlane_-2', 'IschialPlane_3', 'IschialPlane_-3', 'IschialPlane_-middle',
                     'IschialPlane_middle', 'Arrow1', 'Arrow2', 'Arrow3', 'Arrow4', 'ThumbRModelGuardHelp', 'HandRModelGuardHelp','ThumbLModelGuardHelp', 'HandLModelGuardHelp',
                     'IschialPlane_05', 'IschialPlane_-05', 'IschialPlane_15', 'IschialPlane_-15', 'IschialPlane_25', 'IschialPlane_-25', 'ThumbRModelPlaceHelp', 'HandRModelPlaceHelp',
                     'ThumbLModelPlaceHelp', 'HandLModelPlaceHelp', 'BabyHeadModelPlaceHelp', 'BabyBodyModelPlaceHelp']
        fidsName = ['CheckFiducialsMother']
      else:
        print('Input transform for tree not valid')
        return False
      trackerTransform_inv = slicer.util.getNode(trackerTransformName_inv)

      # # make the models observe the inverse transform from the tracker
      # if transformName != 'HandLModelToHandL':
      #   handLToTracker.SetAndObserveTransformNodeID(
      #       trackerTransform_inv.GetID())
      # if transformName != 'HandRModelToHandR':
      #   handRToTracker.SetAndObserveTransformNodeID(
      #       trackerTransform_inv.GetID())
      # if transformName != 'ThumbLModelToThumbL':
      #   thumbLToTracker.SetAndObserveTransformNodeID(
      #       trackerTransform_inv.GetID())
      # if transformName != 'ThumbRModelToThumbR':
      #   thumbRToTracker.SetAndObserveTransformNodeID(
      #       trackerTransform_inv.GetID())
      if transformName != 'BabyHeadModelToBabyHead':
        babyHeadToTracker.SetAndObserveTransformNodeID(
            trackerTransform_inv.GetID())
      if transformName != 'BabyBodyModelToBabyBody':
        babyBodyToTracker.SetAndObserveTransformNodeID(
            trackerTransform_inv.GetID())
      if transformName != 'MotherModelToMother':
        motherToTracker.SetAndObserveTransformNodeID(
            trackerTransform_inv.GetID())
      # make the inverse transform from the tracker observe the inverse transform of ToolModelToTool
      trackerTransform_inv.SetAndObserveTransformNodeID(
          transform_inverted.GetID())

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


  def invertTransform(self, transformName):
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
      transformationNode = slicer.vtkMRMLLinearTransformNode()
      transformationNode.SetName(name)
      slicer.mrmlScene.AddNode(transformationNode)
      transformationNode.SetMatrixTransformToParent(transform_matrix)
    return transformationNode
  
#
# Spontaneous_NavigationTest
#

class Spontaneous_NavigationTest(ScriptedLoadableModuleTest):
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
    self.test_Spontaneous_Navigation1()

  def test_Spontaneous_Navigation1(self):
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


    self.delayDisplay('Test passed')
