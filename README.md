# Image-Compressor
Python application to resize (using PIL) and compress (using TinyPNG) a series of images

Requires an internet connection if compressing (due to use of TinyPNG)

To run the program from the command line, you can use the following arguments:

```
-i input_folder (if not specified, print error)
-o output_folder (if not specified, assume input_folder)
-resize (if not specified, don't resize; if neither resize nor compress, just resize)
-d max_dimension (if not specified, assume 1200px)
-compress (if not specified, don't compress. If specified without api key, print error)
-k api_key (if not specified, print error if specified compress)
```