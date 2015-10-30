MALODOS (for MAnagement of LOcal DOcument System) is a simple but useful software aimed to help the process of archiving and navigate between the documents of your hard-drive
The program can also call any external OCR program in order to add full-text search features.

It is written in python and mainly merges numereous external libraries to give a fast and simple way to scan and numerically record your personal documents (such as invoices, taxe declaration, etc...)

Being written in python, it is portable (works on windows and linux at least, not tested on other systems).

The libraries onto which it is built are essentially:
  * pysqlite3 (and thus sqlite, for database management)
  * twain (for scanner access under windows)
  * sane (for scanner access under linux)
  * PIL
  * wxpython (and thus wxwidgets) for the GUI
  * swftools (for pdf reading)
  * pypdf (for pdf creation)
  * enchant (for OCR spellchecking)

The program can also call any external OCR program in order to add fullbody search features.

User Guide documentation [here](https://sites.google.com/site/malodospage)

If you like this software and want to support it: [click here](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=D7H33JFSFA98J&lc=IL&item_name=David%20GUEZ&item_number=MALODOS&currency_code=ILS&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted).

Note on versions are added [here](Updates.md).
Roadmap for futures versions is available [here](http://sites.google.com/site/malodospage/home/roadmap?pli=1).

http://sites.google.com/site/malodospage/home/MALODOS_presentation.png?attredirects=0