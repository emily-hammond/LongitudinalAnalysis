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
    # number of images
    #
    numberOfImagesButton = ctk.ctkCollapsibleButton()
    numberOfImagesButton.text = "Number of images"
    self.layout.addWidget(numberOfImagesButton)
    
    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(numberOfImagesButton)
    
    #
    # Number of images selector (not fully implemented!!!)
    #
    self.numberSelector = slicer.qMRMLNodeComboBox()
    self.numberSelector.nodeTypes = ["vtkMRMLSelectionNode"]
    self.numberSelector.selectNodeUponCreation = True
    self.numberSelector.addEnabled = False
    self.numberSelector.removeEnabled = False
    self.numberSelector.noneEnabled = True
    self.numberSelector.showHidden = False
    self.numberSelector.showChildNodeTypes = False
    self.numberSelector.setMRMLScene( slicer.mrmlScene )
    self.numberSelector.setToolTip( "State the number of images to compare." )
    parametersFormLayout.addRow("Number of images: ", self.numberSelector)
    self.numberOfImages = 4
    
    #
    # CSV file for results (not fully implemented!!!)
    #
    self.fileSelector = slicer.qMRMLNodeComboBox()
    self.fileSelector.nodeTypes = ["vtkMRMLAnnotationStorageNode"]
    self.fileSelector.selectNodeUponCreation = True
    self.fileSelector.addEnabled = False
    self.fileSelector.removeEnabled = False
    self.fileSelector.noneEnabled = True
    self.fileSelector.showHidden = False
    self.fileSelector.showChildNodeTypes = False
    self.fileSelector.setMRMLScene( slicer.mrmlScene )
    self.fileSelector.setToolTip( "Type the desired filename to store the results." )
    parametersFormLayout.addRow("CSV file: ", self.fileSelector)    

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
    
    # define lists to store images and transforms
    self.imageNodes = []
    self.transformNodes = []
    
    for i in xrange(1,self.numberOfImages):
        
        #
        # image Area
        #
        imageCollapsibleButton = ctk.ctkCollapsibleButton()
        imageCollapsibleButton.text = "Image set " + str(i)
        self.layout.addWidget(imageCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(imageCollapsibleButton)
        
        #
        # image2 volume selector
        #
        self.imageSelector = slicer.qMRMLNodeComboBox()
        self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.imageSelector.selectNodeUponCreation = True
        self.imageSelector.addEnabled = False
        self.imageSelector.removeEnabled = False
        self.imageSelector.noneEnabled = False
        self.imageSelector.showHidden = False
        self.imageSelector.showChildNodeTypes = False
        self.imageSelector.setMRMLScene( slicer.mrmlScene )
        self.imageSelector.setToolTip( "Pick the second image." )
        parametersFormLayout.addRow("Image: ", self.imageSelector)
        
        #
        # transform selector
        #
        self.transformSelector = slicer.qMRMLNodeComboBox()
        self.transformSelector.nodeTypes = ["vtkMRMLTransformNode","vtkMRMLLinearTransformNode"]
        self.transformSelector.selectNodeUponCreation = True
        self.transformSelector.addEnabled = False
        self.transformSelector.removeEnabled = False
        self.transformSelector.noneEnabled = False
        self.transformSelector.showHidden = False
        self.transformSelector.showChildNodeTypes = False
        self.transformSelector.setMRMLScene( slicer.mrmlScene )
        self.transformSelector.setToolTip( "Pick the transform from the image to the baseline image." )
        parametersFormLayout.addRow("Transform: ", self.transformSelector)
        
        # store node information
        self.imageNodes.append(self.imageSelector)
        self.transformNodes.append(self.transformSelector)

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
    self.resampleLabelMapsButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode()
    
  def onSelectCalculate(self):
    self.calculateStatsButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode()
    
  def onShowLayout(self):
    self.showLayoutButton.enabled = self.roiSelector.currentNode() and self.baselineSelector.currentNode()

  def onresampleLabelMapsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    for i in xrange(0,self.numberOfImages-1):
        images.append(self.imageNodes[i].currentNode())
    # gather transforms into list
    transforms = []
    for i in xrange(0,self.numberOfImages-1):
        transforms.append(self.transformNodes[i].currentNode())
    # send to logic
    logic.resampleLabelMaps(self.roiSelector.currentNode(), self.baselineSelector.currentNode(), images, transforms)

  def oncalculateStatsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    for i in xrange(0,self.numberOfImages-1):
        images.append(self.imageNodes[i].currentNode())    # send to logic
    logic.calculateStatistics(images, self.fileSelector.currentNode())
    
  def onshowLayoutButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    for i in xrange(0,self.numberOfImages-1):
        images.append(self.imageNodes[i].currentNode())
    # gather transforms into list
    transforms = []
    for i in xrange(0,self.numberOfImages-1):
        transforms.append(self.transformNodes[i].currentNode())
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

  def getLabelStats(self, image, roi, labelStats):
    # instantiate results dictionary
    labelStats["Image"].append(image.GetName())
  
    # copied/modified from labelstatistics module
    # determine volume of a voxel and conversion factor to cubed centimeters
    cubicMMPerVoxel = reduce(lambda x,y: x*y, roi.GetSpacing())
    ccPerCubicMM = 0.001
    
    # calculate the min and max of the roi image
    stataccum = vtk.vtkImageAccumulate()
    stataccum.SetInputConnection(roi.GetImageDataConnection())
    stataccum.Update()
    lo = int(stataccum.GetMin()[0])
    hi = int(stataccum.GetMax()[0])
    
    # iterate through all the labels in the image
    for i in xrange(lo,hi+1):
        # threshold roi image
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputConnection(roi.GetImageDataConnection())
        thresholder.SetInValue(1)
        thresholder.SetOutValue(0)
        thresholder.ReplaceOutOn()
        thresholder.ThresholdBetween(i,i)
        thresholder.SetOutputScalarType(image.GetImageData().GetScalarType())
        thresholder.Update()

        #  use vtk's statistics class with the binary labelmap as a stencil
        stencil = vtk.vtkImageToImageStencil()
        stencil.SetInputConnection(thresholder.GetOutputPort())
        stencil.ThresholdBetween(1, 1)
        stat1 = vtk.vtkImageAccumulate()
        stat1.SetInputConnection(image.GetImageDataConnection())
        stencil.Update()
        stat1.SetStencilData(stencil.GetOutput())
        stat1.Update()

        # gather stats if count is greater than zero
        if stat1.GetVoxelCount() > 0:
            # add an entry to the LabelStats list
            labelStats["Labels"].append(i)
            labelStats[image.GetName(),i,"Image"] = image.GetName()
            labelStats[image.GetName(),i,"Index"] = i
            labelStats[image.GetName(),i,"Count"] = stat1.GetVoxelCount()
            labelStats[image.GetName(),i,"Volume mm^3"] = labelStats[image.GetName(),i,"Count"] * cubicMMPerVoxel
            labelStats[image.GetName(),i,"Volume cc"] = labelStats[image.GetName(),i,"Volume mm^3"] * ccPerCubicMM
            labelStats[image.GetName(),i,"Min"] = stat1.GetMin()[0]
            labelStats[image.GetName(),i,"Max"] = stat1.GetMax()[0]
            labelStats[image.GetName(),i,"Mean"] = stat1.GetMean()[0]
            labelStats[image.GetName(),i,"StdDev"] = stat1.GetStandardDeviation()[0]

    return hi
       
  def resampleLabelMaps(self, roi, baseline, images, transforms):
    # perform actions on each image/transform pair
    for x in xrange(0, len(images)):
        if( images[x] != None ):
            # apply transforms and create new rois/image
            roiNew = self.applyTransform( images[x], roi, transforms[x] )
 
    return True
    
  # redo this function similar to how it is done with the labelstatistics module
  def calculateStatistics(self, images, filename):
    # initialize results list
    keys = ["Image","Index", "Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev"]
    results = {}
    results['Image'] = []
    results['Labels'] = []
  
    # iterate through all the images
    for x in range(0,len(images)):
        if( images[x] != None ):
            # pull roi from slicer
            roi = slicer.util.getNode(images[x].GetName() + '-label')
            maxLabel = self.getLabelStats(images[x], roi, results)
            
    # print out results in a nice table
    print(keys)
    for im in results['Image']:
        for label in xrange(min(results['Labels']),max(results['Labels'])+1):
            data = []
            for header in keys:
                data.append(results[im,label,header])
            print(data)
            
    # write results to file if a csv file is given
    if( filename != None ):
        with open(filename,'w') as file:
            file.write(', '.join(keys))
            file.write('\n')
            for im in results['Image']:
                for label in xrange(min(results['Labels']),max(results['Labels'])+1):
                    data = []
                    for header in keys:
                        data.append(results[im,label,header])
                    file.write(', '.join(data))
                    file.write('\n')       
    
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
