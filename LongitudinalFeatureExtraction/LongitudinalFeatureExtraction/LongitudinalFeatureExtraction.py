import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import time

#
# LongitudinalFeatureExtraction
#

class LongitudinalFeatureExtraction(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LongitudinalFeatureExtraction" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# LongitudinalFeatureExtractionWidget
#

class LongitudinalFeatureExtractionWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # baseline image Area
    #
    baselineCollapsibleButton = ctk.ctkCollapsibleButton()
    baselineCollapsibleButton.text = "Baseline image"
    self.layout.addWidget(baselineCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(baselineCollapsibleButton)

    #
    # image (original) volume selector
    #
    self.baselineSelector = slicer.qMRMLNodeComboBox()
    self.baselineSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.baselineSelector.selectNodeUponCreation = True
    self.baselineSelector.addEnabled = False
    self.baselineSelector.removeEnabled = False
    self.baselineSelector.noneEnabled = False
    self.baselineSelector.showHidden = False
    self.baselineSelector.showChildNodeTypes = False
    self.baselineSelector.setMRMLScene( slicer.mrmlScene )
    self.baselineSelector.setToolTip( "Pick the image with the original ROI." )
    parametersFormLayout.addRow("Baseline image: ", self.baselineSelector)
    
    #
    # ROI volume selector
    #
    self.roiSelector = slicer.qMRMLNodeComboBox()
    self.roiSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.roiSelector.selectNodeUponCreation = True
    self.roiSelector.addEnabled = False
    self.roiSelector.removeEnabled = False
    self.roiSelector.noneEnabled = False
    self.roiSelector.showHidden = False
    self.roiSelector.showChildNodeTypes = False
    self.roiSelector.setMRMLScene( slicer.mrmlScene )
    self.roiSelector.setToolTip( "Pick the region of interest." )
    parametersFormLayout.addRow("Region of interest (label map) ", self.roiSelector)
    
    #
    # image2 Area
    #
    image2CollapsibleButton = ctk.ctkCollapsibleButton()
    image2CollapsibleButton.text = "Image set 2"
    self.layout.addWidget(image2CollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(image2CollapsibleButton)
    
    #
    # image2 volume selector
    #
    self.image2Selector = slicer.qMRMLNodeComboBox()
    self.image2Selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.image2Selector.selectNodeUponCreation = True
    self.image2Selector.addEnabled = False
    self.image2Selector.removeEnabled = False
    self.image2Selector.noneEnabled = False
    self.image2Selector.showHidden = False
    self.image2Selector.showChildNodeTypes = False
    self.image2Selector.setMRMLScene( slicer.mrmlScene )
    self.image2Selector.setToolTip( "Pick the second image." )
    parametersFormLayout.addRow("Image 2: ", self.image2Selector)
    
    #
    # transform selector
    #
    self.transform2Selector = slicer.qMRMLNodeComboBox()
    self.transform2Selector.nodeTypes = ["vtkMRMLTransformNode","vtkMRMLLinearTransformNode"]
    self.transform2Selector.selectNodeUponCreation = True
    self.transform2Selector.addEnabled = False
    self.transform2Selector.removeEnabled = False
    self.transform2Selector.noneEnabled = False
    self.transform2Selector.showHidden = False
    self.transform2Selector.showChildNodeTypes = False
    self.transform2Selector.setMRMLScene( slicer.mrmlScene )
    self.transform2Selector.setToolTip( "Pick the transform from image2 to image 1." )
    parametersFormLayout.addRow("Transform: ", self.transform2Selector)
    
    #
    # image3 Area
    #
    image3CollapsibleButton = ctk.ctkCollapsibleButton()
    image3CollapsibleButton.text = "Image set 3"
    self.layout.addWidget(image3CollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(image3CollapsibleButton)
    
    #
    # image2 volume selector
    #
    self.image3Selector = slicer.qMRMLNodeComboBox()
    self.image3Selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.image3Selector.selectNodeUponCreation = True
    self.image3Selector.addEnabled = False
    self.image3Selector.removeEnabled = False
    self.image3Selector.noneEnabled = True
    self.image3Selector.showHidden = False
    self.image3Selector.showChildNodeTypes = False
    self.image3Selector.setMRMLScene( slicer.mrmlScene )
    self.image3Selector.setToolTip( "Pick the second image." )
    parametersFormLayout.addRow("Image 3: ", self.image3Selector)
    
    #
    # transform selector
    #
    self.transform3Selector = slicer.qMRMLNodeComboBox()
    self.transform3Selector.nodeTypes = ["vtkMRMLTransformNode","vtkMRMLLinearTransformNode"]
    self.transform3Selector.selectNodeUponCreation = True
    self.transform3Selector.addEnabled = False
    self.transform3Selector.removeEnabled = False
    self.transform3Selector.noneEnabled = True
    self.transform3Selector.showHidden = False
    self.transform3Selector.showChildNodeTypes = False
    self.transform3Selector.setMRMLScene( slicer.mrmlScene )
    self.transform3Selector.setToolTip( "Pick the transform from image2 to image 1." )
    parametersFormLayout.addRow("Transform: ", self.transform3Selector)
    
    #
    # image4 Area
    #
    image4CollapsibleButton = ctk.ctkCollapsibleButton()
    image4CollapsibleButton.text = "Image set 4"
    self.layout.addWidget(image4CollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(image4CollapsibleButton)
    
    #
    # image2 volume selector
    #
    self.image4Selector = slicer.qMRMLNodeComboBox()
    self.image4Selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.image4Selector.selectNodeUponCreation = True
    self.image4Selector.addEnabled = False
    self.image4Selector.removeEnabled = False
    self.image4Selector.noneEnabled = True
    self.image4Selector.showHidden = False
    self.image4Selector.showChildNodeTypes = False
    self.image4Selector.setMRMLScene( slicer.mrmlScene )
    self.image4Selector.setToolTip( "Pick the second image." )
    parametersFormLayout.addRow("Image 4: ", self.image4Selector)
    
    #
    # transform selector
    #
    self.transform4Selector = slicer.qMRMLNodeComboBox()
    self.transform4Selector.nodeTypes = ["vtkMRMLTransformNode","vtkMRMLLinearTransformNode"]
    self.transform4Selector.selectNodeUponCreation = True
    self.transform4Selector.addEnabled = False
    self.transform4Selector.removeEnabled = False
    self.transform4Selector.noneEnabled = True
    self.transform4Selector.showHidden = False
    self.transform4Selector.showChildNodeTypes = False
    self.transform4Selector.setMRMLScene( slicer.mrmlScene )
    self.transform4Selector.setToolTip( "Pick the transform from image2 to image 1." )
    parametersFormLayout.addRow("Transform: ", self.transform4Selector)

    #
    # Resample rois Button
    #
    self.resampleLabelMapsButton = qt.QPushButton("Resample region of interest")
    self.resampleLabelMapsButton.toolTip = "Resample the label maps to find the roi in all images in their original image space."
    self.resampleLabelMapsButton.enabled = True
    parametersFormLayout.addRow(self.resampleLabelMapsButton)

    # connections
    self.resampleLabelMapsButton.connect('clicked(bool)', self.onresampleLabelMapsButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelectResample()
    
    #
    # Calculate statistics Button
    #
    self.calculateStatsButton = qt.QPushButton("Calculate statistics")
    self.calculateStatsButton.toolTip = "Calculate statistics from each region of interest."
    self.calculateStatsButton.enabled = True
    parametersFormLayout.addRow(self.calculateStatsButton)

    # connections
    self.calculateStatsButton.connect('clicked(bool)', self.oncalculateStatsButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelectCalculate()
    
    #
    # Show layout Button
    #
    self.showLayoutButton = qt.QPushButton("Registered images layout")
    self.showLayoutButton.toolTip = "View the images in the baseline image space with transforms applied."
    self.showLayoutButton.enabled = True
    parametersFormLayout.addRow(self.showLayoutButton)

    # connections
    self.showLayoutButton.connect('clicked(bool)', self.onshowLayoutButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onShowLayout()

  def cleanup(self):
    pass

  def onSelectResample(self):
    self.resampleLabelMapsButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode() and self.image2Selector.currentNode() and self.transform2Selector.currentNode()
    
  def onSelectCalculate(self):
    self.calculateStatsButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode() and self.image2Selector.currentNode()
    
  def onShowLayout(self):
    self.showLayoutButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode() and self.image2Selector.currentNode() and self.transform2Selector.currentNode()

  def onresampleLabelMapsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = [self.image2Selector.currentNode(), self.image3Selector.currentNode(), self.image4Selector.currentNode()]
    # gather transforms into list
    transforms = [self.transform2Selector.currentNode(), self.transform3Selector.currentNode(), self.transform4Selector.currentNode()]
    # send to logic
    logic.resampleLabelMaps(self.roiSelector.currentNode(), self.baselineSelector.currentNode(), images, transforms)

  def oncalculateStatsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = [self.baselineSelector.currentNode(), self.image2Selector.currentNode(), self.image3Selector.currentNode(), self.image4Selector.currentNode()]
    # send to logic
    logic.calculateStatistics(images)
    
  def onshowLayoutButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = [self.image2Selector.currentNode(), self.image3Selector.currentNode(), self.image4Selector.currentNode()]
    # gather transforms into list
    transforms = [self.transform2Selector.currentNode(), self.transform3Selector.currentNode(), self.transform4Selector.currentNode()]
    # send to logic
    logic.showLayout(images, transforms)

#
# LongitudinalFeatureExtractionLogic
#

class LongitudinalFeatureExtractionLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True
    
  def printStatus(self, node, event):
    status = node.GetStatusString()
    print('  Apply transform ' + status)
    return
    
  def applyTransform(self, image, roi, transform):
    # create new volumes
    roiNew = slicer.vtkMRMLLabelMapVolumeNode()
    roiNew.SetName( image.GetName() + '-label')
    slicer.mrmlScene.AddNode( roiNew )
    
    # take inverse of transform
    transform.Inverse()
    
    # resample roi using inverse transform
    parameters = {}
    parameters["inputVolume"] = roi
    parameters["referenceVolume"] = image
    parameters["outputVolume"] = roiNew
    parameters["pixelType"] = "int"
    parameters["warpTransform"] = transform
    parameters["interpolationMode"] = "Linear"
    # call module
    cliNode = None
    cliNode = slicer.cli.run( slicer.modules.brainsresample, cliNode, parameters )
    print(cliNode.AddObserver('ModifiedEvent', self.printStatus))
    
    return roiNew
    
  def getLabelStats(self, image, roi):
    # find label value within label map
    findLabel = sitk.StatisticsImageFilter()
    findLabel.Execute( roi )
    label = int(findLabel.GetMaximum())
    
    # find volume of voxel
    voxelVolume = reduce(lambda x,y: x*y, image.GetSpacing())
    
    # find the image statistics within the label map
    stats = sitk.LabelStatisticsImageFilter()
    stats.Execute(image, roi)
    results = [stats.GetCount(label)*voxelVolume, stats.GetMean(label), stats.GetVariance(label),stats.GetMaximum(label),stats.GetMinimum(label)]
    
    return results
       
  def resampleLabelMaps(self, roi, baseline, images, transforms):
    # perform actions on each image/transform pair
    for x in xrange(0, len(images)):
        if( images[x] != None ):
            # apply transforms and create new rois/image
            roiNew = self.applyTransform( images[x], roi, transforms[x] )
 
    return True
    
  # redo this function similar to how it is done with the labelstatistics module
  def calculateStatistics(self, images):
    # initialize results list
    results = []
    headers = ['Volume','Mean','Variance','Maximum','Minimum']
    results.append(headers)
  
    # iterate through all the images
    for x in range(0,len(images)):
        if( images[x] != None ):
            # pull image from slicer
            image_here = sitkUtils.PullFromSlicer(images[x].GetID())

            # pull roi from slicer
            roi = slicer.util.getNode(images[x].GetName() + '-label')
            roi_here = sitkUtils.PullFromSlicer(roi.GetID())
            
            # calculate statistics
            individuals = self.getLabelStats(image_here, roi_here)
            results.append(individuals)
            
    # print out results
    for x in range(0, len(results)):
        print(results[x])

    return True
    
  def showLayout(self, images, transforms):
 
    # apply and observe transforms on appropriate images
    for x in range(0, len(images)):
        if( images[x] != None ):
            # inverse transform (undo what was done previously)
            transforms[x].Inverse()
            
            # observe transform with image
            images[x].SetAndObserveTransformNodeID( transforms[x].GetID() )
            
            # observe transform with roi
            roi = slicer.util.getNode(images[x].GetName() + '-label')
            roi.SetAndObserveTransformNodeID( transforms[x].GetID() )
    return

class LongitudinalFeatureExtractionTest(ScriptedLoadableModuleTest):
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
    #self.setUp()
    self.test_LongitudinalFeatureExtraction1()

  def test_LongitudinalFeatureExtraction1(self):
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
    logic = LongitudinalFeatureExtractionLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
