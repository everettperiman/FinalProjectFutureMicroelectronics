#!/bin/bash
set -euo pipefail
# set -x          # For debugging only

# Get the name of the python script to be launched for building a build
modelBuildScriptName="$1"

# Go to the Run directory
# This is necessary as Expeditor looks at this directory for adaptive rebuild and
# results collection
runDirectory=$(dirname $modelBuildScriptName)
cd $runDirectory
chmod -R 777 $runDirectory


# Copy the script the script to the machine with qmaster if it is not there yet
#
# We are assuming "all shared" configuration, hence this is not required
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"     # Both the scripts are expected to be in the same dir
submitAndReturnIdScript=${SCRIPTS_DIR%%/}/submitAndReturnId.sh

# NOTE: SSH must be setup to login without password
#       See: http://www.linuxproblem.org/art_9.html &
#            http://stackoverflow.com/questions/6377009/adding-public-key-to-ssh-authorized-keys-does-not-log-me-in-automatically
# Invoke the remote script with the given arguments
ssh sgeadmin@10.34.145.41 "bash -s" < $submitAndReturnIdScript "$modelBuildScriptName"