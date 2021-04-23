Description

This is a basic/toy HTML editor written in Python and tkinter as a project after completion of a Python self-study course.

Compatibility
Current version has not yet been tested under MS Windows and may not work properly on OSs different than Linux-based.

Components
Editing:
Due to the fact I hadn't found any off-the-shelf html beautification component for tkinter, I had to make my own, for which purpose I used the html.parser class from the Python Standard Library. The component doesn't support CSS and Javascript colorization (I may extend it in the future - as an exercise) but supports rudimentary text indentation.

Website preview:
by clicking on the "Preview" tab you get the ... impression of what the page looks like. Again, this is a very basic preview based on the tkinterhtml - which is no longer developed, doesn't support hyperlinks and css - but unlike cefpython, doesn't crash.

Modal windows are implemented using tkSimpleDialog.


How to launch the program:
from the command-line:

[localhost@localdomain]$ python3 <prog_directory_name>

 -or-

[localhost@localdomain]$ python3 mainapp.py

 -or-

- click on mainapp.py in a file manager (if nothing happens or a text editor with source code launches instead, check if the file has an executable attribute set).

How to use it:
- click on a button from one of editing tabs located over text-editing area to insert an html tag
- select some text and click on a tag-button to add html tags to the selected text
- use F2 keyboard key to change indentation level
- click the "globe" icon (or select from the drop-down menu: Document->View in browser) to display webpage in a default web browser.

Disclaimer:
Don't use the program with any production code (it isn't suitable for that, anyway) or with any files that you are afraid of corrupting.
After saying that, I bear no responsibility for any data loss that may result from using the software.
