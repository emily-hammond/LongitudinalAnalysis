cmake_minimum_required(VERSION 2.8.9)

project(Multi-LevelRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/Multi-LevelRegistration")
set(EXTENSION_CATEGORY "Registratoin")
set(EXTENSION_CONTRIBUTORS "Emily Hammond (University of Iowa), Jessica C. Sieren (University of Iowa) ")
set(EXTENSION_DESCRIPTION "Perform rigid registration with increasingly smaller volumes of data defined by regions of interest focusing on a desired anatomy.")
set(EXTENSION_ICONURL "https://github.com/emily-hammond/LongitudinalAnalysis/blob/master/MultiLevelRegistrationLogo_275x235.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/wiki/File:MultiLevelRegistrationExample.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})


#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})


#-----------------------------------------------------------------------------
set(MODULE_NAME Multi-LevelRegistration)

#-----------------------------------------------------------------------------

#
# SlicerExecutionModel
#
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

#
# ITK
#
set(${PROJECT_NAME}_ITK_COMPONENTS
  ITKCommon
  ITKIOImageBase
  ITKIOTransformBase
  ITKImageFunction
  ITKImageGrid
  ITKImageIntensity
  ITKOptimizers
  ITKRegistrationCommon
  ITKSpatialObjects
  ITKStatistics
  ITKTestKernel
  ITKTransform
  )
find_package(ITK 4.6 COMPONENTS ${${PROJECT_NAME}_ITK_COMPONENTS} REQUIRED)
set(ITK_NO_IO_FACTORY_REGISTER_MANAGER 1) # See Libs/ITKFactoryRegistration/CMakeLists.txt
include(${ITK_USE_FILE})

#-----------------------------------------------------------------------------
set(MODULE_INCLUDE_DIRECTORIES
  )

set(MODULE_SRCS
  )

set(MODULE_TARGET_LIBRARIES
  ${ITK_LIBRARIES}
  )

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  TARGET_LIBRARIES ${MODULE_TARGET_LIBRARIES}
  INCLUDE_DIRECTORIES ${MODULE_INCLUDE_DIRECTORIES}
  ADDITIONAL_SRCS ${MODULE_SRCS}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
