@echo off
oc config use-context test-project/api-crc-testing:6443/kubeadmin

echo Checking if in root directory
if not exist .\pyproject.toml (
    echo "Please run this script from the root directory of the project"
    exit /b 1
)

echo "Building and deploying the application from local source code"
tar -zcvf build.tar.gz --exclude "node_modules" --exclude "./scheduler/synthetic" --exclude ".git" --exclude "__pycache__" --exclude ".idea" .
oc start-build scheduler --from-archive build.tar.gz --follow
del build.tar.gz
