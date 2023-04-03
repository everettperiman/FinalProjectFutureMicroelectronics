#!/bin/bash
set -euo pipefail
# set -x        # For debugging only

# Get the name of the python script to be launched for building a build
modelBuildScriptName="$1"
# echo "Model build script = $modelBuildScriptName"

# %q escapes the string so that it can be reused as an input for the shell.
# This is exactly what we need to forward all the arguments of this script to
# the hpc script, without choking on spaces or on special characters. %q is
# specific to bash.
escapedArgs=$(printf "%q " "$@")

# Go to the Run directory
# This is necessary as Expeditor looks at this directory for adaptive rebuild and
# results collection
runDirectory=$(dirname $modelBuildScriptName)
cd $runDirectory

# Submit to grid engine. We pass the script through stdin, because the alternative
# is to write it to disk and to use the filename as an argument to qsub. Doing this
# is a security risk because the file could contain a clear text password when
# expanding $escapedArgs (the --fpw, --spw or --mpw arguments coming from Expeditor).
unparsedJobID=`qsub << HEREDOCUMENT
#!/bin/bash
#
#$ -cwd
#$ -V
#$ -j n
#$ -S /bin/bash

set -euo pipefail
# set -x      # For debugging only

# Set the license
export COVLD_LICENSE_FILE="54015@license.memcad.com"

# Source the environment
set +u
source /mnt/users/epaladugu/semulator3d_hg/semulator3d/distrib/bin/semulator3d.sh
set -u

# Launch the model build now that environment and licenses are set properly
python $escapedArgs

# Flush the file buffers
# Required as the master node is expected to read from the file system of the
# node running the model build run
sync

# Set the appropriate permissions so that we can delete the run directory if necessary
chmod -R 777 "$runDirectory"
HEREDOCUMENT
`
echo "$unparsedJobID"

# Parsing the output to get the job id
# see: http://stackoverflow.com/questions/22893680/how-to-get-the-job-id-from-qsub
jobID=`echo "$unparsedJobID" | grep -o '[0-9]\+'`
# echo $jobID


# Monitor the launched job
#
# Uses `qstat -j` to monitor the status of the job.
# Execution of the script should be blocked until the job has terminated
EXPECTED_STDERR_IN_CASE_OF_TERMINATION="Following jobs do not exist: $jobID"
qstatStdErr=""

until [ "$EXPECTED_STDERR_IN_CASE_OF_TERMINATION" == "$qstatStdErr" ];
do
    # Poll timer
    sleep 5

    # Run qstat and get its output (stderr)
    #      1. Get the stderr while redirecting stdout to dev null
    #      2. Replace newlines with white space
    #      3. Trim any white space at the end
    set +e
    qstatStdErr=$(qstat -j $jobID 2>&1 > /dev/null | tr '\n' ' ' | xargs)
    set -e
done

# Wait for some time for the file system updates to be visible at the master node
sync

# Return the jobid so that parent process can use it for the logging purpose
echo $jobID
exit 0