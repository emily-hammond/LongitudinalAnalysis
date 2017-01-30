/*
 * Emily Hammond
 * 9/1/2015
 *
 * The goal of this code is to read in a bunch of images and their corresponding 
 * transformations and label maps, resample the images and crop the data with
 * respect to the reference image listed
 */

#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkCastImageFilter.h"

// extract ROI image
#include "itkPoint.h"
#include "itkExtractImageFilter.h"

#include <itksys/SystemTools.hxx>
#include <fstream>
#include <string>

// function to read in images
template<typename ImageType>
typename ImageType::Pointer ReadInImage( const char * ImageFilename )
{
	typedef itk::ImageFileReader<ImageType>		ReaderType;	
	typename ReaderType::Pointer reader = ReaderType::New();
	reader->SetFileName( ImageFilename );
	
	// update reader
	try
	{
		reader->Update();
		std::cout << std::endl;
		std::cout << ImageFilename << " has been read in." << std::endl;
	}
	catch(itk::ExceptionObject & err)
	{
		std::cerr << "Exception Object Caught!" << std::endl;
		std::cerr << err << std::endl;
		std::cerr << std::endl;
	}
	
	// return output
	return reader->GetOutput();
}

// function to write out images
template<typename inputImageType, typename outputImageType>
int WriteOutImage( const char * ImageFilename, typename inputImageType::Pointer image )
{
	typedef itk::CastImageFilter<inputImageType, outputImageType> CastFilterType;
	typename CastFilterType::Pointer caster = CastFilterType::New();
	caster->SetInput( image );

	typedef itk::ImageFileWriter<outputImageType> WriterType;
	typename WriterType::Pointer writer = WriterType::New();
	writer->SetFileName( ImageFilename );
	writer->SetInput( caster->GetOutput() );

	// update the writer
	try
	{
		writer->Update();
		//std::cout << std::endl;
		//std::cout << ImageFilename << " has been written." << std::endl;
	}
	catch(itk::ExceptionObject & err)
	{
		std::cerr << "Exception Object Caught!" << std::endl;
		std::cerr << err << std::endl;
		std::cerr << std::endl;
	}

	std::cout << ImageFilename << " written to file." << std::endl;

	// return output
	return EXIT_SUCCESS;
}

// function to extract ROI values
double * ExtractROI( const char * filename )
{
	// instantiate ROI array
	static double roi[] = {0.0,0.0,0.0,0.0,0.0,0.0};
	int m = 0;
	bool flag = true; // denoting that ROI is full

	// open file and extract lines
	std::ifstream file( filename );
	std::string line;
	// iterate through file
	while( getline( file, line ) )
	{
		// look at lines that are not commented
		if( line.compare(0,1,"#") != 0 && flag)
		{
			// allocate position array
			int pos [4] = {0};
			int n = 0;
			int posN = 0;

			// create iterator for line to fine | locations
			for( std::string::iterator it = line.begin(); it != line.end(); ++it )
			{
				if( (*it == '|') && (n < 4) )
				{
					pos[n] = posN;
					++n;
				}
				++posN;
			}

			// extract the point to the roi
			for( int i = 0; i < 3; ++i )
			{
				std::string roiT = line.substr(pos[i]+1,(pos[i+1]-pos[i]-1));
				roi[m] = atof(roiT.c_str());
				++m;

				// set flag to false
				if( m == 6 ){ flag = false; }
			}
		}
	}

	std::cout << std::endl;
	std::cout << filename << " has been read." << std::endl;

	return roi;
}

// ***********************Main function********************************
int main( int argc, char * argv[] )
{
	// inputs: CropImages.exe imageFilename ROIFilename outputFilename 

	// instantiate variables to be used
	typedef itk::Image< unsigned short, 3 >			ImageType;
	//typedef itk::Image< unsigned int, 3 >			LabelMapType;


	// read in image and roi
	ImageType::Pointer image = ImageType::New();
	image = ReadInImage< ImageType >( argv[1] );
	double * roi = ExtractROI( argv[2] );
	
	// extract region of interest from resampled image
	// extract center and radii from the roi values
	double c[3] = {-*(roi),-*(roi+1),*(roi+2)};
	double r[3] = {*(roi+3),*(roi+4),*(roi+5)};
	
	// create lower point and upper point
	itk::Point<double, 3> pt1;
	itk::Point<double, 3> pt2;

	// create lower point
	pt1[0] = c[0] + r[0]; //93
	pt1[1] = c[1] + r[1]; //-153
	pt1[2] = c[2] + r[2]; //-649

	// create upper point
	pt2[0] = c[0] - r[0]; //17
	pt2[1] = c[1] - r[1]; //-213
	pt2[2] = c[2] - r[2]; //-787

	// transform points to physical coordinates
	itk::Index<3> idx1, idx2;
	image->TransformPhysicalPointToIndex( pt1, idx1 );
	image->TransformPhysicalPointToIndex( pt2, idx2 );

	// ensure idx2 values are greater than idx1 values
	for( int i = 0; i < 3; ++i )
	{
		if( idx1[i] > idx2[i] )
		{
			const itk::IndexValueType t = idx1[i];
			idx1[i] = idx2[i];
			idx2[i] = t;
		}
	}

	// define desired region
	itk::ImageRegion<3> desiredRegion;
	desiredRegion.SetIndex(idx1);
	desiredRegion.SetUpperIndex(idx2);
	desiredRegion.Crop( image->GetLargestPossibleRegion() );

	// extract the image
	typedef itk::ExtractImageFilter< ImageType, ImageType > ExtractFilterType;
	ExtractFilterType::Pointer extractImage = ExtractFilterType::New();
	extractImage->SetExtractionRegion( desiredRegion );
	extractImage->SetInput( image );
	extractImage->SetDirectionCollapseToIdentity();
	extractImage->InPlaceOn();
		
	// update filter
	try
	{
		extractImage->Update();
	}
	catch(itk::ExceptionObject & err)
	{
		std::cerr << "Exception Object Caught!" << std::endl;
		std::cerr << err << std::endl;
		std::cerr << std::endl;
	}

	// write result to file
	WriteOutImage< ImageType, ImageType >( argv[3], extractImage->GetOutput() );
	
    return EXIT_SUCCESS;
}