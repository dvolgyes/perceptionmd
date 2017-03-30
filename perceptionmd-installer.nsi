;--------------------------------
; General Attributes


Name "PerceptionMD"
Caption "PerceptionMD"
OutFile "perceptionmd-installer.exe"
Unicode true
RequestExecutionLevel admin
InstallDir $PROFILE\PerceptionMD

!define APPNAME "PerceptionMD"
!define COMPANYNAME "PerceptionMD"
!define DESCRIPTION "observer studies in radiology"
# These three must be integers
!define VERSIONMAJOR 0
!define VERSIONMINOR 1
!define VERSIONBUILD 6
# These will be displayed by the "Click here for support information" link in "Add/Remove Programs"
# It is possible to use "mailto:" links in here to open the email client
!define HELPURL "https://github.com/dvolgyes/perceptionmd/issues" # "Support Information" link
!define UPDATEURL "https://github.com/dvolgyes/perceptionmd" # "Product Updates" link
!define ABOUTURL "https://github.com/dvolgyes/perceptionmd" # "Publisher" link
# This is the size (in kB) of all the files copied into "Program Files"
!define INSTALLSIZE 13000000

;--------------------------------
;Interface Settings
  !define MUI_ICON "perceptionmd.ico"
  !define MUI_UNICON "perceptionmd-uninstall.ico"
  
  !include "MUI2.nsh"
  !define MUI_ABORTWARNING

  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_INSTFILES
 
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

  
!ifndef FileAssociation_INCLUDED
!define FileAssociation_INCLUDED
 
!include Util.nsh
 
!verbose push
!verbose 3
!ifndef _FileAssociation_VERBOSE
  !define _FileAssociation_VERBOSE 3
!endif
!verbose ${_FileAssociation_VERBOSE}
!define FileAssociation_VERBOSE `!insertmacro FileAssociation_VERBOSE`
!verbose pop
 
!macro FileAssociation_VERBOSE _VERBOSE
  !verbose push
  !verbose 3
  !undef _FileAssociation_VERBOSE
  !define _FileAssociation_VERBOSE ${_VERBOSE}
  !verbose pop
!macroend
 
 
 
!macro RegisterExtensionCall _EXECUTABLE _EXTENSION _DESCRIPTION
  !verbose push
  !verbose ${_FileAssociation_VERBOSE}
  Push `${_DESCRIPTION}`
  Push `${_EXTENSION}`
  Push `${_EXECUTABLE}`
  ${CallArtificialFunction} RegisterExtension_
  !verbose pop
!macroend
 
!macro UnRegisterExtensionCall _EXTENSION _DESCRIPTION
  !verbose push
  !verbose ${_FileAssociation_VERBOSE}
  Push `${_EXTENSION}`
  Push `${_DESCRIPTION}`
  ${CallArtificialFunction} UnRegisterExtension_
  !verbose pop
!macroend
 
 
 
!define RegisterExtension `!insertmacro RegisterExtensionCall`
!define un.RegisterExtension `!insertmacro RegisterExtensionCall`
 
!macro RegisterExtension
!macroend
 
!macro un.RegisterExtension
!macroend
 
!macro RegisterExtension_
  !verbose push
  !verbose ${_FileAssociation_VERBOSE}
 
  Exch $R2 ;exe
  Exch
  Exch $R1 ;ext
  Exch
  Exch 2
  Exch $R0 ;desc
  Exch 2
  Push $0
  Push $1
 
  ReadRegStr $1 HKCR $R1 ""  ; read current file association
  StrCmp "$1" "" NoBackup  ; is it empty
  StrCmp "$1" "$R0" NoBackup  ; is it our own
    WriteRegStr HKCR $R1 "backup_val" "$1"  ; backup current value
NoBackup:
  WriteRegStr HKCR $R1 "" "$R0"  ; set our file association
 
  ReadRegStr $0 HKCR $R0 ""
  StrCmp $0 "" 0 Skip
    WriteRegStr HKCR "$R0" "" "$R0"
    WriteRegStr HKCR "$R0\shell" "" "open"
    WriteRegStr HKCR "$R0\DefaultIcon" "" "$R2,0"
Skip:
  WriteRegStr HKCR "$R0\shell\open\command" "" '"$R2" "%1"'
  WriteRegStr HKCR "$R0\shell\edit" "" "Edit $R0"
  WriteRegStr HKCR "$R0\shell\edit\command" "" '"$R2" "%1"'
 
  Pop $1
  Pop $0
  Pop $R2
  Pop $R1
  Pop $R0
 
  !verbose pop
!macroend
 
 
 
!define UnRegisterExtension `!insertmacro UnRegisterExtensionCall`
!define un.UnRegisterExtension `!insertmacro UnRegisterExtensionCall`
 
!macro UnRegisterExtension
!macroend
 
!macro un.UnRegisterExtension
!macroend
 
!macro UnRegisterExtension_
  !verbose push
  !verbose ${_FileAssociation_VERBOSE}
 
  Exch $R1 ;desc
  Exch
  Exch $R0 ;ext
  Exch
  Push $0
  Push $1
 
  ReadRegStr $1 HKCR $R0 ""
  StrCmp $1 $R1 0 NoOwn ; only do this if we own it
  ReadRegStr $1 HKCR $R0 "backup_val"
  StrCmp $1 "" 0 Restore ; if backup="" then delete the whole key
  DeleteRegKey HKCR $R0
  Goto NoOwn
 
Restore:
  WriteRegStr HKCR $R0 "" $1
  DeleteRegValue HKCR $R0 "backup_val"
  DeleteRegKey HKCR $R1 ;Delete key with association name settings
 
NoOwn:
 
  Pop $1
  Pop $0
  Pop $R1
  Pop $R0
 
  !verbose pop
!macroend
 
!endif # !FileAssociation_INCLUDED

;--------------------------------
;Installer Sections

;Section "Dummy Section" SecDummy
;SectionEnd


Section "Miniconda environment" MinicondaInstall
	SetOutPath "$INSTDIR"
    inetc::get /CAPTION "Miniconda installer" "https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe" $TEMP\Miniconda2-latest-Windows-x86_64.exe
	ExecWait '$TEMP\Miniconda2-latest-Windows-x86_64.exe /InstallationType=JustMe /S /D=$INSTDIR\Conda_for_PMD'
	Delete '$TEMP\Miniconda2-latest-Windows-x86_64.exe'
	ExecWait '$INSTDIR\Conda_for_PMD\Scripts\conda.exe update conda -y'
	ExecWait '$INSTDIR\Conda_for_PMD\Scripts\conda.exe install numpy scipy cython pip wheel setuptools -y'
	ExecWait '$INSTDIR\Conda_for_PMD\Scripts\conda.exe install -c krisvanneste kivy=1.8.0 -y'
	WriteUninstaller $INSTDIR\Uninstall.exe
SectionEnd

Section "PerceptionMD executable" PMDInstall
	SetOutPath $INSTDIR
	File perceptionmd-uninstall.ico
	ExecWait '$INSTDIR\Conda_for_PMD\Scripts\pip.exe install  https://github.com/dvolgyes/perceptionmd/archive/master.zip'
	
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${COMPANYNAME} - ${APPNAME} - ${DESCRIPTION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\perceptionmd.ico$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "$\"${COMPANYNAME}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "$\"${HELPURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "$\"${UPDATEURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "$\"${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}$\""
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
	# There is no option for modifying or repairing the install
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
	# Set the INSTALLSIZE constant (!defined at the top of this script) so Add/Remove Programs can accurately report the size
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
SectionEnd

Section "Register .pmd extension" RegisterPMD
	SetOutPath $INSTDIR
	${registerExtension} "$INSTDIR\Conda_for_PMD\Scripts\PerceptionMD.bat" ".pmd" "PerceptionMD file"
SectionEnd

Section "Uninstaller" UninstallerSection
	SetOutPath $INSTDIR
SectionEnd

Section "Add uninstaller to Start Menu" StartMenuInst
	createDirectory "$SMPROGRAMS\${COMPANYNAME}"
	createShortCut "$SMPROGRAMS\${COMPANYNAME}\uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

;--------------------------------
;Descriptions
LangString DESC_MinicondaInstall ${LANG_ENGLISH} "Install Miniconda execution environment with Python2"
LangString DESC_PMDInstall ${LANG_ENGLISH} "Install PerceptionMD core files"
LangString DESC_RegisterPMD ${LANG_ENGLISH} "Associate .pmd extension with PerceptionMD"
LangString DESC_UninstallerSection ${LANG_ENGLISH} "Add uninstaller to the Start Menu"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${MinicondaInstall} $(DESC_MinicondaInstall)
!insertmacro MUI_DESCRIPTION_TEXT ${PMDInstall} $(DESC_PMDInstall)
!insertmacro MUI_DESCRIPTION_TEXT ${RegisterPMD} $(DESC_RegisterPMD)
!insertmacro MUI_DESCRIPTION_TEXT ${StartMenuInst} $(DESC_UninstallerSection)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
	${unregisterExtension} ".pmd" "PerceptionMD file"
	RMDir /r '$SMPROGRAMS\${COMPANYNAME}'
	ExecWait '$INSTDIR\Conda_for_PMD\Uninstall-Anaconda.exe /S'
    RMDir /r '$INSTDIR'
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PerceptionMD PerceptionMD"
SectionEnd