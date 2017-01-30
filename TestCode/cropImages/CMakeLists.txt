cmake_minimum_required(VERSION 2.8.9)

project(CropImages)

find_package(ITK REQUIRED)
include(${ITK_USE_FILE})

set(CropImages_SRC CropImages.cxx)

add_library(CropImagesLib SHARED ${CropImages_SRC})
set_target_properties(CropImagesLib PROPERTIES COMPILE_FLAGS "-Dmain=ModuleEntryPoint")
target_link_libraries(CropImagesLib ${ITK_LIBRARIES})

add_executable(CropImages ${CropImages_SRC})
target_link_libraries(CropImages ${ITK_LIBRARIES})