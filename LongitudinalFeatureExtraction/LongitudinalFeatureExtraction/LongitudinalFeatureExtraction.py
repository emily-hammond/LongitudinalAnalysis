import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import time
import numpy as np

#
# LongitudinalFeatureExtraction
#

class LongitudinalFeatureExtraction(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Longitudinal Feature Extraction" # TODO make this more human readable by adding spaces
    self.parent.dependencies = []
    self.parent.contributors = ["Emily Hammond (University of Iowa)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    Identify equivalent regions of interest (ROI) in a registered set of longitudinal images and calculate basic statistics from the ROIs. Inputs:  (1) Number of desired images to compare (2) New file to store the final results in (if desired) (3) Baseline image with corresponding ROI (4) Images with corresponding transforms that take each image into the baseline image space | Outputs: (1) ROIs resampled into each image space (inverse transform is applied) (2) Statistics from each ROI (taken in the original image) (3) Viewing all images in their registered state
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Emily Hammond, University of Iowa.
    """

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
    
    # define lists to store images and transforms
    self.imageNodes = []
    self.transformNodes = []
    self.roiNodes = []
    self.layouts = []
    self.filename = None
    
    # 
    # number of images
    #
    numberOfImagesButton = slicer.qMRMLCollapsibleButton()
    numberOfImagesButton.text = "Setup"
    self.layout.addWidget(numberOfImagesButton)
    
    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(numberOfImagesButton)
    
    #
    # Number of images selector (not fully implemented!!!)
    #
    self.numberSelector = qt.QLineEdit()
    self.numberSelector.setValidator(qt.QIntValidator())
    self.numberSelector.setMaxLength(2)
    self.numberSelector.toolTip = "Enter in the number of images for comparison."
    parametersFormLayout.addRow("Number of images: ", self.numberSelector)
    self.numberSelector.textChanged.connect(self.numberchanged)
        
    #
    # Resample rois Button
    #
    self.fileDialogButton = qt.QPushButton("Select file to store data.")
    self.fileDialogButton.toolTip = "Select the csv file to store the final feature results."
    self.fileDialogButton.enabled = True
    parametersFormLayout.addRow("CSV file: ", self.fileDialogButton)
    
    # connections
    self.fileDialogButton.connect('clicked(bool)', self.onFileDialog)

    # Add vertical spacer
    self.layout.addStretch(1)

    #
    # actions Area
    #
    actionsCollapsibleButton = slicer.qMRMLCollapsibleButton()
    actionsCollapsibleButton.text = "Actions"
    self.layout.addWidget(actionsCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(actionsCollapsibleButton)
    
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
    # Resample into baseline space
    #
    self.baselineSpaceButton = qt.QPushButton("Baseline space")
    self.baselineSpaceButton.toolTip = "Resample rois into baseline image space."
    self.baselineSpaceButton.enabled = True
    parametersFormLayout.addRow(self.baselineSpaceButton)

    # connections
    self.baselineSpaceButton.connect('clicked(bool)', self.onbaselineSpaceButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onBaselineSpace()
    
    #
    # Find extent button
    #
    self.findExtentButton = qt.QPushButton("Find extent")
    self.findExtentButton.toolTip = "Find extent of the label mask."
    self.findExtentButton.enabled = True
    parametersFormLayout.addRow(self.findExtentButton)

    # connections
    self.findExtentButton.connect('clicked(bool)', self.onfindExtentButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onFindExtent()
    
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

    #
    # baseline image Area
    #
    baselineCollapsibleButton = slicer.qMRMLCollapsibleButton()
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
    self.baselineRoiSelector = slicer.qMRMLNodeComboBox()
    self.baselineRoiSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.baselineRoiSelector.selectNodeUponCreation = True
    self.baselineRoiSelector.addEnabled = False
    self.baselineRoiSelector.removeEnabled = False
    self.baselineRoiSelector.noneEnabled = False
    self.baselineRoiSelector.showHidden = False
    self.baselineRoiSelector.showChildNodeTypes = False
    self.baselineRoiSelector.setMRMLScene( slicer.mrmlScene )
    self.baselineRoiSelector.setToolTip( "Pick the region of interest." )
    parametersFormLayout.addRow("Region of interest (label map) ", self.baselineRoiSelector)
    
  def numberchanged(self,number):
    # remove all previous nodes
    for n in xrange(0, len(self.layouts)):
        self.layouts[n].delete()
  
    for i in xrange(1,int(number)):
        #
        # image Area
        #
        imageCollapsibleButton = slicer.qMRMLCollapsibleButton()
        imageCollapsibleButton.text = "Image set " + str(i)
        self.layout.addWidget(imageCollapsibleButton)
        
        self.layouts.append(imageCollapsibleButton)

        # Layout within the dummy collapsible button
        tempLayout = qt.QFormLayout(imageCollapsibleButton)
        
        self.layouts.append(tempLayout)
        
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
        tempLayout.addRow("Image: ", self.imageSelector)
        
        self.layouts.append(self.imageSelector)
        
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
        tempLayout.addRow("Transform: ", self.transformSelector)
        
        self.layouts.append(self.transformSelector)
        
        #
        # ROI volume selector
        #
        self.roiSelector = slicer.qMRMLNodeComboBox()
        self.roiSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.roiSelector.selectNodeUponCreation = True
        self.roiSelector.addEnabled = False
        self.roiSelector.removeEnabled = False
        self.roiSelector.noneEnabled = True
        self.roiSelector.showHidden = False
        self.roiSelector.showChildNodeTypes = False
        self.roiSelector.setMRMLScene( slicer.mrmlScene )
        self.roiSelector.setToolTip( "Corresponding region of interest." )
        tempLayout.addRow("Region of interest (label map) ", self.roiSelector)
        
        self.layouts.append(self.transformSelector)

        # store node information
        self.imageNodes.append(self.imageSelector)
        self.transformNodes.append(self.transformSelector)
        self.roiNodes.append(self.roiSelector)
        self.layouts.append(tempLayout)
    
  def cleanup(self):
    pass
    
  def onFileDialog(self):
    self.fileDialogButton.enabled = True
    self.filename = qt.QFileDialog.getSaveFileName()
    open(self.filename,'w')
 
  def onSelectResample(self):
    self.resampleLabelMapsButton.enabled
    
  def onSelectCalculate(self):
    self.calculateStatsButton.enabled
    
  def onBaselineSpace(self):
    self.baselineSpaceButton.enabled
    
  def onFindExtent(self):
    self.findExtentButton.enabled
    
  def onShowLayout(self):
    self.showLayoutButton.enabled

  def onresampleLabelMapsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    images.append(self.baselineSelector.currentNode())
    for i in xrange(0,int(self.numberSelector.text)-1):
        images.append(self.imageNodes[i].currentNode())
    # gather transforms into list
    transforms = []
    for i in xrange(0,int(self.numberSelector.text)-1):
        transforms.append(self.transformNodes[i].currentNode())
    # send to logic
    logic.resampleLabelMaps(self.baselineRoiSelector.currentNode(), self.baselineSelector.currentNode(), images, transforms)

  def oncalculateStatsButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    rois = []
    images.append(self.baselineSelector.currentNode())
    rois.append(self.baselineRoiSelector.currentNode())
    for i in xrange(0,int(self.numberSelector.text)-1):
        images.append(self.imageNodes[i].currentNode())    # send to logic
        rois.append(self.roiNodes[i].currentNode())
    logic.calculateStatistics(images, rois, self.filename)
    
  def onbaselineSpaceButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    rois = []
    rois.append(self.baselineRoiSelector.currentNode())
    for i in xrange(0,int(self.numberSelector.text)-1):
        rois.append(self.roiNodes[i].currentNode())
    # gather transforms into list
    transforms = []
    for i in xrange(0,int(self.numberSelector.text)-1):
        transforms.append(self.transformNodes[i].currentNode())
    logic.baselineSpace(self.baselineSelector.currentNode(), rois, transforms)
    
  def onfindExtentButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    rois = []
    rois.append(self.baselineRoiSelector.currentNode())
    for i in xrange(0,int(self.numberSelector.text)-1):
        rois.append(self.roiNodes[i].currentNode())
    logic.findExtent(rois, self.filename)
    
  def onshowLayoutButton(self):
    logic = LongitudinalFeatureExtractionLogic()
    # gather images into list
    images = []
    images.append(self.baselineSelector.currentNode())
    for i in xrange(0,int(self.numberSelector.text)-1):
        images.append(self.imageNodes[i].currentNode())
    # gather transforms into list
    transforms = []
    for i in xrange(0,int(self.numberSelector.text)-1):
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
    
    transform.Inverse()
    
    # resample roi using inverse transform
    parameters = {}
    parameters["inputVolume"] = roi
    parameters["referenceVolume"] = image
    parameters["outputVolume"] = roiNew
    parameters["pixelType"] = "int"
    parameters["warpTransform"] = transform
    parameters["interpolationMode"] = "NearestNeighbor"
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
    for x in xrange(1, len(images)):
        if( images[x] != None ):
            # apply transforms and create new rois/image
            roiNew = self.applyTransform( images[x], roi, transforms[x-1] )
        else:
            print("Image not selected")
 
    return True
    
  # redo this function similar to how it is done with the labelstatistics module
  def calculateStatistics(self, images, rois, filename):
    # initialize results list
    keys = ["Image","Index", "Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev"]
    results = {}
    results['Image'] = []
    results['Labels'] = []
  
    # iterate through all the images
    print(images)
    print(rois)
    for x in range(0,len(images)):
        if( images[x] != None ):
            # pull roi from slicer
            if( rois[x] != None ):
                roi = slicer.util.getNode(rois[x].GetName())
            else:
                roi = slicer.util.getNode(images[x].GetName() + '-label')
            maxLabel = self.getLabelStats(images[x], roi, results)
        else:
            print("Image not selected")
            
    # print out results in a nice table
    print(keys)
    for im in results['Image']:
        for label in xrange(min(results['Labels']),max(results['Labels'])+1):
            data = []
            for header in keys:
                data.append(results[im,label,header])
            print(data)
            
    # write results to file if a csv file is given
    print(filename)
    if( filename != None ):
        with open(filename,'a') as file:
            file.write(', '.join(keys))
            file.write('\n')
            for im in results['Image']:
                for label in xrange(min(results['Labels']),max(results['Labels'])+1):
                    data = []
                    for header in keys:
                        #data.append(results[im,label,header])
                        file.write(str(results[im,label,header]))
                        file.write(',')
                    file.write('\n')
    
    return True
    
  def showLayout(self, images, transforms):
 
    # apply and observe transforms on appropriate images
    for x in range(1, len(images)):
        if( images[x] != None ):

            transforms[x-1].Inverse()
            
            # observe transform with image
            images[x].SetAndObserveTransformNodeID( transforms[x-1].GetID() )
            
            # observe transform with roi
            roi = slicer.util.getNode(images[x].GetName() + '-label')
            roi.SetAndObserveTransformNodeID( transforms[x-1].GetID() )

    return
    
  def findExtent(self, rois, filename):
  
    # initialize results list
    keys = ["Image","Xmin", "Xmax", "Ymin", "Ymax", "Zmin", "Zmax","-Xgrowth","+Xgrowth","-Ygrowth","+Ygrowth","-Zgrowth","+Zgrowth"]
    results = []
    
    spacing = rois[0].GetSpacing()
    roi = slicer.util.array(rois[0].GetID())
    
    z = np.any(roi, axis=(1,2))
    y = np.any(roi, axis=(0,2))
    x = np.any(roi, axis=(0,1))
    
    bzmax,bzmin = np.where(z)[0][[0,-1]]
    bymax,bymin = np.where(y)[0][[0,-1]]
    bxmin,bxmax = np.where(x)[0][[0,-1]]
    
    # enter results into list
    temp = [rois[0].GetName(),bxmin,bxmax,bymin,bymax,bzmin,bzmax,0,0,0,0,0,0]
    results.append(temp)
    
    # find extent in all the rois and print
    for x in range(1, len(rois)):
        
        roiNode = slicer.util.getNode(rois[x].GetName() + '_baselineSpace')
        roi = slicer.util.array(roiNode.GetID())
    
        z = np.any(roi, axis=(1,2))
        y = np.any(roi, axis=(0,2))
        x = np.any(roi, axis=(0,1))
        
        zmax,zmin = np.where(z)[0][[0,-1]]
        ymax,ymin = np.where(y)[0][[0,-1]]
        xmin,xmax = np.where(x)[0][[0,-1]]
        
        # enter results into list
        temp = [roiNode.GetName(),xmin,xmax,ymin,ymax,zmin,zmax,spacing[0]*(xmin-bxmin),spacing[0]*(xmax-bxmax),spacing[1]*(ymin-bymin),spacing[1]*(ymax-bymax),spacing[2]*(zmin-bzmin),spacing[2]*(zmax-bzmax)]
        results.append(temp)
        
    print(results)

    # write results to file if a csv file is given
    print(filename)
    if( filename != None ):
        with open(filename,'a') as file:
            file.write('\n\n')
            file.write(', '.join(keys))
            file.write('\n')
            file.writelines(["%s\n" % item for item in results])
    return
    
  def baselineSpace(self, baselineImage, rois, transforms):
  
    for x in range(1, len(rois)):
        if( rois[x].GetName() != None ):
            # create new volumes
            roiNew = slicer.vtkMRMLLabelMapVolumeNode()
            roiNew.SetName(rois[x].GetName() + '_baselineSpace')
            slicer.mrmlScene.AddNode( roiNew )
            
            # resample roi using inverse transform
            parameters = {}
            parameters["inputVolume"] = rois[x]
            parameters["referenceVolume"] = baselineImage
            parameters["outputVolume"] = roiNew
            parameters["pixelType"] = "int"
            parameters["warpTransform"] = transforms[x-1]
            parameters["interpolationMode"] = "NearestNeighbor"
            # call module
            cliNode = None
            cliNode = slicer.cli.run( slicer.modules.brainsresample, cliNode, parameters )
            print(cliNode.AddObserver('ModifiedEvent', self.printStatus))
    
    return roiNew

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
