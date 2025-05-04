
# Optimized workflow configuration
# Copy and paste these settings into the .replit file manually

[[workflows.workflow]]
name = "Optimized Server"
author = "agent"
    
[workflows.workflow.metadata]
agentRequireRestartOnSave = false
    
[[workflows.workflow.tasks]]
task = "packager.installForAll"
    
[[workflows.workflow.tasks]]
task = "shell.exec"
args = "python run_optimized.py"
waitForPort = 8080
