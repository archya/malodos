# Updates #


## Notes on version 1.1.1 ##

This version add support for external OCR programs, such as [tesseract](http://code.google.com/p/tesseract-ocr/), [gocr](http://jocr.sourceforge.net/) or [ocropus](http://code.google.com/p/ocropus/).
These programs must be installed separately. I'm currently using tesseract which seems to give quite good results. Please have a look on the tesseract website for installation instruction.
Once installed (the program itself must be in your PATH) , you will have to tell **MALODOS** to use it, by using the preference window / content tab. A more detailed documentation will come later.

Note also that this version adds a new dependency : [pyenchant](http://packages.python.org/pyenchant/).
You will also have to install it, but the easyest way to to it is to use pip or easy\_install :
```
easy_install pyenchant
```
This package is used for OCR to check the validity of found terms. So you also need to specify which has to be used for spellchecking, also via the preferences/content tab.


## Notes on version 1.2 ##

Several new features added.
  * Allows to create a virtual folder hierarchy and to attach each document to any number of folders.
  * Add two new view mode for the list of documents:
    1. Folder view : documents classified according to the folder(s) they belong to
    1. Tag folder view : a pseudo folder hierarchy is built, based on the tag of documents
  * Possibility to reorder the flat view alphabetically or chronologically (according to document date or date of registration).
  * Possibility to export all of part of the documents into a new database (also useful for backup of the database).
  * Document to go : allows to create a zip file with a free selection of documents, as well as a database to browse these documents.

Beside these new features, the  database format was enforced and modified. An automatic upgrade of the database format is made on the first start-up of this version, but a backup is performed before any irreversible operation.

## Notes on version 1.2.2 ##

This version mainly removes bugs occuring when running under the MS WINDOWS, that prevented the users to save scan images to disk.
Some new options were added on the preference dialog for the scanner tab. These options allows to
  * define a default folder for saving document and/or to use the last folder each time
  * automatically start a new scan when the scanner dialog opens
  * defining an automatic filename with a user defined prefix followed by an automatic increasing number
  * choose between closing or keeping the scanner dialog open after a new scan
  * reset or not the metadata fields between two scans, in case the dialog doesn't close automatically after scan.

Moreover, two new buttons were added to the main panel, the first one allowing to send me a bug report via e-mail (this option is for people affraid of using the bugreport system of this site, which is the prefered way...). The second button is a shortcut to donating for the developement of MALODOS, via paypal.

Finaly, a confirmation dialog is now appearing if any meta-data field is modified for a record and if the user is clicking into another record before saving the changes.
Another confirmation dialog is also appearing if, after a new scan, the user tries to close the scan window before saving the data to the disk.

## Notes on version 1.3 ##

Many new features are added in this release.
  1. Allows to save file in pdf/jpg/bmp/png/tiff format. If the document is multi-page only pdf and tiff files are possibles.
  1. Allows to join multiple documents together (if you scanned them in two pass by accident)
  1. Allows to add scan/file content to the end of any document
  1. Allows to search part of word (ie. searching for "visi" will also give documents containing television) or whole word.
  1. Add a seach dialog to help you building complex document request
  1. Basket view  allowing to regroup different documents in a set and apply any action on all of them (delete them, make a zip file, join them together)

any some minor bug fixes