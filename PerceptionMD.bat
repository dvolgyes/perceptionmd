set argC=0
for %%x in (%*) do Set /A argC+=1

IF /I "%argC%" EQU "0" CALL %~dp0\..\python.exe %~dp0\PerceptionMD.py example
IF /I "%argC%" GEQ "1" CALL %~dp0\..\python.exe %~dp0\PerceptionMD.py "%1"
