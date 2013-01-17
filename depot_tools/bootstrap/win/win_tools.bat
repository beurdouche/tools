@echo off
:: Copyright (c) 2012 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

:: This script will try to find if svn and python are accessible and it not,
:: it will try to download it and 'install' it in depot_tools.

:: Sadly, we can't use SETLOCAL here otherwise it ERRORLEVEL is not correctly
:: returned.

set WIN_TOOLS_ROOT_URL=http://src.chromium.org/svn/trunk/tools

:: Get absolute root directory (.js scripts don't handle relative paths well).
pushd %~dp0..\..
set WIN_TOOLS_ROOT_DIR=%CD%
popd

if "%1" == "force" (
  set WIN_TOOLS_FORCE=1
  shift /1
)


:GIT_CHECK
:: If the batch file exists, skip the git check.
if exist "%WIN_TOOLS_ROOT_DIR%\git.bat" goto :SVN_CHECK
if "%CHROME_HEADLESS%" == "1" goto :SVN_CHECK
if "%WIN_TOOLS_FORCE%" == "1" goto :GIT_INSTALL
call git --version 2>nul 1>nul
if errorlevel 1 goto :GIT_INSTALL
goto :SVN_CHECK


:GIT_INSTALL
echo Installing git (avg 1-2 min download) ...
:: git is not accessible; check it out and create 'proxy' files.
if exist "%~dp0git.zip" del "%~dp0git.zip"
cscript //nologo //e:jscript "%~dp0get_file.js" %WIN_TOOLS_ROOT_URL%/third_party/git_bin.zip "%~dp0git.zip"
if errorlevel 1 goto :GIT_FAIL
:: Cleanup svn directory if it was existing.
if exist "%WIN_TOOLS_ROOT_DIR%\git_bin\." rd /q /s "%WIN_TOOLS_ROOT_DIR%\git_bin"
:: Will create git_bin\...
cscript //nologo //e:jscript "%~dp0unzip.js" "%~dp0git.zip" "%WIN_TOOLS_ROOT_DIR%"
if errorlevel 1 goto :GIT_FAIL
if not exist "%WIN_TOOLS_ROOT_DIR%\git_bin\." goto :GIT_FAIL
del "%~dp0git.zip"
:: Create the batch files.
call copy /y "%WIN_TOOLS_ROOT_DIR%\git_bin\git.bat" "%WIN_TOOLS_ROOT_DIR%\git.bat" 1>nul
call copy /y "%WIN_TOOLS_ROOT_DIR%\git_bin\gitk.bat" "%WIN_TOOLS_ROOT_DIR%\gitk.bat" 1>nul
call copy /y "%WIN_TOOLS_ROOT_DIR%\git_bin\ssh.bat" "%WIN_TOOLS_ROOT_DIR%\ssh.bat" 1>nul
call copy /y "%WIN_TOOLS_ROOT_DIR%\git_bin\ssh-keygen.bat" "%WIN_TOOLS_ROOT_DIR%\ssh-keygen.bat" 1>nul
:: Ensure autocrlf and filemode are set correctly.
call "%WIN_TOOLS_ROOT_DIR%\git.bat" config --global core.autocrlf false
call "%WIN_TOOLS_ROOT_DIR%\git.bat" config --global core.filemode false
goto :SVN_CHECK


:GIT_FAIL
echo ... Failed to checkout git automatically.
echo Please visit http://code.google.com/p/msysgit to download the latest git
echo client before continuing.
echo You can also get the "prebacked" version used at %WIN_TOOLS_ROOT_URL%/
set ERRORLEVEL=1
goto :END


:SVN_CHECK
:: If the batch file exists, skip the svn check.
if exist "%WIN_TOOLS_ROOT_DIR%\svn.bat" goto :PYTHON_CHECK
if "%WIN_TOOLS_FORCE%" == "1" goto :SVN_INSTALL
call svn --version 2>nul 1>nul
if errorlevel 1 goto :SVN_INSTALL
goto :PYTHON_CHECK


:SVN_INSTALL
echo Installing subversion ...
:: svn is not accessible; check it out and create 'proxy' files.
if exist "%~dp0svn.zip" del "%~dp0svn.zip"
cscript //nologo //e:jscript "%~dp0get_file.js" %WIN_TOOLS_ROOT_URL%/third_party/svn_bin.zip "%~dp0svn.zip"
if errorlevel 1 goto :SVN_FAIL
:: Cleanup svn directory if it was existing.
if exist "%WIN_TOOLS_ROOT_DIR%\svn\." rd /q /s "%WIN_TOOLS_ROOT_DIR%\svn"
if exist "%WIN_TOOLS_ROOT_DIR%\svn_bin\." rd /q /s "%WIN_TOOLS_ROOT_DIR%\svn_bin"
:: Will create svn_bin\...
cscript //nologo //e:jscript "%~dp0unzip.js" "%~dp0svn.zip" "%WIN_TOOLS_ROOT_DIR%"
if errorlevel 1 goto :SVN_FAIL
if not exist "%WIN_TOOLS_ROOT_DIR%\svn_bin\." goto :SVN_FAIL
del "%~dp0svn.zip"
:: Create the batch file.
call copy /y "%~dp0svn.new.bat" "%WIN_TOOLS_ROOT_DIR%\svn.bat" 1>nul
call copy /y "%~dp0svnversion.new.bat" "%WIN_TOOLS_ROOT_DIR%\svnversion.bat" 1>nul
goto :PYTHON_CHECK


:SVN_FAIL
echo ... Failed to checkout svn automatically.
echo Please visit http://subversion.tigris.org to download the latest subversion client
echo before continuing.
echo You can also get the "prebacked" version used at %WIN_TOOLS_ROOT_URL%/third_party/
set ERRORLEVEL=1
goto :END


:PYTHON_CHECK
:: If the batch file exists, skip the python check.
set ERRORLEVEL=0
if exist "%WIN_TOOLS_ROOT_DIR%\python.bat" goto :END
if "%WIN_TOOLS_FORCE%" == "1" goto :PYTHON_INSTALL
call python --version 2>nul 1>nul
if errorlevel 1 goto :PYTHON_INSTALL

:: We are done.
set ERRORLEVEL=0
goto :END


:PYTHON_INSTALL
echo Installing python ...
:: Cleanup python directory if it was existing.
if exist "%WIN_TOOLS_ROOT_DIR%\python_bin\." rd /q /s "%WIN_TOOLS_ROOT_DIR%\python_bin"
call svn co -q %WIN_TOOLS_ROOT_URL%/third_party/python_26 "%WIN_TOOLS_ROOT_DIR%\python_bin"
if errorlevel 1 goto :PYTHON_FAIL
:: Create the batch files.
call copy /y "%~dp0python.new.bat" "%WIN_TOOLS_ROOT_DIR%\python.bat" 1>nul
call copy /y "%~dp0pylint.new.bat" "%WIN_TOOLS_ROOT_DIR%\pylint.bat" 1>nul
set ERRORLEVEL=0
goto :END


:PYTHON_FAIL
echo ... Failed to checkout python automatically.
echo Please visit http://python.org to download the latest python 2.x client before
echo continuing.
echo You can also get the "prebacked" version used at %WIN_TOOLS_ROOT_URL%/third_party/
set ERRORLEVEL=1
goto :END


:returncode
set WIN_TOOLS_ROOT_URL=
set WIN_TOOLS_ROOT_DIR=
exit /b %ERRORLEVEL%

:END
call :returncode %ERRORLEVEL%
