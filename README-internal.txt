There are two main components to this code:

1) Code to generate 3 nice public files for each galaxy, from the "kinematics_paperversion" folders on Box. This code has two versions, "process_box" and "process_local".

The simplest thing is to run "process_local" on a directory on your machine (which can be the Reduced-Data folder synced from Box, or another folder with the same structure).

If you want to be fancy and run the code on all the galaxies without downloading the data, you can run "process_box". You'll have to get a client id, client secret, and 1 hour developer access token at https://berkeley.app.box.com/developers/services.

As we get new galaxies observed, they should be put through this process and added to the website. There are some examples in the Makefile of the basic command line argument structure; look in the scripts themselves for more details. There are flags for including or excluding specific galaxies, to make it convenient whether you are running this on a folder with only the new galaxies (e.g. before uploading everybody to Box) or on the Box folder itself, but wanting to run only on newly uploaded galaxies.

This code mostly just rearranges files, but it DOES do a couple of new things not found in the files in kinematics_paperversion. Most useful is the last section of the misc.txt file, which has the sigma profile fits.

IMPORTANT NOTE: the bookkeeping for things like PA, Re, and epsilon can be messy in the kinematics_paperversion files; if these have been tweaked, make sure to check that they are correct in the output file. Following the rules of the paper V table, if Re or epsilon are changed then the new value should be used everywhere. If a different PA is used for folding, however, it doesn't mean the photo PA is "wrong" so we have to keep track of both versions. If exceptions need to be made to fix what is in the kinematics_paperversion files, they can be added to modules/exceptions.py.

2) Code to generate a summary table for all of the galaxies. The version for the galaxies in paper V shouldn't need to be remade, but the version with all observed galaxies can be updated every so often as new galaxies are added. Note that this creates two files; one for the quantities actually listed in the paper table, and one for additional quantities used in scatterplots.