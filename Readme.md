# Description

This is a basic/toy HTML editor written in Python and tkinter as a project after completion of a Python self-study course.

![screenshot](https://github.com/radoslavian/tkinter-html-editor/blob/main/screenshots/screenshot.jpg)

## Requirements:
For code quick-preview you need either tkinterweb:
```
pip install tkinterweb
```
or tkinterhtml:
```
pip install tkinterhtml
```
Program also requires PIL (or its Windows fork, Pillow) for displaying icons.

## Compatibility
Current version hasn't yet been thoroughly tested under MS Windows and may not work properly on OSs different than Linux-based.

### Components
#### Editing:
Due to the fact I hadn't found any off-the-shelf html beautification component for tkinter, I had to make my own, for which purpose I used the html.parser class from the Python Standard Library. The component doesn't support CSS and Javascript colorization (I may extend it in the future - as an exercise) but supports rudimentary text indentation.

#### Website preview:
by clicking on the "Preview" tab you get the ... general impression of what the page looks like. Again, this is a rather limited preview based on the tkinterweb (or tkinterhtml which is used as a fallback).

Modal windows are implemented using tkSimpleDialog.

### How to launch the program:
from the command-line:
```
[localhost@localdomain]$ python3 <prog_directory_name>
```
 -or-
```
[localhost@localdomain]$ python3 mainapp.py
```
 -or-

- click on mainapp.py in a file manager (if nothing happens or a text editor with source code launches instead, check if the file has an executable attribute set).

### How to use it:
- click on a button from one of editing tabs located over text-editing area to insert an html tag
- select some text and click on a tag-button to add html tags to the selected text
- use F2 keyboard key to change indentation level
- click the "globe" icon (or select from the drop-down menu: Document->View in browser) to display webpage in a default web browser (keep in mind that after clicking the preview icon the file is being automatically saved).

Copyright 2022, Radosław Kuzyk

Disclaimer:
This software is provided by the copyright holder “as is” and any express or implied warranties, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose are disclaimed. In no event shall the copyright owner be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this software, even if advised of the possibility of such damage.

Based on/source: [The 3-Clause BSD License](https://opensource.org/licenses/BSD-3-Clause)
