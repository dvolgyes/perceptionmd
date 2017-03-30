# PerceptionMD

Table of Contents
-----------------

  * [Introduction](#introduction)
  * [Installation](#installation)
     * [Linux install](#linux-install)
     * [Windows install](#windows-install)
        * [Installer file](#installer-file)
        * [Using existing Python environment](#using-existing-python-environment)
     * [Test of the installed program](#test-of-the-installed-program)
        * [Linux](#linux)
        * [Windows](#windows)
  * [Designing experiments](#designing-experiments)


## Introduction

PerceptionMD (PMD) is a tool for conducting observer studies in radiology.
MD refers to both the medical field but also to the fact that
it uses markdown-like files to define experiments.

Several other softwares inspired the development, most notably [PsychoPy](http://www.psychopy.org/) and
[ViewDEX](http://www.gu.se/english/research/publication?publicationId=235509) but
there are crucial differencies.

Unlike PsychoPy, PerceptionMD is tailored for medical imaging, especially for
pairwise comparison of 3D volumes, e.g. CT volumes. The main difference compared
to ViewDEX is that
- PMD's main focus is on pairwise comparison studies
- PMD is written in Python, every installation automatically distributes the source code
- PMD's license allows studying the source code and encourages modifications and improvements,
  as long as the [AGPL 3.0](https://www.gnu.org/licenses/agpl-3.0.html) license is respected.
  (Briefly: if you sell or publish your modificatons, it should be published your modifications under the same license.)
  (Remark: the windows installer is generated from NSIS script file. The AGPL v3 license does not
   applicable to the NSIS install system. You can check [NSIS license here](http://nsis.sourceforge.net/License) )

## Installation

The main platform is Linux, but Windows is also more or less supported.
On Linux both Python2 and Python3 are supported, but on Windows Python3 has issues
with the compilers, and it is really hard to set up every dependencies.

### Linux install

You might need administrative priviledges, but if python and cython are already installed,
then you might use 'pip' in '--user' mode.

First install python, cython, and pygame or SDL and kivy.
E.g. on Ubuntu:
```
apt-get install python cython python-pygame python-kivy
pip install git+https://github.com/dvolgyes/perceptionmd
```

### Windows install

#### Installer file
This is the most simple solution, however, it wastes some resources.
The installer downloads a Miniconda distribution, and
installs 'kivy' package for python2 with all the dependencies.
Then it downloads the PerceptionMD source code, and installs some shortcuts
and registers the uninstaller.

This is a very simple process, but it downloads around 300MB from the internet,
and uses around 1.3GB after extraction.

#### Using existing Python environment

This method is much more resource-friendly, however,
you need to install Python, Cython, etc. on your own.
When you have a working environment, then the installation is:
```
pip install -r requirements_win.txt
pip install git+https://github.com/dvolgyes/perceptionmd
```

### Test of the installed program

#### Linux
Execute the "PerceptionMD.py" file with "example" as parameter. This will trigger a
3 page long demo, and the log file will be saved in the working directory.
(The script location depends on the python version and if the package was installed
as a site package or a local package.)

#### Windows
The windows installer places a shortcut into the Start Menu, clicking on the shortcut
will start the demo study.

In case of manual install, executing the $USER$\PerceptionMD\Conda_for_PMD\Scripts\PerceptionMD.bat
will start the demo application.

## Designing experiments

Please read the Language_description.md file for the details.
Examples will be placed in the "Examples" directory.

## Feedback

Any feedback is very appreciated. Patches and improvements are even more welcomed.

I will try to fix every issue but this is not a commercial product, and I don't offer
any kind of 'official' support.
