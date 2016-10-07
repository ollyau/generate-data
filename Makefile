MRVBOX = /Users/melanieveale/Box\ Sync/MASSIVE/Reduced-Data
MRVOUT = /Users/melanieveale/Documents/Research/programming/Kinematics15/all_my_output/generate-data-everybody-test

all: test1

test1:
	python process_local.py -d testinput -o testoutput

everybodytest:
	python process_local.py -d ${MRVBOX} -o ${MRVOUT}