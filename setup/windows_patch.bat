@ECHO OFF

SET LIB=Lib\site-packages\prompt_toolkit\

FOR /F "tokens=* USEBACKQ" %%F IN (`where python`) DO (
    SET PythonPath=%%F
    goto :pypath
)
:pypath

SET PATH=%PythonPath:python.exe=%

SET "PromptToolkit=%PATH%%LIB%"
SET "INPUT=%PromptToolkit%input\win32.py"
SET "OUTPUT=%PromptToolkit%output\win32.py"

SET "SOURCE_INPUT=%~dp0prompt_toolkit\input\win32.py"
SET "SOURCE_OUTPUT=%~dp0prompt_toolkit\output\win32.py"

ECHO Prompt Toolkit Installed @: %PromptToolkit%
ECHO.

COPY /Y %SOURCE_INPUT% %INPUT%
COPY /Y %SOURCE_OUTPUT% %OUTPUT%

ECHO.
ECHO ~Patch Complete!~
ECHO.

PAUSE