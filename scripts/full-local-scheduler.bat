@echo off
oc config use-context test-project/api-crc-testing:6443/kubeadmin

echo Checking if in root directory
if not exist .\pyproject.toml (
    echo "Please run this script from the root directory of the project"
    exit /b 1
)

call scripts\local-build-scheduler.bat
call scripts\local-deploy-scheduler.bat