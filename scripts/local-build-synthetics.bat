@echo off

echo This script is currently broken, binary builds do not support building from a specific Dockerfile
echo It now only works in the ICHP cluster using an azure pipeline.
exit /b 1

oc config use-context test-project/api-crc-testing:6443/kubeadmin

echo Checking if in root directory
if not exist .\pyproject.toml (
    echo "Please run this script from the root directory of the project"
    exit /b 1
)

echo "Building synthetics images locally and pushing to OpenShift"

::Build the synthetics untar image
echo "Building synthetic-unzip image"
tar -zcvf build.tar.gz --exclude "node_modules" --exclude "synth-data" --exclude ".git" --exclude "__pycache__" --exclude ".idea" -C "synthetic/synthetic-unzip" . -C "../.." ./scheduler
oc start-build synthetic-unzip --from-archive build.tar.gz --incremental=true --follow
del build.tar.gz
