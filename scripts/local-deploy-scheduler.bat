@echo off
oc config use-context test-project/api-crc-testing:6443/kubeadmin

echo Checking if in root directory
if not exist .\pyproject.toml (
    echo "Please run this script from the root directory of the project"
    exit /b 1
)

echo "Packaging helm chart and deploying to OpenShift"
helm package oc
helm upgrade --install scheduler .\scheduler-0.0.1.tgz -f .\oc\values_local.yaml