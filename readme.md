#Crius Quickly Build Tool

This Tool aims to compile C/C++ code effectively.
Especially when we just need to update several files,
it's powerful and efficient.

Usage:
crius <build> [Product name] [files name with full path]
            -g [git commits id] : extract file names from the specific commit id
            -p [patches name] : extract file names from the specific patch
            -l [file including a file list] : extract file names from the specific file
            -O [output dir] : default is CRIUS_OBJ
crius extract
            -g [git commits id] : extract file names from the specific commit id
            -p [patches name] : extract file names from the specific patch
            -o [output file name] : write the file names into the specific file
crius update [Product name] : update or create build log for the specific product

Product Name:SF-RP-S9M SF-LC-S9M SF-RP-P1S SF-RP-P1L SF-RP-P0 SF-TDM1001
