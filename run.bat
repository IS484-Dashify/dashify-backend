@echo off

start "app.py" cmd /k "py app.py"
start "getResults.py" cmd /k "py getResults.py"
start "thresholds.py" cmd /k "py thresholds.py"
start "notifications.py" cmd /k "py notifications.py"
start "results.py" cmd /k "py results.py"
@REM start "components.py" cmd /k "py components.py"
@REM start "machines.py" cmd /k "py machines.py"
@REM start "services.py" cmd /k "py services.py"
@REM start "getStatus.py" cmd /k "py getStatus.py"
@REM start "getNames.py" cmd /k "py getNames.py"
@REM start "users.py" cmd /k "py users.py"

